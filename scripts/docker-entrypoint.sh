#!/bin/bash
set -e

# Переходим в рабочую директорию приложения
cd /app || exit 1

# Функция для обработки сигналов завершения
cleanup() {
    echo "Получен сигнал завершения, останавливаем бота..."
    kill $BOT_PID $HEALTH_PID 2>/dev/null || true
    wait $BOT_PID 2>/dev/null || true
    exit 0
}

# Устанавливаем обработчики сигналов
trap cleanup SIGTERM SIGINT

# Запускаем бота
echo "Запуск Telegram бота из директории: $(pwd)"
python magic.py &
BOT_PID=$!

echo "Бот запущен (PID: $BOT_PID)"

# Open the port Render requires ($PORT). Only returns "ok", serves no files.
python scripts/health_server.py &
HEALTH_PID=$!
echo "Health endpoint started on port ${PORT:-8080} (PID: $HEALTH_PID)"

# Ждем завершения процесса
wait $BOT_PID
