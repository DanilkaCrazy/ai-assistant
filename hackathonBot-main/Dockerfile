# Базовый образ Python
FROM python:3.12-slim

# Чтобы Python не кешировал .pyc и логи шли в stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Рабочая директория внутри контейнера
WORKDIR /app

# Скопируем список зависимостей и установим их
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё содержимое репозитория (включая botMain.py)
COPY . ./

# Команда запуска бота
CMD ["python", "botMain.py"]
