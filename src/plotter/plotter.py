import base64
import json
import logging
from logging.config import dictConfig
from typing import Any, Dict, Union, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.utils import PlotlyJSONEncoder

from logging_config import LOGGING_CONFIG, ColoredFormatter

# Глобально запретить бинарные массивы в JSON
try:
    # В новых Plotly есть конфиг json-энджина
    pio.json.config.default_engine = "json"  # type: ignore[attr-defined]
except Exception:
    pass


dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
for h in logging.getLogger().handlers:
    if isinstance(h, logging.StreamHandler):
        h.setFormatter(
            ColoredFormatter("%(levelname)s:     %(asctime)s %(name)s - %(message)s")
        )

def _debug_trace_shapes(fig):
    spec = _fig_spec(fig)  # новый
    out = []
    for t in spec.get("data", []):
        ttype = t.get("type")
        if ttype == "pie":
            out.append({"type": ttype,
                        "labels": len(t.get("labels", [])),
                        "values": len(t.get("values", []))})
        else:
            out.append({"type": ttype,
                        "x": len(t.get("x", [])),
                        "y": len(t.get("y", []))})
    return out

def _unpack_bdata(obj):
    """Рекурсивно заменяет {"dtype": "...", "bdata": "..."} на обычные list"""
    if isinstance(obj, dict):
        # точное совпадение по ключам
        if set(obj.keys()) == {"dtype", "bdata"}:
            arr = np.frombuffer(base64.b64decode(obj["bdata"]), dtype=np.dtype(obj["dtype"]))
            return arr.tolist()
        return {k: _unpack_bdata(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_unpack_bdata(v) for v in obj]
    return obj

def _fig_spec(fig) -> dict:
    # 1) пробуем «правильный» движок, который обычно НЕ делает bdata
    s = pio.to_json(fig, engine="json", validate=True)
    spec = json.loads(s)
    # 2) на всякий случай распаковываем, если где-то всё же проскочило
    spec = _unpack_bdata(spec)
    return spec


def _trace_shapes(spec: dict):
    out = []
    for t in spec.get("data", []):
        ttype = t.get("type")
        if ttype == "pie":
            out.append({"type": ttype, "labels": len(t.get("labels", [])), "values": len(t.get("values", []))})
        else:
            out.append({"type": ttype, "x": len(t.get("x", [])), "y": len(t.get("y", []))})
    return out


class Plotter:
    def __init__(self, data_source: Union[str, Dict[str, Any], List[Dict[str, Any]]]):
        """
        Инициализация Plotter

        Args:
            data_source: путь к JSON файлу, словарь с данными или список словарей
        """
        if isinstance(data_source, str):
            # Если передан путь к файлу
            self.json_path = data_source
            self.df = pd.read_json(data_source)
        elif isinstance(data_source, (dict, list)):
            # Если передан словарь или список словарей
            self.json_path = None
            self.df = pd.DataFrame(data_source)
        else:
            raise ValueError("data_source должен быть строкой (путь к файлу), словарем или списком словарей")


    def treemap_prod(self) -> go.Figure:
        """
        Древовидная карта (сектор Производство)
        """
        df_sum = (
            self.df.groupby(["Основная отрасль", "Подотрасль (Основная)"], as_index=False)
            ["Выручка предприятия, тыс. руб"].sum()
        )

        fig = px.treemap(
            df_sum,
            path=["Основная отрасль", "Подотрасль (Основная)"],
            values="Выручка предприятия, тыс. руб",
            color="Основная отрасль",
            title="Древовидная карта: Выручка предприятий по отраслям и подотраслям"
        )
        return fig

    def scatter_busy(self) -> go.Figure:
        """
        Точечный график (сектор Занятость)
        """
        fig = px.scatter(
            self.df,
            x="Среднесписочная численность персонала, работающего в Москве, чел",
            y="Фонд оплаты труда сотрудников, работающих в Москве, тыс. руб.",
            size="Средняя з.п. сотрудников, работающих в Москве, тыс.руб.",
            color="Основная отрасль",
            hover_name="Наименование организации",
            hover_data={"Средняя з.п. сотрудников, работающих в Москве, тыс.руб.": ":,.0f"},
            title="Занятость: связь численности персонала и фонда оплаты труда",
            size_max=25
        )
        fig.update_layout(
            xaxis_title="Численность персонала, чел",
            yaxis_title="Фонд оплаты труда, тыс. руб."
        )
        return fig

    def norm_export(self) -> go.Figure:
        """
        Нормированные столбцы (сектор Экспорт)
        """
        df_group = (
            self.df.groupby("Основная отрасль", as_index=False)
            .agg({
                "Объем экспорта, тыс. руб.": "sum",
                "Объем экспорта (млн руб.) за предыдущий календарный год": "sum"
            })
        )
        df_group["Объем экспорта (млн руб.) за предыдущий календарный год"] *= 1000
        df_group["Сумма_обоих"] = (df_group["Объем экспорта, тыс. руб."] +
                                 df_group["Объем экспорта (млн руб.) за предыдущий календарный год"])
        df_group["Текущий год %"] = df_group["Объем экспорта, тыс. руб."] / df_group["Сумма_обоих"] * 100
        df_group["Прошлый год %"] = (df_group["Объем экспорта (млн руб.) за предыдущий календарный год"] /
                                   df_group["Сумма_обоих"] * 100)

        df_melted = df_group.melt(
            id_vars=["Основная отрасль", "Объем экспорта, тыс. руб.",
                     "Объем экспорта (млн руб.) за предыдущий календарный год"],
            value_vars=["Текущий год %", "Прошлый год %"],
            var_name="Год",
            value_name="Процент"
        )

        df_melted["Сумма"] = df_melted.apply(
            lambda row: row["Объем экспорта, тыс. руб."] if row["Год"] == "Текущий год %"
            else row["Объем экспорта (млн руб.) за предыдущий календарный год"], axis=1
        )

        fig = px.bar(
            df_melted,
            x="Основная отрасль",
            y="Процент",
            color="Год",
            text_auto=".1f",
            hover_data={"Сумма": ":,.0f", "Процент": ":.1f"},
            title="Экспорт: процентное соотношение текущего и предыдущего года по отраслям"
        )
        fig.update_layout(
            barmode="stack",
            yaxis=dict(title="Процент (%)", range=[0, 100]),
            xaxis_title="Основная отрасль"
        )
        return fig

    def pie_prod(self) -> go.Figure:
        """
        Круговая диаграмма (сектор Производство)
        Сортировка: по убыванию суммы налогов
        """
        df_pie = self.df.copy()
        df_pie["Сумма налогов"] = (
            df_pie["Акцизы, тыс. руб."] +
            df_pie["Налоги, уплаченные в бюджет Москвы (без акцизов), тыс.руб."]
        )

        df_group = (
            df_pie.groupby(["Основная отрасль", "Подотрасль (Основная)"], as_index=False)
            ["Сумма налогов"].sum()
            .sort_values("Сумма налогов", ascending=False)
        )

        category_order = df_group["Подотрасль (Основная)"].tolist()

        fig = px.pie(
            df_group,
            names="Подотрасль (Основная)",
            values="Сумма налогов",
            color="Основная отрасль",
            category_orders={"Подотрасль (Основная)": category_order},
            title="Производство: распределение налогов по подотраслям"
        )

        fig.update_traces(
            sort=False,
            textinfo="percent+label",
            hovertemplate="%{label}<br>Сумма: %{value:,.0f} тыс. руб."
        )

        return fig

    def area_ecology(self) -> go.Figure:
        """
        Диаграмма с областями (сектор Экология)
        """
        df_ecology = self.df.copy()
        df_ecology["Нагрузка, %"] = (
            (df_ecology["Транспортный налог, тыс.руб."] +
             df_ecology["Налог на землю, тыс.руб."] +
             df_ecology["Акцизы, тыс. руб."]) /
            df_ecology["Выручка предприятия, тыс. руб"] * 100
        )
        fig = px.area(
            df_ecology,
            x="Основная отрасль",
            y="Нагрузка, %",
            color="Год",
            title="Экология: налогово-ресурсная нагрузка по отраслям"
        )
        fig.update_layout(yaxis_title="Нагрузка, %", xaxis_title="Основная отрасль")

        return fig

    def hist_energy(self) -> go.Figure:
        """
        Гистограмма (сектор Энергопотребление)
        Сортировка: сначала по отрасли, затем по уровню загрузки по возрастанию
        """
        df_hist = (
            self.df.groupby(["Наименование организации", "Основная отрасль"], as_index=False)
            ["Уровень загрузки производственных мощностей"].mean()
            .sort_values(["Основная отрасль", "Уровень загрузки производственных мощностей"],
                        ascending=[True, True])
        )

        category_order = df_hist["Наименование организации"].tolist()

        fig = px.bar(
            df_hist,
            x="Наименование организации",
            y="Уровень загрузки производственных мощностей",
            color="Основная отрасль",
            title="Энергопотребление: уровень загрузки производственных мощностей"
        )

        fig.update_layout(
            xaxis_title="Организация",
            yaxis_title="Средний уровень загрузки (%)",
            xaxis={'categoryorder': 'array', 'categoryarray': category_order}
        )

        return fig

    def table_invest(self) -> go.Figure:
        """
        Сводная таблица (сектор Инвестиции)
        """
        # Исправляем названия колонок для группировки
        df_table = (
            self.df.groupby(["Наименование организации", "Год"], as_index=False)
            .agg({
                "Выручка предприятия, тыс. руб": "sum",
                "Чистая прибыль (убыток),тыс. руб.": "sum",
                "Инвестиции в Мск  тыс. руб.": "sum"
            })
            .round(0)
            .sort_values(["Наименование организации", "Год"])
        )

        organizations = []
        years = []
        revenues = []
        profits = []
        investments = []

        fill_colors = []
        color_index = 0

        for org_name, group in df_table.groupby("Наименование организации"):
            org_rows = len(group)
            organizations.extend([org_name] + [""] * (org_rows - 1))

            years.extend(group["Год"].tolist())
            revenues.extend(group["Выручка предприятия, тыс. руб"].tolist())
            profits.extend(group["Чистая прибыль (убыток),тыс. руб."].tolist())
            investments.extend(group["Инвестиции в Мск  тыс. руб."].tolist())

            color = 'white' if color_index % 2 == 0 else 'lightgrey'
            fill_colors.extend([color] * org_rows)
            color_index += 1

        fig = go.Figure(
            data=[
                go.Table(
                    columnorder=[1, 2, 3, 4, 5],
                    columnwidth=[200, 80, 120, 120, 120],
                    header=dict(
                        values=[
                            "Наименование организации",
                            "Год",
                            "Выручка предприятия, тыс. руб",
                            "Чистая прибыль (убыток), тыс. руб.",
                            "Инвестиции в Мск  тыс. руб."
                        ],
                        fill_color="lightgrey",
                        align="center",
                        font=dict(size=12, color="black"),
                        line_color='grey'
                    ),
                    cells=dict(
                        values=[
                            organizations,
                            years,
                            revenues,
                            profits,
                            investments
                        ],
                        align="center",
                        fill_color=[fill_colors] * 5,
                        line_color='grey',
                        height=30
                    )
                )
            ]
        )

        fig.update_layout(
            title="Инвестиции: сводная таблица по организациям и годам",
            height=600
        )

        return fig