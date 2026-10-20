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

# PO-token provider (bgutil) on 127.0.0.1:4416: started here, before the bot, so yt-dlp finds it with no env setup.
if [ -f /opt/bgutil/server/build/main.js ]; then
    (cd /opt/bgutil/server && node build/main.js > /tmp/bgutil.log 2>&1 &)
    for i in $(seq 1 30); do
        curl -s -o /dev/null http://127.0.0.1:4416/ && break
        sleep 1
    done
    echo "PO token provider started on 127.0.0.1:4416 (log: /tmp/bgutil.log)"
fi

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
