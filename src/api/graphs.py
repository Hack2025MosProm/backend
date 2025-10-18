import logging
from datetime import datetime, timedelta, timezone
from logging.config import dictConfig
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from repositories import CompanyRepository
from models import User, Token, Company, Graph, GraphType, GraphCreate, GraphRead, UserCompanyLink
from database.database import db
from logging_config import LOGGING_CONFIG, ColoredFormatter
from settings import settings
from api.auth import get_current_user
from plotter.plotter import Plotter

# Setup logging
dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
root_logger = logging.getLogger()
for handler in root_logger.handlers:
    if type(handler) is logging.StreamHandler:
        handler.setFormatter(ColoredFormatter('%(levelname)s:     %(asctime)s %(name)s - %(message)s'))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

router = APIRouter(prefix="/graphs", tags=["graphs"])


def get_company_data_for_user(user: User, company_ids: List[int], session: Session) -> List[Dict[str, Any]]:
    """
    Получает данные компаний пользователя для генерации графиков
    """
    # Получаем компании пользователя из базы данных через сессию
    from sqlmodel import select
    statement = select(Company).join(UserCompanyLink).where(UserCompanyLink.user_id == user.id)
    user_companies = session.exec(statement).all()
    user_company_ids = {company.id for company in user_companies}

    # Проверяем, что все запрашиваемые компании принадлежат пользователю
    invalid_ids = set(company_ids) - user_company_ids

    if invalid_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"У вас нет доступа к компаниям с ID: {list(invalid_ids)}"
        )

    # Получаем данные компаний
    companies_data = []
    for company_id in company_ids:
        company = session.get(Company, company_id)
        if company:
            companies_data.append(company.json_data)

    if not companies_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Не найдены данные компаний"
        )

    return companies_data


def generate_graph_data(graph_type: GraphType, company_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Генерирует данные графика с помощью Plotter
    """
    try:
        plotter = Plotter(company_data)

        # Выбираем нужный метод в зависимости от типа графика
        method_map = {
            GraphType.treemap_prod: plotter.treemap_prod,
            GraphType.scatter_busy: plotter.scatter_busy,
            GraphType.norm_export: plotter.norm_export,
            GraphType.pie_prod: plotter.pie_prod,
            GraphType.area_ecology: plotter.area_ecology,
            GraphType.hist_energy: plotter.hist_energy,
            GraphType.table_invest: plotter.table_invest,
        }

        method = method_map.get(graph_type)
        if not method:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неподдерживаемый тип графика: {graph_type}"
            )

        fig = method()

        # Конвертируем фигуру в JSON с использованием PlotlyJSONEncoder
        import plotly.utils
        import json
        graph_json = json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))

        return graph_json

    except Exception as e:
        logger.error(f"Ошибка при генерации графика {graph_type}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации графика: {str(e)}"
        )


@router.post("/generate", response_model=GraphRead)
async def generate_graph(
    graph_request: GraphCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(db.get_session)
):
    """
    Генерирует график для указанных компаний пользователя
    """
    try:
        # Получаем данные компаний
        company_data = get_company_data_for_user(current_user, graph_request.company_ids, session)

        # Генерируем данные графика
        graph_data = generate_graph_data(graph_request.graph_type, company_data)

        # Сохраняем график в базу данных
        graph = Graph(
            graph_type=graph_request.graph_type,
            user_id=current_user.id,
            company_ids=graph_request.company_ids,
            graph_data=graph_data
        )

        session.add(graph)
        session.commit()
        session.refresh(graph)

        logger.info(f"График {graph_request.graph_type} создан для пользователя {current_user.id}")

        return GraphRead(
            id=graph.id,
            graph_type=graph.graph_type,
            user_id=graph.user_id,
            company_ids=graph.company_ids,
            graph_data=graph.graph_data,
            created_at=graph.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при создании графика: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )


@router.post("/generate-all", response_model=List[GraphRead])
async def generate_all_graphs(
    company_ids: List[int],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(db.get_session)
):
    """
    Генерирует все доступные типы графиков для указанных компаний пользователя
    """
    try:
        # Получаем данные компаний
        company_data = get_company_data_for_user(current_user, company_ids, session)

        generated_graphs = []

        # Генерируем все типы графиков
        for graph_type in GraphType:
            try:
                # Генерируем данные графика
                graph_data = generate_graph_data(graph_type, company_data)

                # Сохраняем график в базу данных
                graph = Graph(
                    graph_type=graph_type,
                    user_id=current_user.id,
                    company_ids=company_ids,
                    graph_data=graph_data
                )

                session.add(graph)
                session.commit()
                session.refresh(graph)

                generated_graphs.append(GraphRead(
                    id=graph.id,
                    graph_type=graph.graph_type,
                    user_id=graph.user_id,
                    company_ids=graph.company_ids,
                    graph_data=graph.graph_data,
                    created_at=graph.created_at
                ))

                logger.info(f"График {graph_type} создан для пользователя {current_user.id}")

            except Exception as e:
                logger.error(f"Ошибка при создании графика {graph_type}: {str(e)}")
                continue  # Продолжаем с другими графиками

        if not generated_graphs:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось создать ни одного графика"
            )

        logger.info(f"Создано {len(generated_graphs)} графиков для пользователя {current_user.id}")

        return generated_graphs

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при создании графиков: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )


@router.get("/", response_model=List[GraphRead])
async def get_user_graphs(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(db.get_session)
):
    """
    Получает все графики пользователя
    """
    try:
        statement = select(Graph).where(Graph.user_id == current_user.id).order_by(Graph.created_at.desc())
        graphs = session.exec(statement).all()

        return [
            GraphRead(
                id=graph.id,
                graph_type=graph.graph_type,
                user_id=graph.user_id,
                company_ids=graph.company_ids,
                graph_data=graph.graph_data,
                created_at=graph.created_at
            )
            for graph in graphs
        ]

    except Exception as e:
        logger.error(f"Ошибка при получении графиков пользователя: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении графиков"
        )


@router.get("/{graph_id}", response_model=GraphRead)
async def get_graph(
    graph_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(db.get_session)
):
    """
    Получает конкретный график пользователя по ID
    """
    try:
        statement = select(Graph).where(
            Graph.id == graph_id,
            Graph.user_id == current_user.id
        )
        graph = session.exec(statement).first()

        if not graph:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="График не найден"
            )

        return GraphRead(
            id=graph.id,
            graph_type=graph.graph_type,
            user_id=graph.user_id,
            company_ids=graph.company_ids,
            graph_data=graph.graph_data,
            created_at=graph.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении графика {graph_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении графика"
        )


@router.delete("/{graph_id}")
async def delete_graph(
    graph_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(db.get_session)
):
    """
    Удаляет график пользователя
    """
    try:
        statement = select(Graph).where(
            Graph.id == graph_id,
            Graph.user_id == current_user.id
        )
        graph = session.exec(statement).first()

        if not graph:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="График не найден"
            )

        session.delete(graph)
        session.commit()

        logger.info(f"График {graph_id} удален пользователем {current_user.id}")

        return {"message": "График успешно удален"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении графика {graph_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении графика"
        )
