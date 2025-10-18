# 🏭 Otkroimosprom Backend

Backend система для анализа и визуализации данных московских промышленных предприятий. Система предоставляет API для работы с компаниями, генерации графиков и аналитики.

## 🚀 Возможности

### 📊 Управление компаниями

- **CRUD операции** с компаниями
- **Фильтрация** по различным метрикам (отрасль, размер, статус, год)
- **Массовый парсинг** из CSV/JSON файлов
- **Поиск** по ИНН, отрасли, статусу
- **Связывание** компаний с пользователями

### 📈 Генерация графиков

- **7 типов графиков**: древовидные карты, точечные графики, гистограммы и др.
- **Интерактивная визуализация** с Plotly
- **Экспорт** в различные форматы
- **Массовое удаление** графиков

### 🔐 Аутентификация и авторизация

- **JWT токены** для безопасной авторизации
- **Регистрация** и **вход** пользователей
- **Изоляция данных** между пользователями

### 📋 Парсинг данных

- **Эмулятор парсера** для работы с тестовыми данными
- **Поддержка CSV и JSON** форматов
- **Автоматическое сохранение** в базу данных
- **Умная обработка дубликатов**

## 🛠 Технологии

- **FastAPI** - современный веб-фреймворк для Python
- **SQLModel** - ORM на основе Pydantic и SQLAlchemy
- **PostgreSQL** - реляционная база данных
- **Plotly** - библиотека для интерактивной визуализации
- **Pydantic** - валидация данных
- **JWT** - аутентификация
- **Docker** - контейнеризация

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.8+
- PostgreSQL 12+
- Docker (опционально)

### Установка

1. **Клонирование репозитория**

```bash
git clone https://github.com/Hack2025MosProm/backend.git
cd otkroimosprom-backend
```

2. **Установка зависимостей**

```bash
pip install -r requirements.txt
```

3. **Настройка базы данных**

```bash
createdb otkroimosprom
```

4. **Настройка переменных окружения**

```bash
cp .env.example .env
```

5. **Запуск приложения**

```bash
# Разработка
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080

# Или через Docker
docker-compose up -d
```

### Docker

```bash
# Сборка и запуск
docker-compose up --build

# Остановка
docker-compose down
```

## 📚 API Документация

### Основные эндпоинты

| Метод  | Путь                           | Описание                 |
| ------ | ------------------------------ | ------------------------ |
| `POST` | `/api/v1/auth/register`        | Регистрация пользователя |
| `POST` | `/api/v1/auth/login`           | Авторизация              |
| `GET`  | `/api/v1/companies/`           | Список компаний          |
| `GET`  | `/api/v1/companies/filter`     | Фильтрация компаний      |
| `POST` | `/api/v1/companies/parse/bulk` | Массовый парсинг         |
| `POST` | `/api/v1/graphs/generate`      | Генерация графика        |
| `GET`  | `/api/v1/graphs/`              | Список графиков          |

### Парсинг данных

#### Массовый парсинг

```bash
curl -X POST "http://localhost:8080/api/v1/companies/parse/bulk" \
  -H "Authorization: Bearer <token>"
```

#### Поиск по ИНН

```bash
curl -X POST "http://localhost:8080/api/v1/companies/parse/search-by-inn" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "7721840520", "save_to_db": true}'
```

#### Поиск по отрасли

```bash
curl -X POST "http://localhost:8080/api/v1/companies/parse/search-by-industry" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "IT", "save_to_db": true}'
```

### Генерация графиков

#### Создание графика

```bash
curl -X POST "http://localhost:8080/api/v1/graphs/generate" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "graph_type": "treemap_prod",
    "company_ids": [1, 2, 3]
  }'
```

#### Массовое удаление графиков

```bash
curl -X DELETE "http://localhost:8080/api/v1/graphs/bulk" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "delete_all": true,
    "graph_ids": []
  }'
```

## 🔧 Конфигурация

### Переменные окружения

```bash
# База данных
postgresql_uri=postgresql+psycopg2://postgres:<password>@<server>:<port>/<db_name>

# JWT
jwt_secret=your-jwt-secret
access_token_expire_minutes=60

# Приложение
logging_level=INFO
logging_format=standart
port=8080
host=0.0.0.0
reload=1
workers=1
```

## 📊 Типы графиков

| Тип            | Описание              | Сектор            |
| -------------- | --------------------- | ----------------- |
| `treemap_prod` | Древовидная карта     | Производство      |
| `scatter_busy` | Точечный график       | Занятость         |
| `norm_export`  | Нормированные столбцы | Экспорт           |
| `pie_prod`     | Круговая диаграмма    | Производство      |
| `area_ecology` | Диаграмма с областями | Экология          |
| `hist_energy`  | Гистограмма           | Энергопотребление |
| `table_invest` | Сводная таблица       | Инвестиции        |

## 📈 Мониторинг и логирование

### Логирование

- **Уровни**: DEBUG, INFO, WARNING, ERROR
- **Формат**: JSON с цветным выводом
- **Файлы**: `logs/app.log`

### Метрики

- Время выполнения запросов
- Количество обработанных компаний
- Статистика генерации графиков

## 🔒 Безопасность

### Аутентификация

- **JWT токены** с истечением срока действия
- **Хеширование паролей** с bcrypt
- **Валидация** всех входящих данных

### Авторизация

- **Изоляция данных** между пользователями
- **Проверка прав доступа** к компаниям и графикам
- **Защита от SQL инъекций** через ORM

## 🚀 Развертывание

### Production

1. **Настройка сервера**

```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
export DATABASE_URL=postgresql://...
export SECRET_KEY=...

# Запуск с Gunicorn
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

2. **Docker**

```bash
# Сборка образа
docker build -t otkroimosprom-backend .

# Запуск контейнера
docker run -p 8080:8080 otkroimosprom-backend
```

## 🤝 Разработка

### Установка для разработки

```bash
# Клонирование
git clone https://github.com/Hack2025MosProm/backend.git
cd otkroimosprom-backend

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate.ps1  # Windows Powershell

# Установка зависимостей
pip install -r requirements.txt
```

### Структура кода

- **API слой**: `src/api/` - эндпоинты и валидация
- **Бизнес логика**: `src/repositories/` - работа с данными
- **Модели**: `src/models/` - структуры данных
- **Утилиты**: `src/csv_reader/`, `src/parser/` - вспомогательные модули

## 📝 Changelog

### MVP

- ✨ Первоначальный релиз
- 🔐 Система аутентификации
- 📊 Управление компаниями
- 📈 Генерация графиков
- 🔍 Парсинг данных
- 📚 API документация

## 📞 Поддержка

- **Документация**: [docs/api.v1.md](docs/api.v1.md)
- **Issues**: GitHub Issues

---

**Сделано с ❤️ для анализа московской промышленности**
