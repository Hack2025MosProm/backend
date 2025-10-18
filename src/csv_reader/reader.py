import csv
import json
import logging
from logging.config import dictConfig
from pathlib import Path
from typing import List, Dict, Any, Optional

import aiofiles

try:
    from logging_config import LOGGING_CONFIG, ColoredFormatter

    dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(__name__)

    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if type(handler) is logging.StreamHandler:
            handler.setFormatter(ColoredFormatter('%(levelname)s:     %(asctime)s %(name)s - %(message)s'))
except ImportError:
    logger = logging.getLogger(__name__)

class AsyncCSVReader:
    def __init__(self, path: str, delimiter: str = ";"):
        logger.debug(f"Initialized AsyncCSVReader with path: {path} and delimiter: '{delimiter}'")
        self.path = path
        self.delimiter = delimiter

    def _clean_value(self, value: str) -> Any:
        """Очищает и конвертирует значения из CSV"""
        if not value or value.strip() == "":
            return None

        # Заменяем запятые на точки для числовых значений
        cleaned = value.replace(",", ".").strip()

        # Пытаемся конвертировать в число
        try:
            if "." in cleaned:
                return float(cleaned)
            else:
                return int(cleaned)
        except ValueError:
            return cleaned

    def _determine_company_size(self, row: Dict[str, Any]) -> str:
        """Определяет размер компании на основе выручки"""
        try:
            revenue = row.get("Выручка предприятия, тыс. руб")
            if revenue is None or revenue == "":
                return "Не указан"

            # Конвертируем в число
            if isinstance(revenue, str):
                revenue = float(revenue.replace(",", "."))
            elif isinstance(revenue, (int, float)):
                revenue = float(revenue)
            else:
                return "Не указан"

            # Классификация по выручке (в тысячах рублей)
            if revenue >= 2000000:  # 2 млрд рублей
                return "Крупное"
            elif revenue >= 800000:  # 800 млн рублей
                return "Среднее"
            else:
                return "Малое"

        except (ValueError, TypeError):
            return "Не указан"

    def _parse_support_measures(self, support_data: Any) -> bool:
        """Парсит данные о мерах поддержки в булево значение"""
        if support_data is None or support_data == "":
            return False

        # Проверяем, есть ли данные о поддержке
        support_str = str(support_data).lower().strip()
        if support_str in ["да", "есть", "получены", "оказаны", "true", "1"]:
            return True
        elif support_str in ["нет", "не получены", "не оказаны", "false", "0", ""]:
            return False
        else:
            # Если есть какой-то текст, считаем что поддержка есть
            return len(support_str) > 0

    def _parse_special_status(self, status_data: Any) -> str:
        """Парсит особый статус компании"""
        if status_data is None or status_data == "":
            return "Нет"

        status_str = str(status_data).strip()
        if status_str.lower() in ["сведения отсутствуют", "нет", "отсутствует", ""]:
            return "Нет"
        else:
            return status_str

    def _extract_key_fields(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Извлекает ключевые поля для базы данных"""
        return {
            "inn": row.get("ИНН"),
            "name": row.get("Наименование организации"),
            "full_name": row.get("Наименование организации"),  # Используем то же поле для полного названия
            "spark_status": "Действующая",  # Статус по умолчанию
            "main_industry": row.get("Основная отрасль"),
            "company_size_final": self._determine_company_size(row),  # Определяем размер по выручке
            "organization_type": row.get("Вид организации"),
            "support_measures": self._parse_support_measures(row.get("Данные об оказанных мерах поддержки")),
            "special_status": self._parse_special_status(row.get("Наличие особого статуса")),
            "year": row.get("Год"),
        }

    async def read_companies(self) -> List[Dict[str, Any]]:
        """
        Читает CSV файл с данными предприятий и возвращает список словарей с JSON данными
        """
        companies = []

        async with aiofiles.open(self.path, mode="r", encoding="utf-8") as f:
            logger.debug(f"Reading CSV file from path: {self.path}")
            content = await f.read()

        reader = csv.DictReader(content.splitlines(), delimiter=self.delimiter)

        for row_num, row in enumerate(reader, start=1):
            # Очищаем значения
            cleaned_row = {k: self._clean_value(v) for k, v in row.items()}

            # Добавляем номер записи
            cleaned_row["number"] = row_num

            companies.append(cleaned_row)

        logger.debug(f"Read {len(companies)} companies from CSV file")
        return companies

    async def read_companies_with_key_fields(self) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Читает CSV файл и возвращает:
        1. Полные JSON данные всех компаний
        2. Только ключевые поля для базы данных
        """
        companies = await self.read_companies()

        # Извлекаем ключевые поля для базы данных
        key_fields = [self._extract_key_fields(company) for company in companies]

        logger.debug(f"Extracted {len(key_fields)} key fields for database")
        return companies, key_fields

    async def write_companies(self, companies: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
        """
        Записывает данные компаний в CSV файл
        """
        if output_path is None:
            original_path = Path(self.path)
            output_path = str(original_path.with_name(original_path.stem + "_processed.csv"))

        if not companies:
            logger.warning("No companies to write")
            return output_path

        # Получаем все возможные поля из первой записи
        fieldnames = list(companies[0].keys())

        async with aiofiles.open(output_path, mode="w", encoding="utf-8", newline="") as f:
            # Записываем заголовки
            await f.write(self.delimiter.join(fieldnames) + "\n")

            # Записываем данные
            for company in companies:
                row_values = []
                for field in fieldnames:
                    value = company.get(field, "")
                    # Конвертируем в строку и экранируем если нужно
                    if value is None:
                        row_values.append("")
                    else:
                        row_values.append(str(value))

                await f.write(self.delimiter.join(row_values) + "\n")

        logger.debug(f"Wrote {len(companies)} companies to CSV file: {output_path}")
        return output_path

    async def get_company_by_inn(self, inn: str) -> Optional[Dict[str, Any]]:
        """
        Находит компанию по ИНН
        """
        companies = await self.read_companies()

        for company in companies:
            if company.get("ИНН") == inn:
                return company

        return None

    async def get_companies_by_industry(self, industry: str) -> List[Dict[str, Any]]:
        """
        Находит компании по отрасли
        """
        companies = await self.read_companies()

        return [company for company in companies
                if company.get("Основная отрасль") == industry]

    async def get_companies_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Находит компании по статусу
        """
        companies = await self.read_companies()

        return [company for company in companies
                if company.get("Статус ИТОГ") == status]


if __name__ == "__main__":
    import asyncio

    async def main():
        # Пример использования AsyncCSVReader
        reader = AsyncCSVReader("test_data.csv", delimiter=";")

        print("=== Пример 1: Чтение всех компаний ===")
        companies = await reader.read_companies()
        print(f"Загружено {len(companies)} компаний")

        if companies:
            print(f"Первая компания: {companies[0]['Наименование организации']}")
            print(f"ИНН первой компании: {companies[0]['ИНН']}")

            print("\n=== Первые 5 компаний в формате JSON ===")
            for i, company in enumerate(companies[:5], 1):
                print(f"\n--- Компания {i} ---")
                print(json.dumps(company, ensure_ascii=False, indent=2))

        print("\n=== Пример 2: Чтение с ключевыми полями ===")
        all_data, key_fields = await reader.read_companies_with_key_fields()
        print(f"Полных записей: {len(all_data)}")
        print(f"Ключевых полей: {len(key_fields)}")

        if key_fields:
            print(f"Пример ключевых полей: {key_fields[0]}")

            print("\n=== Первые 3 ключевых поля в формате JSON ===")
            for i, key_field in enumerate(key_fields[:3], 1):
                print(f"\n--- Ключевые поля компании {i} ---")
                print(json.dumps(key_field, ensure_ascii=False, indent=2))

        print("\n=== Пример 3: Поиск компании по ИНН ===")
        if companies:
            first_inn = companies[0]['ИНН']
            company = await reader.get_company_by_inn(first_inn)
            if company:
                print(f"Найдена компания: {company['Наименование организации']}")
                print("\n--- Найденная компания в формате JSON ---")
                print(json.dumps(company, ensure_ascii=False, indent=2))

        print("\n=== Пример 4: Фильтрация по отрасли ===")
        it_companies = await reader.get_companies_by_industry("IT")
        print(f"IT компаний: {len(it_companies)}")

        print("\n=== Пример 5: Фильтрация по подтверждению ===")
        confirmed_companies = [c for c in companies if c.get("Подтвержден") == "Подтвержден"]
        print(f"Подтвержденных компаний: {len(confirmed_companies)}")

        print("\n=== Пример 6: Анализ ключевых метрик ===")
        # Анализируем новые ключевые поля
        industries = {}
        company_sizes = {}
        support_measures = {}
        special_statuses = {}
        districts = {}
        organization_types = {}
        years = {}
        sub_industries = {}

        for company in companies:
            industry = company.get("Основная отрасль", "Не указана")
            sub_industry = company.get("Подотрасль (Основная)", "Не указана")
            company_size = reader._determine_company_size(company)
            support = company.get("Данные об оказанных мерах поддержки", "Не указано")
            special_status = company.get("Наличие особого статуса", "Не указан")
            district = company.get("Округ", "Не указан")
            org_type = company.get("Вид организации", "Не указан")
            year = company.get("Год", "Не указан")

            industries[industry] = industries.get(industry, 0) + 1
            sub_industries[sub_industry] = sub_industries.get(sub_industry, 0) + 1
            company_sizes[company_size] = company_sizes.get(company_size, 0) + 1
            support_measures[support] = support_measures.get(support, 0) + 1
            special_statuses[special_status] = special_statuses.get(special_status, 0) + 1
            districts[district] = districts.get(district, 0) + 1
            organization_types[org_type] = organization_types.get(org_type, 0) + 1
            years[year] = years.get(year, 0) + 1

        print("Распределение по отраслям:")
        for industry, count in sorted(industries.items(), key=lambda x: x[1], reverse=True):
            print(f"  {industry}: {count}")

        print("\nРаспределение по размерам предприятий:")
        for size, count in sorted(company_sizes.items(), key=lambda x: x[1], reverse=True):
            print(f"  {size}: {count}")

        print("\nРаспределение по мерам поддержки:")
        for support, count in sorted(support_measures.items(), key=lambda x: x[1], reverse=True):
            print(f"  {support}: {count}")

        print("\nРаспределение по особым статусам:")
        for status, count in sorted(special_statuses.items(), key=lambda x: x[1], reverse=True):
            print(f"  {status}: {count}")

        print("\nРаспределение по округам:")
        for district, count in sorted(districts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {district}: {count}")

        print("\nРаспределение по видам организаций:")
        for org_type, count in sorted(organization_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {org_type}: {count}")

        print("\nРаспределение по подотраслям:")
        for sub_industry, count in sorted(sub_industries.items(), key=lambda x: x[1], reverse=True):
            print(f"  {sub_industry}: {count}")

        print("\nРаспределение по годам:")
        for year, count in sorted(years.items(), key=lambda x: x[1], reverse=True):
            print(f"  {year}: {count}")

        print("\n=== Пример 7: Анализ компаний с поддержкой ===")
        companies_with_support = [c for c in companies if c.get("Данные об оказанных мерах поддержки") == "Да"]
        print(f"Компаний с мерами поддержки: {len(companies_with_support)}")

        if companies_with_support:
            print("Примеры компаний с поддержкой:")
            for i, company in enumerate(companies_with_support[:3], 1):
                print(f"  {i}. {company.get('Наименование организации')} (ИНН: {company.get('ИНН')})")

            print("\n=== Первые 2 компании с поддержкой в формате JSON ===")
            for i, company in enumerate(companies_with_support[:2], 1):
                print(f"\n--- Компания с поддержкой {i} ---")
                print(json.dumps(company, ensure_ascii=False, indent=2))

        print("\n=== Пример 8: Анализ особых статусов ===")
        companies_with_special_status = [c for c in companies if c.get("Наличие особого статуса") != "Сведения отсутствуют"]
        print(f"Компаний с особым статусом: {len(companies_with_special_status)}")

        if companies_with_special_status:
            print("Компании с особым статусом:")
            for i, company in enumerate(companies_with_special_status[:3], 1):
                print(f"  {i}. {company.get('Наименование организации')} (ИНН: {company.get('ИНН')}, Статус: {company.get('Наличие особого статуса')})")

        print("\n=== Пример 9: Анализ по выручке ===")
        # Анализируем выручку
        revenue_analysis = {
            "Крупные (>2 млрд)": 0,
            "Средние (800млн-2млрд)": 0,
            "Малые (<800млн)": 0,
            "Без данных": 0
        }

        for company in companies:
            revenue = company.get("Выручка предприятия, тыс. руб")
            if revenue and str(revenue).strip():
                try:
                    rev_value = float(str(revenue).replace(",", "."))
                    if rev_value >= 2000000:
                        revenue_analysis["Крупные (>2 млрд)"] += 1
                    elif rev_value >= 800000:
                        revenue_analysis["Средние (800млн-2млрд)"] += 1
                    else:
                        revenue_analysis["Малые (<800млн)"] += 1
                except (ValueError, TypeError):
                    revenue_analysis["Без данных"] += 1
            else:
                revenue_analysis["Без данных"] += 1

        print("Распределение по выручке:")
        for category, count in revenue_analysis.items():
            print(f"  {category}: {count}")

        print("\n=== Пример 10: Анализ по налогам ===")
        # Анализируем налоги
        tax_analysis = {
            "Высокие налоги (>50млн)": 0,
            "Средние налоги (10-50млн)": 0,
            "Низкие налоги (<10млн)": 0,
            "Без данных": 0
        }

        for company in companies:
            taxes = company.get("Налоги, уплаченные в бюджет Москвы (без акцизов), тыс.руб.")
            if taxes and str(taxes).strip():
                try:
                    tax_value = float(str(taxes).replace(",", "."))
                    if tax_value >= 50000:
                        tax_analysis["Высокие налоги (>50млн)"] += 1
                    elif tax_value >= 10000:
                        tax_analysis["Средние налоги (10-50млн)"] += 1
                    else:
                        tax_analysis["Низкие налоги (<10млн)"] += 1
                except (ValueError, TypeError):
                    tax_analysis["Без данных"] += 1
            else:
                tax_analysis["Без данных"] += 1

        print("Распределение по налогам:")
        for category, count in tax_analysis.items():
            print(f"  {category}: {count}")

        print("\n=== Пример 11: Анализ экспорта ===")
        # Анализируем экспорт
        export_companies = [c for c in companies if c.get("Наличие поставок продукции на экспорт") == "Да"]
        print(f"Компаний с экспортом: {len(export_companies)}")

        if export_companies:
            print("Примеры компаний с экспортом:")
            for i, company in enumerate(export_companies[:3], 1):
                export_volume = company.get("Объем экспорта (млн руб.) за предыдущий календарный год", "Не указан")
                print(f"  {i}. {company.get('Наименование организации')} (Экспорт: {export_volume} млн руб.)")

            print("\n=== Первая компания с экспортом в формате JSON ===")
            if export_companies:
                print("\n--- Компания с экспортом ---")
                print(json.dumps(export_companies[0], ensure_ascii=False, indent=2))

        print("\n=== Пример 12: Сохранение обработанных данных ===")
        # Фильтруем компании с поддержкой
        companies_with_support = [c for c in companies if c.get("Данные об оказанных мерах поддержки") == "Да"]

        if companies_with_support:
            output_path = await reader.write_companies(companies_with_support)
            print(f"Сохранено {len(companies_with_support)} компаний с поддержкой в файл: {output_path}")

        print("\n=== Пример 13: Комплексный анализ ключевых метрик ===")
        # Анализируем комбинации ключевых полей
        companies_with_support_count = len([c for c in companies if c.get("Данные об оказанных мерах поддержки") == "Да"])
        companies_with_special_status_count = len([c for c in companies if c.get("Наличие особого статуса") != "Сведения отсутствуют"])
        confirmed_companies_count = len([c for c in companies if c.get("Подтвержден") == "Подтвержден"])
        export_companies_count = len([c for c in companies if c.get("Наличие поставок продукции на экспорт") == "Да"])

        key_metrics_analysis = {
            "total_companies": len(companies),
            "companies_with_support": companies_with_support_count,
            "companies_with_special_status": companies_with_special_status_count,
            "confirmed_companies": confirmed_companies_count,
            "export_companies": export_companies_count,
            "large_companies": revenue_analysis["Крупные (>2 млрд)"],
            "medium_companies": revenue_analysis["Средние (800млн-2млрд)"],
            "small_companies": revenue_analysis["Малые (<800млн)"],
            "high_tax_companies": tax_analysis["Высокие налоги (>50млн)"],
        }

        print("Ключевые метрики:")
        for metric, value in key_metrics_analysis.items():
            print(f"  {metric}: {value}")

        # Процентное соотношение
        if key_metrics_analysis["total_companies"] > 0:
            support_percentage = (key_metrics_analysis["companies_with_support"] / key_metrics_analysis["total_companies"]) * 100
            special_percentage = (key_metrics_analysis["companies_with_special_status"] / key_metrics_analysis["total_companies"]) * 100
            confirmed_percentage = (key_metrics_analysis["confirmed_companies"] / key_metrics_analysis["total_companies"]) * 100
            export_percentage = (key_metrics_analysis["export_companies"] / key_metrics_analysis["total_companies"]) * 100

            print(f"\nПроцентное соотношение:")
            print(f"  Компаний с поддержкой: {support_percentage:.1f}%")
            print(f"  Компаний с особым статусом: {special_percentage:.1f}%")
            print(f"  Подтвержденных компаний: {confirmed_percentage:.1f}%")
            print(f"  Компаний с экспортом: {export_percentage:.1f}%")

    # Запуск примеров
    asyncio.run(main())
