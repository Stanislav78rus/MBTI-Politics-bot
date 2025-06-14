# Политический MBTI Бот 🤖📜

Этот бот помогает пользователю определить свой политический архетип по аналогии с типологией MBTI. Вдохновлён историей великих мировых лидеров.

## 🔧 Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-user/your-repo.git
cd your-repo
```

2. Создайте `.env` файл на основе `.env.example` и добавьте свои переменные:
```
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_telegram_user_id
```

3. Запуск через Docker:
```bash
docker build -t political-mbti-bot .
docker run --env-file .env political-mbti-bot
```

## 📦 Структура проекта

- `main.py` — основной код Telegram-бота
- `questions.json` — вопросы теста
- `results.json` — типы личностей и лидеры
- `requirements.txt` — зависимости
- `Dockerfile` — сборка контейнера
- `render.yaml` — конфигурация Render.com

## 🚀 Автодеплой через Render

Проект можно задеплоить как Background Worker. Используйте `render.yaml` для автозапуска.

## ✍️ Лицензия

MIT License
