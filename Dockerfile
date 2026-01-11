# Используем официальный образ Python
FROM python:3.10-slim

# Устанавливаем пользователя на раннем этапе
ARG USER_NAME=appuser
ARG USER_UID=1001
ARG USER_GID=1001

# Создаем не-root пользователя и группу
RUN groupadd --gid $USER_GID $USER_NAME && \
    useradd --uid $USER_UID --gid $USER_GID --shell /bin/bash --create-home $USER_NAME

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости для matplotlib
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения
COPY --chown=$USER_UID:$USER_GID . .

# Создаём директорию для базы данных 
RUN mkdir -p /app/data && chown $USER_UID:$USER_GID /app/data

USER $USER_NAME

# Переменная окружения для unbuffered вывода Python
ENV PYTHONUNBUFFERED=1

# Запускаем бота
CMD ["python", "bot.py"]


