import logging
from logging.config import dictConfig
from pathlib import Path
from typing import Any, Dict, List

from csv_reader.reader import AsyncCSVReader
from logging_config import LOGGING_CONFIG, ColoredFormatter

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
root_logger = logging.getLogger()
for handler in root_logger.handlers:
    if type(handler) is logging.StreamHandler:
        handler.setFormatter(ColoredFormatter('%(levelname)s:     %(asctime)s %(name)s - %(message)s'))

class ParserEmulator:
    """
    Эмулятор парсера, который читает заранее подготовленные данные из CSV файла.
    """

    def __init__(self, data_file_path: str = None):
        """
        Инициализация эмулятора парсера.

        Args:
            data_file_path: Путь к файлу с тестовыми данными.
                          По умолчанию использует test_data.csv в папке parser
        """
        if data_file_path is None:
            # Используем файл по умолчанию в папке parser
            current_dir = Path(__file__).parent
            data_file_path = str(current_dir / "test_data.csv")

        self.data_file_path = data_file_path
        self.csv_reader = AsyncCSVReader(data_file_path)

        logger.info(f"ParserEmulator инициализирован с файлом: {data_file_path}")

    async def parse_companies(self) -> List[Dict[str, Any]]:
        """
        Эмулирует парсинг компаний, читая данные из CSV файла.

        Returns:
            Список словарей с данными компаний
        """
        try:
            logger.info("Начинаем эмуляцию парсинга компаний")

            # Читаем данные из CSV файла
            companies = await self.csv_reader.read_companies()

            logger.info(f"Эмуляция парсинга завершена. Получено {len(companies)} компаний")

            return companies

        except Exception as e:
            logger.error(f"Ошибка при эмуляции парсинга: {e}")
            raise

    async def parse_companies_with_key_fields(self) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Эмулирует парсинг компаний с извлечением ключевых полей.

        Returns:
            Кортеж из (полные данные, ключевые поля)
        """
        try:
            logger.info("Начинаем эмуляцию парсинга с ключевыми полями")

            # Читаем данные с ключевыми полями
            all_data, key_fields = await self.csv_reader.read_companies_with_key_fields()

            logger.info(f"Эмуляция парсинга завершена. Получено {len(all_data)} полных записей и {len(key_fields)} ключевых полей")

            return all_data, key_fields

        except Exception as e:
            logger.error(f"Ошибка при эмуляции парсинга с ключевыми полями: {e}")
            raise

    async def get_company_by_inn(self, inn: str) -> Dict[str, Any] | None:
        """
        Эмулирует поиск компании по ИНН.

        Args:
            inn: ИНН компании для поиска

        Returns:
            Данные компании или None, если не найдена
        """
        try:
            logger.info(f"Эмуляция поиска компании по ИНН: {inn}")

            company = await self.csv_reader.get_company_by_inn(inn)

            if company:
                logger.info(f"Компания найдена: {company.get('Наименование организации', 'Неизвестно')}")
            else:
                logger.info("Компания не найдена")

            return company

        except Exception as e:
            logger.error(f"Ошибка при поиске компании по ИНН: {e}")
            raise

    async def get_companies_by_industry(self, industry: str) -> List[Dict[str, Any]]:
        """
        Эмулирует поиск компаний по отрасли.

        Args:
            industry: Название отрасли

        Returns:
            Список компаний в указанной отрасли
        """
        try:
            logger.info(f"Эмуляция поиска компаний по отрасли: {industry}")

            companies = await self.csv_reader.get_companies_by_industry(industry)

            logger.info(f"Найдено {len(companies)} компаний в отрасли '{industry}'")

            return companies

        except Exception as e:
            logger.error(f"Ошибка при поиске компаний по отрасли: {e}")
            raise

    async def get_companies_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Эмулирует поиск компаний по статусу.

        Args:
            status: Статус компании

        Returns:
            Список компаний с указанным статусом
        """
        try:
            logger.info(f"Эмуляция поиска компаний по статусу: {status}")

            companies = await self.csv_reader.get_companies_by_status(status)

            logger.info(f"Найдено {len(companies)} компаний со статусом '{status}'")

            return companies

        except Exception as e:
            logger.error(f"Ошибка при поиске компаний по статусу: {e}")
            raise

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Эмулирует получение статистики по данным.

        Returns:
            Словарь со статистикой
        """
        try:
            logger.info("Эмуляция получения статистики")

            companies = await self.parse_companies()

            # Подсчитываем статистику
            total_companies = len(companies)
            industries = {}
            company_sizes = {}
            support_measures = {}
            special_statuses = {}
            districts = {}
            organization_types = {}
            years = {}

            for company in companies:
                # Отрасли
                industry = company.get("Основная отрасль", "Не указана")
                industries[industry] = industries.get(industry, 0) + 1

                # Размеры компаний
                company_size = self.csv_reader._determine_company_size(company)
                company_sizes[company_size] = company_sizes.get(company_size, 0) + 1

                # Меры поддержки
                support = company.get("Данные об оказанных мерах поддержки", "Не указано")
                support_measures[support] = support_measures.get(support, 0) + 1

                # Особые статусы
                special_status = company.get("Наличие особого статуса", "Не указан")
                special_statuses[special_status] = special_statuses.get(special_status, 0) + 1

                # Округа
                district = company.get("Округ", "Не указан")
                districts[district] = districts.get(district, 0) + 1

                # Типы организаций
                org_type = company.get("Вид организации", "Не указан")
                organization_types[org_type] = organization_types.get(org_type, 0) + 1

                # Годы
                year = company.get("Год", "Не указан")
                years[year] = years.get(year, 0) + 1

            statistics = {
                "total_companies": total_companies,
                "industries": industries,
                "company_sizes": company_sizes,
                "support_measures": support_measures,
                "special_statuses": special_statuses,
                "districts": districts,
                "organization_types": organization_types,
                "years": years
            }

            logger.info(f"Статистика получена: {total_companies} компаний")

            return statistics

        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            raise


# Пример использования
if __name__ == "__main__":
    import asyncio

    async def main():
        # Создаем эмулятор парсера
        parser = ParserEmulator()

        print("=== Эмуляция парсинга компаний ===")

        # Получаем все компании
        companies = await parser.parse_companies()
        print(f"Загружено {len(companies)} компаний")

        if companies:
            print(f"Первая компания: {companies[0].get('Наименование организации', 'Неизвестно')}")
            print(f"ИНН первой компании: {companies[0].get('ИНН', 'Неизвестно')}")

        # Получаем статистику
        print("\n=== Статистика ===")
        stats = await parser.get_statistics()
        print(f"Всего компаний: {stats['total_companies']}")
        print(f"Отраслей: {len(stats['industries'])}")
        print(f"Размеров компаний: {len(stats['company_sizes'])}")

        # Поиск по отрасли
        print("\n=== Поиск по отрасли ===")
        if companies:
            first_industry = companies[0].get("Основная отрасль", "IT")
            industry_companies = await parser.get_companies_by_industry(first_industry)
            print(f"Компаний в отрасли '{first_industry}': {len(industry_companies)}")

        # Поиск по ИНН
        print("\n=== Поиск по ИНН ===")
        if companies:
            first_inn = companies[0].get("ИНН")
            if first_inn:
                company = await parser.get_company_by_inn(str(first_inn))
                if company:
                    print(f"Найдена компания: {company.get('Наименование организации', 'Неизвестно')}")
                else:
                    print("Компания не найдена")

    # Запуск примера
    asyncio.run(main())
