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
