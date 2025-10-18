# /src/api/companies.py

import logging
from datetime import datetime, timezone
from logging.config import dictConfig
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from api.auth import get_current_user
from database.database import db
from logging_config import LOGGING_CONFIG, ColoredFormatter
from models import Company, User, UserCompanyLink, ConfirmationStatus, CompanyUpdate, CompanyRead
from repositories.company_repository import CompanyRepository
from csv_reader.reader import AsyncCSVReader
from parser.parser import ParserEmulator

# Setup logging
dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
root_logger = logging.getLogger()
for handler in root_logger.handlers:
    if type(handler) is logging.StreamHandler:
        handler.setFormatter(ColoredFormatter('%(levelname)s:     %(asctime)s %(name)s - %(message)s'))

router = APIRouter(prefix="/companies", tags=["companies"])

# =========================
# Модели
# =========================

class CompanyUpdateRequest(BaseModel):
    """Модель для обновления основных полей компании"""
    name: Optional[str] = Field(None, description="Название компании")
    full_name: Optional[str] = Field(None, description="Полное наименование компании")
    inn: Optional[int] = Field(None, description="ИНН компании")
    year: Optional[int] = Field(None, description="Год")
    spark_status: Optional[str] = Field(None, description="Статус СПАРК")
    main_industry: Optional[str] = Field(None, description="Основная отрасль")
    company_size_final: Optional[str] = Field(None, description="Размер предприятия (итог)")
    organization_type: Optional[str] = Field(None, description="Тип организации")
    support_measures: Optional[bool] = Field(None, description="Меры поддержки")
    special_status: Optional[str] = Field(None, description="Особый статус")
    confirmation_status: Optional[ConfirmationStatus] = Field(None, description="Статус подтверждения")
    confirmed_at: Optional[datetime] = Field(None, description="Когда подтвердили компанию")
    confirmer_identifier: Optional[str] = Field(None, description="Идентификатор подтверждающего")

class CompanyKeyMetricsUpdate(BaseModel):
    """Модель для обновления ключевых метрик"""
    spark_status: Optional[str] = Field(None, description="Статус СПАРК")
    main_industry: Optional[str] = Field(None, description="Основная отрасль")
    company_size_final: Optional[str] = Field(None, description="Размер предприятия (итог)")
    organization_type: Optional[str] = Field(None, description="Тип организации")
    support_measures: Optional[bool] = Field(None, description="Меры поддержки")
    special_status: Optional[str] = Field(None, description="Особый статус")

class CompanyJsonDataUpdate(BaseModel):
    """Модель для обновления JSON данных"""
    json_data: Dict[str, Any] = Field(..., description="Полные JSON данные компании")

class CompanyJsonCreate(BaseModel):
    """Модель для создания компании из JSON данных"""
    number: Optional[int] = Field(None, alias="№", description="Номер записи")
    inn: int = Field(..., alias="ИНН", description="ИНН компании")
    name: str = Field(..., alias="Наименование организации", description="Название организации")
    main_industry: str = Field(..., alias="Основная отрасль", description="Основная отрасль")
    sub_industry: Optional[str] = Field(None, alias="Подотрасль (Основная)", description="Подотрасль")
    support_measures: Optional[str] = Field(None, alias="Данные об оказанных мерах поддержки", description="Меры поддержки")
    special_status: Optional[str] = Field(None, alias="Наличие особого статуса", description="Особый статус")
    revenue: Optional[float] = Field(None, alias="Выручка предприятия, тыс. руб", description="Выручка")
    net_profit: Optional[float] = Field(None, alias="Чистая прибыль (убыток),тыс. руб.", description="Чистая прибыль")
    staff_count: Optional[int] = Field(None, alias="Среднесписочная численность персонала, работающего в Москве, чел", description="Численность персонала")
    payroll_fund: Optional[float] = Field(None, alias="Фонд оплаты труда  сотрудников, работающих в Москве, тыс. руб.", description="Фонд оплаты труда")
    avg_salary: Optional[float] = Field(None, alias="Средняя з.п. сотрудников, работающих в Москве,  тыс.руб.", description="Средняя зарплата")
    moscow_taxes: Optional[float] = Field(None, alias="Налоги, уплаченные в бюджет Москвы (без акцизов), тыс.руб.", description="Налоги в бюджет Москвы")
    profit_tax: Optional[float] = Field(None, alias="Налог на прибыль, тыс.руб.", description="Налог на прибыль")
    property_tax: Optional[float] = Field(None, alias="Налог на имущество, тыс.руб.", description="Налог на имущество")
    land_tax: Optional[float] = Field(None, alias="Налог на землю, тыс.руб.", description="Налог на землю")
    income_tax: Optional[float] = Field(None, alias="НДФЛ, тыс.руб.", description="НДФЛ")
    transport_tax: Optional[float] = Field(None, alias="Транспортный налог, тыс.руб.", description="Транспортный налог")
    other_taxes: Optional[float] = Field(None, alias="Прочие налоги", description="Прочие налоги")
    excise_taxes: Optional[float] = Field(None, alias="Акцизы, тыс. руб.", description="Акцизы")
    moscow_investments: Optional[float] = Field(None, alias="Инвестиции в Мск  тыс. руб.", description="Инвестиции в Москву")
    export_volume: Optional[float] = Field(None, alias="Объем экспорта, тыс. руб.", description="Объем экспорта")
    capacity_utilization: Optional[int] = Field(None, alias="Уровень загрузки производственных мощностей", description="Уровень загрузки")
    has_export: Optional[str] = Field(None, alias="Наличие поставок продукции на экспорт", description="Наличие экспорта")
    prev_year_export: Optional[float] = Field(None, alias="Объем экспорта (млн руб.) за предыдущий календарный год", description="Объем экспорта за предыдущий год")
    production_coordinates: Optional[str] = Field(None, alias="Координаты адреса производства", description="Координаты производства")
    district: Optional[str] = Field(None, alias="Округ", description="Округ")
    area: Optional[str] = Field(None, alias="Район", description="Район")
    year: int = Field(..., alias="Год", description="Год")
    confirmed: Optional[str] = Field(None, alias="Подтвержден", description="Статус подтверждения")
    confirmed_by: Optional[str] = Field(None, alias="Кем подтвержден", description="Кем подтвержден")
    organization_type: Optional[str] = Field(None, alias="Вид организации", description="Вид организации")
    last_modified: Optional[str] = Field(None, alias="Дата последнего изменения", description="Дата последнего изменения")

class CompanyListResponse(BaseModel):
    """Модель ответа со списком компаний"""
    companies: List[CompanyRead]
    total: int
    limit: int
    offset: int

class ParseResponse(BaseModel):
    """Модель ответа для парсинга"""
    parsed_count: int = Field(..., description="Количество распарсенных компаний")
    saved_count: int = Field(..., description="Количество сохраненных компаний")
    skipped_count: int = Field(..., description="Количество пропущенных компаний")
    companies: List[CompanyRead] = Field(..., description="Список сохраненных компаний")
    message: str = Field(..., description="Сообщение о результате")

class ParseSearchRequest(BaseModel):
    """Модель запроса для поиска при парсинге"""
    query: str = Field(..., description="Поисковый запрос")
    save_to_db: bool = Field(True, description="Сохранять найденные компании в базу данных")

# =========================
# Утилиты
# =========================

def get_session() -> Session:
    """Получает сессию базы данных"""
    return db.getSession()

def check_company_ownership(company_id: int, user_id: int, session: Session) -> Company:
    """Проверяет, что компания принадлежит пользователю"""
    statement = (
        select(Company)
        .join(UserCompanyLink)
        .where(
            Company.id == company_id,
            UserCompanyLink.user_id == user_id
        )
    )

    company = session.exec(statement).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found or access denied"
        )
    return company

async def save_parsed_companies_to_db(
    parsed_companies: List[Dict[str, Any]],
    user_id: int,
    session: Session
) -> tuple[int, int, List[CompanyRead]]:
    """
    Сохраняет распарсенные компании в базу данных.

    Returns:
        Кортеж из (количество сохраненных, количество пропущенных, список сохраненных компаний)
    """
    saved_count = 0
    skipped_count = 0
    saved_companies = []

    for company_data in parsed_companies:
        try:
            # Преобразуем данные в формат для базы данных
            company_dict = AsyncCSVReader.create_company_from_json(company_data)

            # Проверяем, не существует ли уже компания с таким ИНН и годом
            existing_company = session.exec(
                select(Company).where(
                    Company.inn == company_dict["inn"],
                    Company.year == company_dict["year"]
                )
            ).first()

            if existing_company:
                # Проверяем, не принадлежит ли уже эта компания пользователю
                existing_link = session.exec(
                    select(UserCompanyLink).where(
                        UserCompanyLink.user_id == user_id,
                        UserCompanyLink.company_id == existing_company.id
                    )
                ).first()

                if not existing_link:
                    # Компания существует, но не принадлежит пользователю - добавляем связь
                    user_company_link = UserCompanyLink(
                        user_id=user_id,
                        company_id=existing_company.id
                    )
                    session.add(user_company_link)
                    session.flush()

                    # Преобразуем в CompanyRead
                    company_read = CompanyRead(
                        id=existing_company.id,
                        name=existing_company.name,
                        full_name=existing_company.full_name,
                        inn=existing_company.inn,
                        year=existing_company.year,
                        spark_status=existing_company.spark_status,
                        main_industry=existing_company.main_industry,
                        company_size_final=existing_company.company_size_final,
                        organization_type=existing_company.organization_type,
                        support_measures=existing_company.support_measures,
                        special_status=existing_company.special_status,
                        confirmation_status=existing_company.confirmation_status,
                        confirmed_at=existing_company.confirmed_at,
                        confirmer_identifier=existing_company.confirmer_identifier,
                        json_data=existing_company.json_data,
                        created_at=existing_company.created_at,
                        updated_at=existing_company.updated_at
                    )
                    saved_companies.append(company_read)
                    saved_count += 1
                else:
                    # Компания уже принадлежит пользователю
                    skipped_count += 1
            else:
                # Создаем новую компанию
                company = Company(
                    inn=company_dict["inn"],
                    name=company_dict["name"],
                    full_name=company_dict["full_name"],
                    year=company_dict["year"],
                    spark_status=company_dict["spark_status"],
                    main_industry=company_dict["main_industry"],
                    company_size_final=company_dict["company_size_final"],
                    organization_type=company_dict["organization_type"],
                    support_measures=company_dict["support_measures"],
                    special_status=company_dict["special_status"],
                    confirmation_status=company_dict["confirmation_status"],
                    confirmed_at=company_dict["confirmed_at"],
                    confirmer_identifier=company_dict["confirmer_identifier"],
                    json_data=company_dict["json_data"]
                )

                session.add(company)
                session.flush()  # Получаем ID

                # Создаем связь пользователя с компанией
                user_company_link = UserCompanyLink(
                    user_id=user_id,
                    company_id=company.id
                )
                session.add(user_company_link)

                # Преобразуем в CompanyRead
                company_read = CompanyRead(
                    id=company.id,
                    name=company.name,
                    full_name=company.full_name,
                    inn=company.inn,
                    year=company.year,
                    spark_status=company.spark_status,
                    main_industry=company.main_industry,
                    company_size_final=company.company_size_final,
                    organization_type=company.organization_type,
                    support_measures=company.support_measures,
                    special_status=company.special_status,
                    confirmation_status=company.confirmation_status,
                    confirmed_at=company.confirmed_at,
                    confirmer_identifier=company.confirmer_identifier,
                    json_data=company.json_data,
                    created_at=company.created_at,
                    updated_at=company.updated_at
                )
                saved_companies.append(company_read)
                saved_count += 1

        except Exception as e:
            logger.warning(f"Ошибка при сохранении компании: {e}")
            skipped_count += 1
            continue

    return saved_count, skipped_count, saved_companies

# =========================
# Эндпоинты
# =========================

@router.get("/", response_model=CompanyListResponse)
async def get_user_companies(
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=50, description="Количество записей"),
    offset: int = Query(default=0, description="Смещение"),
):
    """Получить список компаний пользователя"""
    logger.info(f"Getting companies for user: {current_user.username}")

    session = get_session()
    try:
        statement = (
            select(Company)
            .join(UserCompanyLink)
            .where(UserCompanyLink.user_id == current_user.id)
            .limit(limit)
            .offset(offset)
        )

        companies = session.exec(statement).all()

        company_responses = [
            CompanyRead(
                id=company.id,
                inn=company.inn,
                name=company.name,
                full_name=company.full_name,
                year=company.year,
                spark_status=company.spark_status,
                main_industry=company.main_industry,
                company_size_final=company.company_size_final,
                organization_type=company.organization_type,
                support_measures=company.support_measures,
                special_status=company.special_status,
                confirmation_status=company.confirmation_status,
                confirmed_at=company.confirmed_at,
                confirmer_identifier=company.confirmer_identifier,
                json_data=company.json_data,
                created_at=company.created_at,
                updated_at=company.updated_at
            )
            for company in companies
        ]

        return CompanyListResponse(
            companies=company_responses,
            total=len(company_responses),
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error getting companies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get companies"
        )
    finally:
        session.close()

@router.get("/filter", response_model=CompanyListResponse)
async def filter_companies(
    current_user: User = Depends(get_current_user),
    spark_status: Optional[str] = Query(None, description="Статус СПАРК"),
    main_industry: Optional[str] = Query(None, description="Основная отрасль"),
    company_size_final: Optional[str] = Query(None, description="Размер предприятия"),
    organization_type: Optional[str] = Query(None, description="Тип организации"),
    support_measures: Optional[bool] = Query(None, description="Получены ли меры поддержки"),
    special_status: Optional[str] = Query(None, description="Особый статус"),
    year: Optional[int] = Query(None, description="Год"),
    limit: int = Query(default=50, ge=1, le=100, description="Количество записей"),
    offset: int = Query(default=0, ge=0, description="Смещение"),
):
    """Фильтровать компании пользователя по метрикам"""
    logger.info(f"Filtering companies for user: {current_user.username}")

    session = get_session()
    try:
        # Используем репозиторий для фильтрации с автоматической фильтрацией по пользователю
        company_repo = CompanyRepository(session)
        companies = company_repo.filter_by_metrics(
            user_id=current_user.id,
            spark_status=spark_status,
            main_industry=main_industry,
            company_size_final=company_size_final,
            organization_type=organization_type,
            support_measures=support_measures,
            special_status=special_status,
            year=year,
            skip=offset,
            limit=limit
        )

        logger.info(f"Found {len(companies)} companies matching filters for user {current_user.username}")

        return CompanyListResponse(
            companies=companies,
            total=len(companies),
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error filtering companies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to filter companies"
        )
    finally:
        session.close()

@router.get("/{company_id}", response_model=CompanyRead)
async def get_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
):
    """Получить детальную информацию о компании"""
    logger.info(f"Getting company {company_id} for user: {current_user.username}")

    session = get_session()
    try:
        company = check_company_ownership(company_id, current_user.id, session)

        return CompanyRead(
            id=company.id,
            inn=company.inn,
            name=company.name,
            full_name=company.full_name,
            year=company.year,
            spark_status=company.spark_status,
            main_industry=company.main_industry,
            company_size_final=company.company_size_final,
            organization_type=company.organization_type,
            support_measures=company.support_measures,
            special_status=company.special_status,
            confirmation_status=company.confirmation_status,
            confirmed_at=company.confirmed_at,
            confirmer_identifier=company.confirmer_identifier,
            json_data=company.json_data,
            created_at=company.created_at,
            updated_at=company.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get company"
        )
    finally:
        session.close()



@router.patch("/{company_id}", response_model=CompanyRead)
async def update_company(
    company_id: int,
    update_data: CompanyUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    """Обновить основные данные компании"""
    logger.info(f"Updating company {company_id} for user: {current_user.username}")

    session = get_session()
    try:
        company = check_company_ownership(company_id, current_user.id, session)

        # Обновляем только переданные поля
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if hasattr(company, key) and value is not None:
                setattr(company, key, value)

        # Обновляем время изменения
        company.updated_at = datetime.now(timezone.utc)

        session.add(company)
        session.commit()
        session.refresh(company)

        logger.info(f"Company {company_id} updated successfully")

        return CompanyRead(
            id=company.id,
            inn=company.inn,
            name=company.name,
            full_name=company.full_name,
            year=company.year,
            spark_status=company.spark_status,
            main_industry=company.main_industry,
            company_size_final=company.company_size_final,
            organization_type=company.organization_type,
            support_measures=company.support_measures,
            special_status=company.special_status,
            confirmation_status=company.confirmation_status,
            confirmed_at=company.confirmed_at,
            confirmer_identifier=company.confirmer_identifier,
            json_data=company.json_data,
            created_at=company.created_at,
            updated_at=company.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating company: {e}", exc_info=True)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update company"
        )
    finally:
        session.close()

@router.patch("/{company_id}/key-metrics", response_model=CompanyRead)
async def update_company_key_metrics(
    company_id: int,
    metrics_data: CompanyKeyMetricsUpdate,
    current_user: User = Depends(get_current_user),
):
    """Обновить ключевые метрики компании"""
    logger.info(f"Updating key metrics for company {company_id} for user: {current_user.username}")

    session = get_session()
    try:
        company = check_company_ownership(company_id, current_user.id, session)

        # Обновляем только переданные метрики
        update_dict = metrics_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if hasattr(company, key) and value is not None:
                setattr(company, key, value)

        # Обновляем время изменения
        company.updated_at = datetime.now(timezone.utc)

        session.add(company)
        session.commit()
        session.refresh(company)

        logger.info(f"Key metrics for company {company_id} updated successfully")

        return CompanyRead(
            id=company.id,
            inn=company.inn,
            name=company.name,
            full_name=company.full_name,
            year=company.year,
            spark_status=company.spark_status,
            main_industry=company.main_industry,
            company_size_final=company.company_size_final,
            organization_type=company.organization_type,
            support_measures=company.support_measures,
            special_status=company.special_status,
            confirmation_status=company.confirmation_status,
            confirmed_at=company.confirmed_at,
            confirmer_identifier=company.confirmer_identifier,
            json_data=company.json_data,
            created_at=company.created_at,
            updated_at=company.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating key metrics: {e}", exc_info=True)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update key metrics"
        )
    finally:
        session.close()

@router.patch("/{company_id}/json-data", response_model=Dict[str, Any])
async def update_company_json_data(
    company_id: int,
    json_data: CompanyJsonDataUpdate,
    current_user: User = Depends(get_current_user),
):
    """Обновить JSON данные компании"""
    logger.info(f"Updating JSON data for company {company_id} for user: {current_user.username}")

    session = get_session()
    try:
        company = check_company_ownership(company_id, current_user.id, session)

        # Обновляем JSON данные
        company.json_data = json_data.json_data
        company.updated_at = datetime.now(timezone.utc)

        session.add(company)
        session.commit()
        session.refresh(company)

        logger.info(f"JSON data for company {company_id} updated successfully")

        return {
            "company_id": company.id,
            "json_data": company.json_data,
            "updated_at": company.updated_at
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating JSON data: {e}", exc_info=True)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update JSON data"
        )
    finally:
        session.close()

@router.get("/{company_id}/json-data", response_model=Dict[str, Any])
async def get_company_json_data(
    company_id: int,
    current_user: User = Depends(get_current_user),
):
    """Получить JSON данные компании"""
    logger.info(f"Getting JSON data for company {company_id} for user: {current_user.username}")

    session = get_session()
    try:
        company = check_company_ownership(company_id, current_user.id, session)

        return {
            "company_id": company.id,
            "json_data": company.json_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting JSON data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get JSON data"
        )
    finally:
        session.close()

@router.post("/create-from-json", response_model=CompanyRead)
async def create_company_from_json(
    json_data: CompanyJsonCreate,
    current_user: User = Depends(get_current_user),
):
    """Создать компанию из JSON данных"""
    logger.info(f"Creating company from JSON for user: {current_user.username}")

    session = get_session()
    try:
        # Преобразуем Pydantic модель в словарь
        json_dict = json_data.model_dump()

        # Используем статический метод из AsyncCSVReader для создания компании
        company_data = AsyncCSVReader.create_company_from_json(json_dict)

        # Проверяем, не существует ли уже компания с таким ИНН и годом
        existing_company = session.exec(
            select(Company).where(
                Company.inn == company_data["inn"],
                Company.year == company_data["year"]
            )
        ).first()

        if existing_company:
            # Проверяем, не принадлежит ли уже эта компания пользователю
            existing_link = session.exec(
                select(UserCompanyLink).where(
                    UserCompanyLink.user_id == current_user.id,
                    UserCompanyLink.company_id == existing_company.id
                )
            ).first()

            if existing_link:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Компания с таким ИНН и годом уже существует у пользователя"
                )
            else:
                # Компания существует, но не принадлежит пользователю - добавляем связь
                user_company_link = UserCompanyLink(
                    user_id=current_user.id,
                    company_id=existing_company.id
                )
                session.add(user_company_link)
                session.commit()

                logger.info(f"Added existing company {existing_company.id} to user {current_user.id}")

                # Преобразуем существующую компанию в CompanyRead
                return CompanyRead(
                    id=existing_company.id,
                    name=existing_company.name,
                    full_name=existing_company.full_name,
                    inn=existing_company.inn,
                    year=existing_company.year,
                    spark_status=existing_company.spark_status,
                    main_industry=existing_company.main_industry,
                    company_size_final=existing_company.company_size_final,
                    organization_type=existing_company.organization_type,
                    support_measures=existing_company.support_measures,
                    special_status=existing_company.special_status,
                    confirmation_status=existing_company.confirmation_status,
                    confirmed_at=existing_company.confirmed_at,
                    confirmer_identifier=existing_company.confirmer_identifier,
                    json_data=existing_company.json_data,
                    created_at=existing_company.created_at,
                    updated_at=existing_company.updated_at
                )

        # Создаем новую компанию
        company = Company(
            inn=company_data["inn"],
            name=company_data["name"],
            full_name=company_data["full_name"],
            year=company_data["year"],
            spark_status=company_data["spark_status"],
            main_industry=company_data["main_industry"],
            company_size_final=company_data["company_size_final"],
            organization_type=company_data["organization_type"],
            support_measures=company_data["support_measures"],
            special_status=company_data["special_status"],
            confirmation_status=company_data["confirmation_status"],
            confirmed_at=company_data["confirmed_at"],
            confirmer_identifier=company_data["confirmer_identifier"],
            json_data=company_data["json_data"]
        )

        session.add(company)
        session.flush()  # Получаем ID

        # Создаем связь пользователя с компанией
        user_company_link = UserCompanyLink(
            user_id=current_user.id,
            company_id=company.id
        )
        session.add(user_company_link)

        session.commit()
        session.refresh(company)

        logger.info(f"Created new company {company.id} for user {current_user.id}")

        # Преобразуем в CompanyRead
        return CompanyRead(
            id=company.id,
            name=company.name,
            full_name=company.full_name,
            inn=company.inn,
            year=company.year,
            spark_status=company.spark_status,
            main_industry=company.main_industry,
            company_size_final=company.company_size_final,
            organization_type=company.organization_type,
            support_measures=company.support_measures,
            special_status=company.special_status,
            confirmation_status=company.confirmation_status,
            confirmed_at=company.confirmed_at,
            confirmer_identifier=company.confirmer_identifier,
            json_data=company.json_data,
            created_at=company.created_at,
            updated_at=company.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating company from JSON: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create company from JSON: {e}"
        )
    finally:
        session.close()

@router.delete("/{company_id}")
async def delete_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
):
    """Удалить компанию"""
    logger.info(f"Deleting company {company_id} for user: {current_user.username}")

    session = get_session()
    try:
        company = check_company_ownership(company_id, current_user.id, session)

        # Удаляем связь пользователя с компанией
        user_company_link_statement = select(UserCompanyLink).where(
            UserCompanyLink.user_id == current_user.id,
            UserCompanyLink.company_id == company_id
        )
        user_company_link = session.exec(user_company_link_statement).first()
        if user_company_link:
            session.delete(user_company_link)

        # Удаляем компанию
        session.delete(company)
        session.commit()

        logger.info(f"Company {company_id} deleted successfully")

        return {"message": "Company deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting company: {e}", exc_info=True)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete company"
        )
    finally:
        session.close()

# =========================
# Эндпоинты парсинга
# =========================

@router.post("/parse/bulk", response_model=ParseResponse)
async def bulk_parse_companies(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(db.get_session)
):
    """
    Массовый парсинг всех компаний из тестового файла
    """
    try:
        logger.info(f"Начинаем массовый парсинг для пользователя: {current_user.username}")

        # Создаем эмулятор парсера
        parser = ParserEmulator()

        # Парсим компании с ключевыми полями
        all_data, key_fields = await parser.parse_companies_with_key_fields()

        # Сохраняем в базу данных
        saved_count, skipped_count, saved_companies = await save_parsed_companies_to_db(
            all_data, current_user.id, session
        )

        session.commit()

        logger.info(f"Массовый парсинг завершен. Сохранено: {saved_count}, пропущено: {skipped_count}")

        return ParseResponse(
            parsed_count=len(all_data),
            saved_count=saved_count,
            skipped_count=skipped_count,
            companies=saved_companies,
            message=f"Парсинг завершен. Обработано {len(all_data)} компаний, сохранено {saved_count}, пропущено {skipped_count}"
        )

    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при массовом парсинге: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при массовом парсинге: {str(e)}"
        )

@router.post("/parse/search-by-inn", response_model=ParseResponse)
async def parse_search_by_inn(
    request: ParseSearchRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(db.get_session)
):
    """
    Парсинг и поиск компании по ИНН
    """
    try:
        logger.info(f"Поиск компании по ИНН {request.query} для пользователя: {current_user.username}")

        # Создаем эмулятор парсера
        parser = ParserEmulator()

        # Ищем компанию по ИНН
        company = await parser.get_company_by_inn(request.query)

        if not company:
            return ParseResponse(
                parsed_count=0,
                saved_count=0,
                skipped_count=0,
                companies=[],
                message=f"Компания с ИНН {request.query} не найдена"
            )

        # Сохраняем в базу данных, если требуется
        saved_count = 0
        skipped_count = 0
        saved_companies = []

        if request.save_to_db:
            saved_count, skipped_count, saved_companies = await save_parsed_companies_to_db(
                [company], current_user.id, session
            )
            session.commit()

        logger.info(f"Поиск по ИНН завершен. Найдено: 1, сохранено: {saved_count}")

        return ParseResponse(
            parsed_count=1,
            saved_count=saved_count,
            skipped_count=skipped_count,
            companies=saved_companies,
            message=f"Найдена компания с ИНН {request.query}. Сохранено: {saved_count}"
        )

    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при поиске по ИНН: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при поиске по ИНН: {str(e)}"
        )

@router.post("/parse/search-by-industry", response_model=ParseResponse)
async def parse_search_by_industry(
    request: ParseSearchRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(db.get_session)
):
    """
    Парсинг и поиск компаний по отрасли
    """
    try:
        logger.info(f"Поиск компаний по отрасли '{request.query}' для пользователя: {current_user.username}")

        # Создаем эмулятор парсера
        parser = ParserEmulator()

        # Ищем компании по отрасли
        companies = await parser.get_companies_by_industry(request.query)

        if not companies:
            return ParseResponse(
                parsed_count=0,
                saved_count=0,
                skipped_count=0,
                companies=[],
                message=f"Компании в отрасли '{request.query}' не найдены"
            )

        # Сохраняем в базу данных, если требуется
        saved_count = 0
        skipped_count = 0
        saved_companies = []

        if request.save_to_db:
            saved_count, skipped_count, saved_companies = await save_parsed_companies_to_db(
                companies, current_user.id, session
            )
            session.commit()

        logger.info(f"Поиск по отрасли завершен. Найдено: {len(companies)}, сохранено: {saved_count}")

        return ParseResponse(
            parsed_count=len(companies),
            saved_count=saved_count,
            skipped_count=skipped_count,
            companies=saved_companies,
            message=f"Найдено {len(companies)} компаний в отрасли '{request.query}'. Сохранено: {saved_count}"
        )

    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при поиске по отрасли: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при поиске по отрасли: {str(e)}"
        )

@router.post("/parse/search-by-status", response_model=ParseResponse)
async def parse_search_by_status(
    request: ParseSearchRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(db.get_session)
):
    """
    Парсинг и поиск компаний по статусу
    """
    try:
        logger.info(f"Поиск компаний по статусу '{request.query}' для пользователя: {current_user.username}")

        # Создаем эмулятор парсера
        parser = ParserEmulator()

        # Ищем компании по статусу
        companies = await parser.get_companies_by_status(request.query)

        if not companies:
            return ParseResponse(
                parsed_count=0,
                saved_count=0,
                skipped_count=0,
                companies=[],
                message=f"Компании со статусом '{request.query}' не найдены"
            )

        # Сохраняем в базу данных, если требуется
        saved_count = 0
        skipped_count = 0
        saved_companies = []

        if request.save_to_db:
            saved_count, skipped_count, saved_companies = await save_parsed_companies_to_db(
                companies, current_user.id, session
            )
            session.commit()

        logger.info(f"Поиск по статусу завершен. Найдено: {len(companies)}, сохранено: {saved_count}")

        return ParseResponse(
            parsed_count=len(companies),
            saved_count=saved_count,
            skipped_count=skipped_count,
            companies=saved_companies,
            message=f"Найдено {len(companies)} компаний со статусом '{request.query}'. Сохранено: {saved_count}"
        )

    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при поиске по статусу: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при поиске по статусу: {str(e)}"
        )
