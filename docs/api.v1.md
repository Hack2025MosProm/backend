# API Documentation v1

## Authentication

### POST `/api/v1/auth/register`

Регистрация нового пользователя в системе.

**Request Body (JSON)**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `username` | string | Да | Имя пользователя (3-50 символов) |
| `password` | string | Да | Пароль (минимум 6 символов) |

**Response 201**

```json
{
  "id": 1,
  "username": "newuser",
  "created_at": "2025-01-18T14:30:00Z",
  "updated_at": "2025-01-18T14:30:00Z"
}
```

**Response 400**

```json
{
  "detail": "Username already registered"
}
```

---

### POST `/api/v1/auth/login`

Авторизация пользователя через form-data (стандартный OAuth2).

**Form Data (x-www-form-urlencoded)**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `username` | string | Да | Имя пользователя |
| `password` | string | Да | Пароль пользователя |

**Response 200**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Response 401**

```json
{
  "detail": "Incorrect username or password"
}
```

---

### POST `/api/v1/auth/login-json`

Авторизация пользователя через JSON (альтернативный способ).

**Request Body (JSON)**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `username` | string | Да | Имя пользователя |
| `password` | string | Да | Пароль пользователя |

**Response 200**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Response 401**

```json
{
  "detail": "Incorrect username or password"
}
```

---

### GET `/api/v1/auth/me`

Получить информацию о текущем авторизованном пользователе.

**Headers**
| Заголовок | Тип | Обязательно | Описание |
|--------------------|--------|--------------|----------|
| `Authorization` | string | Да | `Bearer <JWT>` полученный из login эндпоинтов |

**Response 200**

```json
{
  "id": 1,
  "username": "user123",
  "created_at": "2025-01-18T14:30:00Z",
  "updated_at": "2025-01-18T14:30:00Z"
}
```

**Response 401**

```json
{
  "detail": "Could not validate credentials"
}
```

---

## Files

### POST `/api/v1/files/upload`

Загрузка CSV файла с данными предприятий и их обработка.

**Headers**
| Заголовок | Тип | Обязательно | Описание |
|--------------------|--------|--------------|----------|
| `Authorization` | string | Да | `Bearer <JWT>` токен авторизации |

**Form Data (multipart/form-data)**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `file` | file | Да | CSV файл с данными предприятий |
| `as_name` | string | Нет | Альтернативное имя для файла |

**Response 200**

```json
{
  "file_name": "companies.csv",
  "stored_name": "abc123_companies.csv",
  "size_bytes": 1024000,
  "companies_processed": 150,
  "companies_saved": [
    {
      "id": 1,
      "name": "ООО Компания 1",
      "inn": 1234567890
    },
    {
      "id": 2,
      "name": "АО Компания 2",
      "inn": 9876543210
    }
  ]
}
```

**Response 400**

```json
{
  "detail": "Only CSV files are allowed"
}
```

**Response 413**

```json
{
  "detail": "File too large (limit 50 MB)"
}
```

---

## Companies

### GET `/api/v1/companies/`

Получить список компаний пользователя с пагинацией.

**Headers**
| Заголовок | Тип | Обязательно | Описание |
|--------------------|--------|--------------|----------|
| `Authorization` | string | Да | `Bearer <JWT>` токен авторизации |

**Query Parameters**
| Параметр | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `limit` | integer | Нет | Количество записей (по умолчанию: 50) |
| `offset` | integer | Нет | Смещение (по умолчанию: 0) |

**Response 200**

```json
{
  "companies": [
    {
      "id": 1,
      "inn": 1234567890,
      "name": "ООО Компания 1",
      "full_name": "Общество с ограниченной ответственностью Компания 1",
      "spark_status": "Действующая",
      "main_industry": "IT",
      "company_size_final": "Среднее",
      "organization_type": "ООО",
      "support_measures": true,
      "special_status": "Есть",
      "confirmation_status": "Не подтверждён",
      "confirmed_at": null,
      "confirmer_identifier": null,
      "updated_at": "2025-01-18T14:30:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

---

### GET `/api/v1/companies/filter`

Фильтровать компании пользователя по метрикам.

**Headers**
| Заголовок | Тип | Обязательно | Описание |
|--------------------|--------|--------------|----------|
| `Authorization` | string | Да | `Bearer <JWT>` токен авторизации |

**Query Parameters**
| Параметр | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `spark_status` | string | Нет | Статус СПАРК |
| `main_industry` | string | Нет | Основная отрасль |
| `company_size_final` | string | Нет | Размер предприятия |
| `organization_type` | string | Нет | Тип организации |
| `support_measures` | boolean | Нет | Получены ли меры поддержки |
| `special_status` | string | Нет | Особый статус |
| `year` | integer | Нет | Год |
| `limit` | integer | Нет | Количество записей (по умолчанию: 50, минимум: 1, максимум: 100) |
| `offset` | integer | Нет | Смещение (по умолчанию: 0, минимум: 0) |

**Response 200**

```json
{
  "companies": [
    {
      "id": 1,
      "inn": 1234567890,
      "name": "ООО Компания 1",
      "full_name": "Общество с ограниченной ответственностью Компания 1",
      "year": 2023,
      "spark_status": "Действующая",
      "main_industry": "IT",
      "company_size_final": "Среднее",
      "organization_type": "ООО",
      "support_measures": true,
      "special_status": "Есть",
      "confirmation_status": "Не подтверждён",
      "confirmed_at": null,
      "confirmer_identifier": null,
      "json_data": {},
      "created_at": "2025-01-18T14:30:00Z",
      "updated_at": "2025-01-18T14:30:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

**Response 400**

```json
{
  "detail": "Validation error"
}
```

**Response 401**

```json
{
  "detail": "Not authenticated"
}
```

---

### GET `/api/v1/companies/{company_id}`

Получить детальную информацию о конкретной компании.

**Headers**
| Заголовок | Тип | Обязательно | Описание |
|--------------------|--------|--------------|----------|
| `Authorization` | string | Да | `Bearer <JWT>` токен авторизации |

**Path Parameters**
| Параметр | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `company_id` | integer | Да | ID компании |

**Response 200**

```json
{
  "id": 1,
  "inn": 1234567890,
  "name": "ООО Компания 1",
  "full_name": "Общество с ограниченной ответственностью Компания 1",
  "spark_status": "Действующая",
  "main_industry": "IT",
  "company_size_final": "Среднее",
  "organization_type": "ООО",
  "support_measures": true,
  "special_status": "Есть",
  "confirmation_status": "Не подтверждён",
  "confirmed_at": null,
  "confirmer_identifier": null,
  "updated_at": "2025-01-18T14:30:00Z"
}
```

**Response 404**

```json
{
  "detail": "Company not found or access denied"
}
```

---

### PATCH `/api/v1/companies/{company_id}`

Обновить основные данные компании. Позволяет частично обновить любые поля компании. Обновляются только переданные поля, остальные остаются без изменений.

**Headers**
| Заголовок | Тип | Обязательно | Описание |
|--------------------|--------|--------------|----------|
| `Authorization` | string | Да | `Bearer <JWT>` токен авторизации |

**Path Parameters**
| Параметр | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `company_id` | integer | Да | ID компании |

**Request Body (JSON)**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `name` | string | Нет | Название компании |
| `full_name` | string | Нет | Полное наименование компании |
| `spark_status` | string | Нет | Статус СПАРК |
| `main_industry` | string | Нет | Основная отрасль |
| `company_size_final` | string | Нет | Размер предприятия (итог) |
| `organization_type` | string | Нет | Тип организации |
| `support_measures` | boolean | Нет | Меры поддержки |
| `special_status` | string | Нет | Особый статус |

**Примеры запросов:**

**1. Обновление только названия:**

```json
{
  "name": "ООО Обновленная Компания"
}
```

**2. Обновление нескольких полей:**

```json
{
  "name": "АО Агро69",
  "full_name": "Полное наименование АО \"Агро609\"",
  "spark_status": "Действующая",
  "main_industry": "Пищевая промышленность",
  "company_size_final": "Крупное",
  "organization_type": null,
  "support_measures": false,
  "special_status": "Нет"
}
```

**3. Обновление только ключевых метрик:**

```json
{
  "main_industry": "IT",
  "company_size_final": "Среднее",
  "support_measures": true
}
```

**Response 200**

```json
{
  "id": 1,
  "inn": 1234567890,
  "name": "ООО Обновленная Компания",
  "full_name": "Общество с ограниченной ответственностью Обновленная Компания",
  "spark_status": "Действующая",
  "main_industry": "IT",
  "company_size_final": "Крупное",
  "organization_type": "ООО",
  "support_measures": true,
  "special_status": "Есть",
  "confirmation_status": "Не подтверждён",
  "confirmed_at": null,
  "confirmer_identifier": null,
  "updated_at": "2025-01-18T15:00:00Z"
}
```

---

### PATCH `/api/v1/companies/{company_id}/key-metrics`

Обновить ключевые метрики компании. Специализированный эндпоинт для обновления только ключевых бизнес-метрик компании.

**Headers**
| Заголовок | Тип | Обязательно | Описание |
|--------------------|--------|--------------|----------|
| `Authorization` | string | Да | `Bearer <JWT>` токен авторизации |

**Path Parameters**
| Параметр | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `company_id` | integer | Да | ID компании |

**Request Body (JSON)**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `main_industry` | string | Нет | Основная отрасль |
| `company_size_final` | string | Нет | Размер предприятия (итог) |
| `organization_type` | string | Нет | Тип организации |
| `support_measures` | boolean | Нет | Меры поддержки |
| `special_status` | string | Нет | Особый статус |

**Примеры запросов:**

**1. Обновление отрасли:**

```json
{
  "main_industry": "IT"
}
```

**2. Обновление размера и поддержки:**

```json
{
  "company_size_final": "Крупное",
  "support_measures": true,
  "special_status": "Есть"
}
```

**3. Полное обновление метрик:**

```json
{
  "main_industry": "Производство",
  "company_size_final": "Среднее",
  "organization_type": "ООО",
  "support_measures": false,
  "special_status": "Нет"
}
```

**Response 200**

```json
{
  "id": 1,
  "inn": 1234567890,
  "name": "ООО Компания 1",
  "full_name": "Общество с ограниченной ответственностью Компания 1",
  "spark_status": "Действующая",
  "main_industry": "Производство",
  "company_size_final": "Крупное",
  "organization_type": "ООО",
  "support_measures": false,
  "special_status": "Нет",
  "confirmation_status": "Не подтверждён",
  "confirmed_at": null,
  "confirmer_identifier": null,
  "updated_at": "2025-01-18T15:30:00Z"
}
```

---

### PATCH `/api/v1/companies/{company_id}/json-data`

Обновить JSON данные компании. Позволяет полностью заменить или дополнить JSON данные, сохраненные из исходного CSV файла.

**Headers**
| Заголовок | Тип | Обязательно | Описание |
|--------------------|--------|--------------|----------|
| `Authorization` | string | Да | `Bearer <JWT>` токен авторизации |

**Path Parameters**
| Параметр | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `company_id` | integer | Да | ID компании |

**Request Body (JSON)**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `json_data` | object | Да | Полные JSON данные компании (любая структура) |

**Примеры запросов:**

**1. Обновление основных полей:**

```json
{
  "json_data": {
    "ИНН": "1234567890",
    "Наименование организации": "ООО Обновленная Компания",
    "Основная отрасль": "Производство",
    "Размер предприятия (итог)": "Крупное"
  }
}
```

**2. Добавление новых полей:**

```json
{
  "json_data": {
    "ИНН": "1234567890",
    "Наименование организации": "ООО Компания",
    "Новое поле": "Новое значение",
    "Аналитические данные": {
      "коэффициент_ликвидности": 2.1,
      "рентабельность": 15.5
    }
  }
}
```

**3. Полная замена данных:**

```json
{
  "json_data": {
    "ИНН": "9876543210",
    "Наименование организации": "АО Новая Компания",
    "Полное наименование организации": "Акционерное общество Новая Компания",
    "Статус СПАРК": "Действующая",
    "Основная отрасль": "Строительство",
    "Размер предприятия (итог)": "Среднее",
    "Тип организации": "АО",
    "Данные о мерах поддержки": "Не получены",
    "Наличие особого статуса": "Нет",
    "Выручка 2023": 10000000,
    "Прибыль 2023": 1000000,
    "Сотрудники": 50,
    "Адрес": "г. Москва, ул. Примерная, д. 1",
    "Телефон": "+7 (495) 123-45-67"
  }
}
```

**Response 200**

```json
{
  "company_id": 1,
  "json_data": {
    "ИНН": "1234567890",
    "Наименование организации": "ООО Обновленная Компания",
    "Полное наименование организации": "Общество с ограниченной ответственностью Обновленная Компания",
    "Статус СПАРК": "Действующая",
    "Основная отрасль": "Производство",
    "Размер предприятия (итог)": "Крупное",
    "Выручка предприятия, тыс. руб. 2023": 5000000,
    "Чистая прибыль (убыток),тыс. руб. 2023": 500000,
    "Среднесписочная численность персонала (всего по компании), чел 2023": 100,
    "Дополнительные поля": "Обновленные данные"
  },
  "updated_at": "2025-01-18T16:00:00Z"
}
```

**Важные особенности:**

- JSON данные полностью заменяются новыми
- Поддерживается любая структура JSON (объекты, массивы, вложенные данные)
- Поле `json_data` обязательно
- Время обновления автоматически устанавливается в `updated_at`

---

### GET `/api/v1/companies/{company_id}/json-data`

Получить JSON данные компании.

**Headers**
| Заголовок | Тип | Обязательно | Описание |
|--------------------|--------|--------------|----------|
| `Authorization` | string | Да | `Bearer <JWT>` токен авторизации |

**Path Parameters**
| Параметр | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `company_id` | integer | Да | ID компании |

**Response 200**

```json
{
  "company_id": 1,
  "json_data": {
    "ИНН": "1234567890",
    "Наименование организации": "ООО Компания 1",
    "Полное наименование организации": "Общество с ограниченной ответственностью Компания 1",
    "Статус СПАРК": "Действующая",
    "Основная отрасль": "IT",
    "Размер предприятия (итог)": "Среднее",
    "Выручка предприятия, тыс. руб. 2023": 5000000,
    "Чистая прибыль (убыток),тыс. руб. 2023": 500000,
    "Среднесписочная численность персонала (всего по компании), чел 2023": 100
  }
}
```

---

### DELETE `/api/v1/companies/{company_id}`

Удалить компанию.

**Headers**
| Заголовок | Тип | Обязательно | Описание |
|--------------------|--------|--------------|----------|
| `Authorization` | string | Да | `Bearer <JWT>` токен авторизации |

**Path Parameters**
| Параметр | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `company_id` | integer | Да | ID компании |

**Response 200**

```json
{
  "message": "Company deleted successfully"
}
```

**Response 404**

```json
{
  "detail": "Company not found or access denied"
}
```

---

## Error Responses

### 401 Unauthorized

```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden

```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found

```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error"
}
```

---

## Graphs

### POST `/api/v1/graphs/generate`

Генерирует график для указанных компаний пользователя.

**Headers**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `Authorization` | string | Да | Bearer токен авторизации |

**Request Body (JSON)**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `graph_type` | string | Да | Тип графика (treemap_prod, scatter_busy, norm_export, pie_prod, area_ecology, hist_energy, table_invest) |
| `company_ids` | array | Да | Список ID компаний для генерации графика |

**Response 200**

```json
{
  "id": 1,
  "graph_type": "treemap_prod",
  "user_id": 1,
  "company_ids": [1, 2, 3],
  "graph_data": {
    "data": [...],
    "layout": {...}
  },
  "created_at": "2025-01-18T14:30:00Z"
}
```

**Response 403**

```json
{
  "detail": "У вас нет доступа к компаниям с ID: [4, 5]"
}
```

**Response 404**

```json
{
  "detail": "Не найдены данные компаний"
}
```

---

### POST `/api/v1/graphs/generate-all`

Генерирует все доступные типы графиков для указанных компаний пользователя.

**Headers**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `Authorization` | string | Да | Bearer токен авторизации |

**Request Body (JSON)**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `company_ids` | array | Да | Список ID компаний для генерации графиков |

**Response 200**

```json
[
  {
    "id": 1,
    "graph_type": "treemap_prod",
    "user_id": 1,
    "company_ids": [1, 2, 3],
    "graph_data": {...},
    "created_at": "2025-01-18T14:30:00Z"
  },
  {
    "id": 2,
    "graph_type": "scatter_busy",
    "user_id": 1,
    "company_ids": [1, 2, 3],
    "graph_data": {...},
    "created_at": "2025-01-18T14:30:01Z"
  }
]
```

---

### GET `/api/v1/graphs/`

Получает все графики пользователя.

**Headers**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `Authorization` | string | Да | Bearer токен авторизации |

**Response 200**

```json
[
  {
    "id": 1,
    "graph_type": "treemap_prod",
    "user_id": 1,
    "company_ids": [1, 2, 3],
    "graph_data": {...},
    "created_at": "2025-01-18T14:30:00Z"
  }
]
```

---

### GET `/api/v1/graphs/{graph_id}`

Получает конкретный график пользователя по ID.

**Headers**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `Authorization` | string | Да | Bearer токен авторизации |

**Path Parameters**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `graph_id` | integer | Да | ID графика |

**Response 200**

```json
{
  "id": 1,
  "graph_type": "treemap_prod",
  "user_id": 1,
  "company_ids": [1, 2, 3],
  "graph_data": {...},
  "created_at": "2025-01-18T14:30:00Z"
}
```

**Response 404**

```json
{
  "detail": "График не найден"
}
```

---

### DELETE `/api/v1/graphs/{graph_id}`

Удаляет график пользователя.

**Headers**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `Authorization` | string | Да | Bearer токен авторизации |

**Path Parameters**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `graph_id` | integer | Да | ID графика |

**Response 200**

```json
{
  "message": "График успешно удален"
}
```

**Response 404**

```json
{
  "detail": "График не найден"
}
```

### Типы графиков

| Тип            | Описание                                 |
| -------------- | ---------------------------------------- |
| `treemap_prod` | Древовидная карта (сектор Производство)  |
| `scatter_busy` | Точечный график (сектор Занятость)       |
| `norm_export`  | Нормированные столбцы (сектор Экспорт)   |
| `pie_prod`     | Круговая диаграмма (сектор Производство) |
| `area_ecology` | Диаграмма с областями (сектор Экология)  |
| `hist_energy`  | Гистограмма (сектор Энергопотребление)   |
| `table_invest` | Сводная таблица (сектор Инвестиции)      |

---

## Парсинг компаний

### POST `/api/v1/companies/parse/bulk`

Массовый парсинг всех компаний из тестового файла. Парсит все доступные компании и сохраняет их в базу данных пользователя.

**Headers**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `Authorization` | string | Да | Bearer токен авторизации |

**Response 200**

```json
{
  "parsed_count": 80,
  "saved_count": 75,
  "skipped_count": 5,
  "companies": [
    {
      "id": 1,
      "name": "ООО \"РУ КМЗ\"",
      "full_name": "ООО \"РУ КМЗ\"",
      "inn": 7721840520,
      "year": 2021,
      "spark_status": "Активная",
      "main_industry": "Машиностроение",
      "company_size_final": "Среднее",
      "organization_type": "ООО",
      "support_measures": true,
      "special_status": "Сведения отсутствуют",
      "confirmation_status": "confirmed",
      "confirmed_at": "2025-01-18T14:30:00Z",
      "confirmer_identifier": "Росстат",
      "json_data": {...},
      "created_at": "2025-01-18T14:30:00Z",
      "updated_at": "2025-01-18T14:30:00Z"
    }
  ],
  "message": "Парсинг завершен. Обработано 80 компаний, сохранено 75, пропущено 5"
}
```

**Response 500**

```json
{
  "detail": "Ошибка при массовом парсинге: <описание ошибки>"
}
```

---

### POST `/api/v1/companies/parse/search-by-inn`

Поиск и парсинг компании по ИНН. Ищет конкретную компанию в тестовых данных и сохраняет её в базу данных пользователя.

**Headers**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `Authorization` | string | Да | Bearer токен авторизации |

**Request Body (JSON)**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `query` | string | Да | ИНН компании для поиска |
| `save_to_db` | boolean | Нет | Сохранять найденную компанию в базу данных (по умолчанию: true) |

**Request Example**

```json
{
  "query": "7721840520",
  "save_to_db": true
}
```

**Response 200**

```json
{
  "parsed_count": 1,
  "saved_count": 1,
  "skipped_count": 0,
  "companies": [
    {
      "id": 1,
      "name": "ООО \"РУ КМЗ\"",
      "full_name": "ООО \"РУ КМЗ\"",
      "inn": 7721840520,
      "year": 2021,
      "spark_status": "Активная",
      "main_industry": "Машиностроение",
      "company_size_final": "Среднее",
      "organization_type": "ООО",
      "support_measures": true,
      "special_status": "Сведения отсутствуют",
      "confirmation_status": "confirmed",
      "confirmed_at": "2025-01-18T14:30:00Z",
      "confirmer_identifier": "Росстат",
      "json_data": {...},
      "created_at": "2025-01-18T14:30:00Z",
      "updated_at": "2025-01-18T14:30:00Z"
    }
  ],
  "message": "Найдена компания с ИНН 7721840520. Сохранено: 1"
}
```

**Response 200 (компания не найдена)**

```json
{
  "parsed_count": 0,
  "saved_count": 0,
  "skipped_count": 0,
  "companies": [],
  "message": "Компания с ИНН 7721840520 не найдена"
}
```

**Response 500**

```json
{
  "detail": "Ошибка при поиске по ИНН: <описание ошибки>"
}
```

---

### POST `/api/v1/companies/parse/search-by-industry`

Поиск и парсинг компаний по отрасли. Ищет все компании в указанной отрасли и сохраняет их в базу данных пользователя.

**Headers**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `Authorization` | string | Да | Bearer токен авторизации |

**Request Body (JSON)**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `query` | string | Да | Название отрасли для поиска |
| `save_to_db` | boolean | Нет | Сохранять найденные компании в базу данных (по умолчанию: true) |

**Request Example**

```json
{
  "query": "IT",
  "save_to_db": true
}
```

**Response 200**

```json
{
  "parsed_count": 15,
  "saved_count": 12,
  "skipped_count": 3,
  "companies": [
    {
      "id": 2,
      "name": "ООО \"Технологии\"",
      "full_name": "ООО \"Технологии\"",
      "inn": 1234567890,
      "year": 2021,
      "spark_status": "Активная",
      "main_industry": "IT",
      "company_size_final": "Малое",
      "organization_type": "ООО",
      "support_measures": false,
      "special_status": "Сведения отсутствуют",
      "confirmation_status": "not_confirmed",
      "confirmed_at": null,
      "confirmer_identifier": "",
      "json_data": {...},
      "created_at": "2025-01-18T14:30:00Z",
      "updated_at": "2025-01-18T14:30:00Z"
    }
  ],
  "message": "Найдено 15 компаний в отрасли 'IT'. Сохранено: 12"
}
```

**Response 200 (компании не найдены)**

```json
{
  "parsed_count": 0,
  "saved_count": 0,
  "skipped_count": 0,
  "companies": [],
  "message": "Компании в отрасли 'IT' не найдены"
}
```

**Response 500**

```json
{
  "detail": "Ошибка при поиске по отрасли: <описание ошибки>"
}
```

---

### POST `/api/v1/companies/parse/search-by-status`

Поиск и парсинг компаний по статусу. Ищет все компании с указанным статусом и сохраняет их в базу данных пользователя.

**Headers**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `Authorization` | string | Да | Bearer токен авторизации |

**Request Body (JSON)**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `query` | string | Да | Статус компании для поиска |
| `save_to_db` | boolean | Нет | Сохранять найденные компании в базу данных (по умолчанию: true) |

**Request Example**

```json
{
  "query": "Подтвержден",
  "save_to_db": true
}
```

**Response 200**

```json
{
  "parsed_count": 25,
  "saved_count": 20,
  "skipped_count": 5,
  "companies": [
    {
      "id": 3,
      "name": "ООО \"Промышленность\"",
      "full_name": "ООО \"Промышленность\"",
      "inn": 9876543210,
      "year": 2021,
      "spark_status": "Активная",
      "main_industry": "Машиностроение",
      "company_size_final": "Крупное",
      "organization_type": "ООО",
      "support_measures": true,
      "special_status": "Сведения отсутствуют",
      "confirmation_status": "confirmed",
      "confirmed_at": "2025-01-18T14:30:00Z",
      "confirmer_identifier": "Росстат",
      "json_data": {...},
      "created_at": "2025-01-18T14:30:00Z",
      "updated_at": "2025-01-18T14:30:00Z"
    }
  ],
  "message": "Найдено 25 компаний со статусом 'Подтвержден'. Сохранено: 20"
}
```

**Response 200 (компании не найдены)**

```json
{
  "parsed_count": 0,
  "saved_count": 0,
  "skipped_count": 0,
  "companies": [],
  "message": "Компании со статусом 'Подтвержден' не найдены"
}
```

**Response 500**

```json
{
  "detail": "Ошибка при поиске по статусу: <описание ошибки>"
}
```

---

## Модели данных для парсинга

### ParseResponse

Модель ответа для всех эндпоинтов парсинга.

| Поле            | Тип                | Описание                         |
| --------------- | ------------------ | -------------------------------- |
| `parsed_count`  | integer            | Количество распарсенных компаний |
| `saved_count`   | integer            | Количество сохраненных компаний  |
| `skipped_count` | integer            | Количество пропущенных компаний  |
| `companies`     | array[CompanyRead] | Список сохраненных компаний      |
| `message`       | string             | Сообщение о результате операции  |

### ParseSearchRequest

Модель запроса для поисковых эндпоинтов парсинга.

| Поле         | Тип     | Обязательно | Описание                                                        |
| ------------ | ------- | ----------- | --------------------------------------------------------------- |
| `query`      | string  | Да          | Поисковый запрос (ИНН, отрасль или статус)                      |
| `save_to_db` | boolean | Нет         | Сохранять найденные компании в базу данных (по умолчанию: true) |

---

## Особенности работы парсинга

### Умное сохранение

- Система проверяет, не существует ли уже компания с таким ИНН и годом
- Если компания существует, но не принадлежит пользователю, создается связь
- Если компания уже принадлежит пользователю, она пропускается

### Обработка ошибок

- При ошибке сохранения отдельной компании, она пропускается, но процесс продолжается
- Все операции выполняются в транзакциях с возможностью rollback
- Подробная статистика показывает количество обработанных, сохраненных и пропущенных компаний

### Источник данных

- Парсинг выполняется из файла `src/parser/test_data.csv`
- Данные содержат информацию о московских предприятиях
- Поддерживаются различные отрасли, статусы и типы организаций
