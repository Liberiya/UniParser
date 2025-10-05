# Инструкции по развертыванию University Staff Parser Bot

## Системные требования

### Минимальные требования
- Python 3.11+
- 2 GB RAM
- 1 GB свободного места
- Интернет соединение

### Рекомендуемые требования
- Python 3.11+
- 4 GB RAM
- 5 GB свободного места
- Стабильное интернет соединение
- Docker (опционально)

## Установка и настройка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd university-parser-bot
```

### 2. Создание виртуального окружения

```bash
# Создание виртуального окружения
python -m venv venv

# Активация (Linux/Mac)
source venv/bin/activate

# Активация (Windows)
venv\Scripts\activate
```

### 3. Установка зависимостей

```bash
# Установка Python пакетов
pip install -r requirements.txt

# Установка Playwright браузеров
playwright install chromium

# Установка русской модели spaCy (опционально)
python -m spacy download ru_core_news_sm
```

### 4. Настройка переменных окружения

Создайте файл `.env`:

```env
# Обязательные настройки
TELEGRAM_TOKEN=your_bot_token_here

# Настройки парсера
RATE_LIMIT_DELAY=2
MAX_PAGES_DEPTH=2
JS_RENDER_TIMEOUT=30
PARSING_TIMEOUT=120
CONFIDENCE_THRESHOLD=0.6

# База данных
DATABASE_URL=sqlite:///data/parser_bot.db

# Redis (опционально)
REDIS_URL=redis://localhost:6379/0

# Логирование
LOG_LEVEL=INFO
DEVELOPER_MODE=false

# Webhook (опционально)
WEBHOOK_URL=https://yourdomain.com
WEBHOOK_PATH=/webhook
PORT=8080
```

### 5. Создание необходимых директорий

```bash
mkdir -p logs data
```

## Запуск

### Локальный запуск

```bash
# Запуск бота
python main.py

# Или через модуль
python -m bot.main
```

### Запуск через Docker

#### Простой запуск
```bash
# Сборка образа
docker build -t university-parser-bot .

# Запуск контейнера
docker run --env-file .env university-parser-bot
```

#### Запуск с docker-compose
```bash
# Запуск всех сервисов
docker-compose up --build

# Запуск в фоновом режиме
docker-compose up -d --build

# Просмотр логов
docker-compose logs -f bot
```

## Настройка веб-сервера (для webhook)

### Nginx конфигурация

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location /webhook {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL сертификат (Let's Encrypt)

```bash
# Установка certbot
sudo apt install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d yourdomain.com

# Автоматическое обновление
sudo crontab -e
# Добавить: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Мониторинг и логирование

### Настройка логирования

```python
# В main.py можно настроить дополнительные логи
logger.add(
    "logs/error.log",
    level="ERROR",
    rotation="1 week",
    retention="1 month"
)
```

### Мониторинг через systemd (Linux)

Создайте файл `/etc/systemd/system/university-parser-bot.service`:

```ini
[Unit]
Description=University Staff Parser Bot
After=network.target

[Service]
Type=simple
User=bot
WorkingDirectory=/path/to/university-parser-bot
Environment=PATH=/path/to/university-parser-bot/venv/bin
ExecStart=/path/to/university-parser-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запуск сервиса:
```bash
sudo systemctl daemon-reload
sudo systemctl enable university-parser-bot
sudo systemctl start university-parser-bot
sudo systemctl status university-parser-bot
```

### Мониторинг через PM2 (Node.js)

```bash
# Установка PM2
npm install -g pm2

# Создание конфигурации
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'university-parser-bot',
    script: 'main.py',
    interpreter: 'python',
    cwd: '/path/to/university-parser-bot',
    env: {
      NODE_ENV: 'production'
    },
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G'
  }]
}
EOF

# Запуск
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## Резервное копирование

### Автоматическое резервное копирование

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/university-parser-bot"
SOURCE_DIR="/path/to/university-parser-bot"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание директории для бэкапа
mkdir -p $BACKUP_DIR

# Копирование данных
cp -r $SOURCE_DIR/data $BACKUP_DIR/data_$DATE
cp -r $SOURCE_DIR/logs $BACKUP_DIR/logs_$DATE

# Архивирование
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz -C $BACKUP_DIR data_$DATE logs_$DATE

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +30 -delete

echo "Backup completed: backup_$DATE.tar.gz"
```

Добавьте в crontab:
```bash
# Ежедневный бэкап в 2:00
0 2 * * * /path/to/backup.sh
```

## Обновление

### Обновление кода

```bash
# Остановка бота
sudo systemctl stop university-parser-bot

# Обновление кода
git pull origin main

# Обновление зависимостей
pip install -r requirements.txt

# Запуск бота
sudo systemctl start university-parser-bot
```

### Обновление через Docker

```bash
# Остановка контейнеров
docker-compose down

# Обновление образов
docker-compose pull

# Пересборка и запуск
docker-compose up --build -d
```

## Безопасность

### Настройка файрвола

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# iptables
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -j DROP
```

### Защита токена

```bash
# Установка правильных прав на .env
chmod 600 .env
chown bot:bot .env
```

### Регулярные обновления

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Обновление Python пакетов
pip list --outdated
pip install --upgrade package_name
```

## Производительность

### Оптимизация базы данных

```sql
-- Создание индексов для SQLite
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_parsing_results_user_id ON parsing_results(user_id);
CREATE INDEX IF NOT EXISTS idx_staff_records_parsing_result_id ON staff_records(parsing_result_id);
```

### Мониторинг ресурсов

```bash
# Мониторинг использования памяти
htop

# Мониторинг дискового пространства
df -h

# Мониторинг логов
tail -f logs/bot.log | grep ERROR
```

## Устранение неполадок

### Частые проблемы

#### Бот не запускается
```bash
# Проверка токена
grep TELEGRAM_TOKEN .env

# Проверка логов
tail -f logs/bot.log

# Проверка зависимостей
pip list | grep aiogram
```

#### Ошибки парсинга
```bash
# Проверка Playwright
playwright --version

# Переустановка браузеров
playwright install chromium --force

# Проверка сетевого соединения
curl -I https://example.com
```

#### Проблемы с базой данных
```bash
# Проверка файла базы данных
ls -la data/parser_bot.db

# Проверка прав доступа
chmod 664 data/parser_bot.db
chown bot:bot data/parser_bot.db
```

### Логи и отладка

```bash
# Просмотр всех логов
tail -f logs/bot.log

# Фильтрация по уровню
grep ERROR logs/bot.log

# Мониторинг в реальном времени
journalctl -u university-parser-bot -f
```

## Масштабирование

### Горизонтальное масштабирование

```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  bot:
    build: .
    scale: 3
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### Балансировка нагрузки

```nginx
upstream bot_backend {
    server localhost:8080;
    server localhost:8081;
    server localhost:8082;
}

server {
    location /webhook {
        proxy_pass http://bot_backend;
    }
}
```

## Поддержка

### Контакты
- GitHub Issues: [ссылка на репозиторий]
- Email: [email администратора]
- Telegram: [@username администратора]

### Документация
- README.md - основная документация
- USER_GUIDE.md - руководство пользователя
- API.md - документация API (если есть)

### Сообщество
- Telegram группа: [ссылка на группу]
- Discord сервер: [ссылка на сервер]
- Форум: [ссылка на форум]
