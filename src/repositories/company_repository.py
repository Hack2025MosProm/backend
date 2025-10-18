import logging
from typing import List

from sqlmodel import Session, select

from models.models import CompanyCreate, CompanyUpdate, CompanyRead, Company

logger = logging.getLogger(__name__)

def _company_to_company_read(company: Company) -> CompanyRead:
    """Преобразует Company в CompanyRead"""
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

class CompanyRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: CompanyCreate) -> CompanyCreate:
        self.session.add(data)
        self.session.commit()
        self.session.refresh(data)
        return data

    def get_by_id(self, record_id: int) -> CompanyRead | None:
        company = self.session.get(Company, record_id)
        if not company:
            return None
        return _company_to_company_read(company)

    def list_all(self, skip: int = 0, limit: int = 100) -> List[CompanyRead]:
        statement = select(Company).offset(skip).limit(limit)
        results = self.session.exec(statement).all()
        return [_company_to_company_read(company) for company in results]

    def get_by_inn(self, inn: str) -> CompanyRead | None:
        statement = select(Company).where(Company.inn == inn)
        company = self.session.exec(statement).first()
        if not company:
            return None
        return _company_to_company_read(company)

    def get_by_inn_and_year(self, inn: str, year: int) -> CompanyRead | None:
        statement = select(Company).where(Company.inn == inn, Company.year == year)
        company = self.session.exec(statement).first()
        if not company:
            return None
        return _company_to_company_read(company)

    def filter_by_metrics(
        self,
        user_id: int = None,
        spark_status: str = None,
        main_industry: str = None,
        company_size_final: str = None,
        organization_type: str = None,
        support_measures: bool = None,
        special_status: str = None,
        years: List[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CompanyRead]:
        """
        Фильтрует компании по заданным метрикам.
        """
        from models.models import UserCompanyLink, Company

        statement = select(Company)

        # Фильтрация по пользователю - добавляем JOIN с таблицей связей
        if user_id is not None:
            statement = statement.join(UserCompanyLink, Company.id == UserCompanyLink.company_id)
            statement = statement.where(UserCompanyLink.user_id == user_id)

        if spark_status is not None:
            statement = statement.where(Company.spark_status == spark_status)
        if main_industry is not None:
            statement = statement.where(Company.main_industry == main_industry)
        if company_size_final is not None:
            statement = statement.where(Company.company_size_final == company_size_final)
        if organization_type is not None:
            statement = statement.where(Company.organization_type == organization_type)
        if support_measures is not None:
            statement = statement.where(Company.support_measures == support_measures)
        if special_status is not None:
            statement = statement.where(Company.special_status == special_status)
        if years is not None and len(years) > 0:
            statement = statement.where(Company.year.in_(years))

        statement = statement.offset(skip).limit(limit)
        results = self.session.exec(statement).all()
        return [_company_to_company_read(company) for company in results]

    def update(self, db_obj: CompanyRead, obj_in: CompanyUpdate) -> CompanyRead:
        """Частично обновляет запись в БД."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)

        self.session.add(db_obj)
        self.session.commit()
        self.session.refresh(db_obj)
        return db_obj

    def delete(self, record_id: int) -> bool:
        """Удаляет запись по ID и возвращает True в случае успеха."""
        record = self.get_by_id(record_id)
        if not record:
            return False

        self.session.delete(record)
        self.session.commit()
        return True