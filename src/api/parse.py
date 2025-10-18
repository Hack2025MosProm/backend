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

router = APIRouter(prefix="/parser", tags=["parser"])

# =========================
# Утилиты
# =========================

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
# Модели
# =========================


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
# Эндпоинты
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
