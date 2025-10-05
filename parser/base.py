"""
Базовый класс парсера
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from loguru import logger

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


class BaseParser(ABC):
    """Базовый класс для парсеров"""
    
    def __init__(
        self,
        rate_limit_delay: float = 2.0,
        max_depth: int = 2,
        js_render_timeout: int = 30,
        parsing_timeout: int = 120,
        confidence_threshold: float = 0.6
    ):
        self.rate_limit_delay = rate_limit_delay
        self.max_depth = max_depth
        self.js_render_timeout = js_render_timeout
        self.parsing_timeout = parsing_timeout
        self.confidence_threshold = confidence_threshold
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    async def parse_url(self, url: str) -> List[Dict[str, Any]]:
        """Основной метод парсинга URL"""
        logger.info(f"Начинаю парсинг URL: {url}")
        
        start_time = time.time()
        results = []
        
        try:
            # Получаем страницы для парсинга
            pages_to_parse = await self._get_pages_to_parse(url)
            
            for page_url in pages_to_parse:
                if time.time() - start_time > self.parsing_timeout:
                    logger.warning(f"Превышен таймаут парсинга: {self.parsing_timeout} сек")
                    break
                
                # Парсим страницу
                page_results = await self._parse_page(page_url)
                results.extend(page_results)
                
                # Соблюдаем rate limit
                await asyncio.sleep(self.rate_limit_delay)
            
            # Дедупликация и валидация результатов
            results = await self._deduplicate_and_validate(results)
            
            logger.info(f"Парсинг завершен. Найдено {len(results)} записей")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге {url}: {e}")
            raise
    
    async def _get_pages_to_parse(self, url: str) -> List[str]:
        """Получение списка страниц для парсинга"""
        pages = [url]
        
        try:
            # Пробуем найти дополнительные страницы
            if self.max_depth > 1:
                additional_pages = await self._find_additional_pages(url)
                pages.extend(additional_pages[:self.max_depth - 1])
            
            return pages
        except Exception as e:
            logger.warning(f"Не удалось найти дополнительные страницы: {e}")
            return pages
    
    async def _find_additional_pages(self, base_url: str) -> List[str]:
        """Поиск дополнительных страниц для парсинга"""
        additional_pages = []
        
        try:
            # Получаем HTML страницы
            response = self.session.get(base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ищем ссылки на страницы сотрудников
            staff_keywords = [
                'staff', 'employees', 'personnel', 'faculty', 'people',
                'сотрудники', 'преподаватели', 'кафедра', 'kafedra',
                'about/structure', 'structure', 'team'
            ]
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text().lower()
                
                # Проверяем, содержит ли ссылка ключевые слова
                if any(keyword in text or keyword in href.lower() for keyword in staff_keywords):
                    full_url = urljoin(base_url, href)
                    if self._is_valid_internal_url(full_url, base_url):
                        additional_pages.append(full_url)
            
            return list(set(additional_pages))  # Убираем дубликаты
            
        except Exception as e:
            logger.warning(f"Ошибка при поиске дополнительных страниц: {e}")
            return []
    
    def _is_valid_internal_url(self, url: str, base_url: str) -> bool:
        """Проверка, является ли URL внутренней ссылкой"""
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_url)
            
            return (
                parsed_url.netloc == parsed_base.netloc and
                parsed_url.scheme in ['http', 'https'] and
                not any(ext in url.lower() for ext in ['.pdf', '.doc', '.docx', '.jpg', '.png', '.gif'])
            )
        except:
            return False
    
    async def _parse_page(self, url: str) -> List[Dict[str, Any]]:
        """Парсинг отдельной страницы"""
        logger.info(f"Парсинг страницы: {url}")
        
        try:
            # Сначала пробуем простой HTML парсинг
            results = await self._parse_html_page(url)
            
            # Если результатов мало, пробуем JS рендеринг
            if len(results) < 3:
                logger.info(f"Мало результатов HTML парсинга ({len(results)}), пробуем JS рендеринг")
                js_results = await self._parse_js_page(url)
                results.extend(js_results)
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге страницы {url}: {e}")
            return []
    
    async def _parse_html_page(self, url: str) -> List[Dict[str, Any]]:
        """Парсинг HTML страницы без JS"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return await self._extract_staff_data(soup, url)
            
        except Exception as e:
            logger.error(f"Ошибка HTML парсинга {url}: {e}")
            return []
    
    async def _parse_js_page(self, url: str) -> List[Dict[str, Any]]:
        """Парсинг страницы с JS рендерингом"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Устанавливаем таймаут
                page.set_default_timeout(self.js_render_timeout * 1000)
                
                # Переходим на страницу
                await page.goto(url, wait_until='networkidle')
                
                # Ждем загрузки контента
                await page.wait_for_timeout(2000)
                
                # Получаем HTML
                html = await page.content()
                await browser.close()
                
                # Парсим полученный HTML
                soup = BeautifulSoup(html, 'html.parser')
                return await self._extract_staff_data(soup, url)
                
        except Exception as e:
            logger.error(f"Ошибка JS парсинга {url}: {e}")
            return []
    
    @abstractmethod
    async def _extract_staff_data(self, soup: BeautifulSoup, url: str) -> List[Dict[str, Any]]:
        """Извлечение данных о сотрудниках из HTML"""
        pass
    
    async def _deduplicate_and_validate(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Дедупликация и валидация результатов"""
        # Дедупликация по email
        seen_emails = set()
        unique_results = []
        
        for result in results:
            email = result.get('email', '').lower()
            if email and email not in seen_emails:
                seen_emails.add(email)
                unique_results.append(result)
            elif not email:
                # Если нет email, проверяем по ФИО
                fio = result.get('fio', '').lower()
                if fio not in [r.get('fio', '').lower() for r in unique_results]:
                    unique_results.append(result)
        
        # Фильтруем по confidence threshold
        filtered_results = [
            r for r in unique_results 
            if r.get('confidence', 0) >= self.confidence_threshold
        ]
        
        logger.info(f"После дедупликации и фильтрации: {len(filtered_results)} записей")
        return filtered_results
