.PHONY: dev test lint clean

# Запуск в режиме разработки
dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Запуск тестов
test:
	pytest tests/ -v --tb=short

# Запуск конкретных тестов
test-analyze:
	pytest tests/test_analyze.py -v

test-edge:
	pytest tests/test_edge_cases.py -v

test-telegram:
	pytest tests/test_telegram.py -v

# Установка зависимостей
install:
	pip install -r requirements.txt

# Создание .env из примера
env:
	cp .env.example .env
	@echo "✅ .env создан. Заполните API ключи!"

# Очистка
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Docker
docker-build:
	docker build -t yarko-ai .

docker-run:
	docker run -p 8000:8000 --env-file .env yarko-ai
