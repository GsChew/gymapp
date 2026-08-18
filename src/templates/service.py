from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.workout import WorkoutModel, WorkoutTemplate
from src.repository.templates import TemplateRepository
from src.schemas.workout import SWorkoutFromTemplate, SWorkoutTemplateCreate


async def get_templates(session: AsyncSession, user_id: int) -> list[WorkoutTemplate]:
    """Return workout templates owned by the current user."""
    logger.info("Getting templates user_id={}", user_id)
    try:
        return await TemplateRepository.get_templates(session=session, user_id=user_id)
    except SQLAlchemyError as error:
        logger.exception("Database error while getting templates user_id={}", user_id)
        raise ValueError("Не удалось получить шаблоны") from error


async def create_template(
    session: AsyncSession,
    user_id: int,
    data: SWorkoutTemplateCreate,
) -> WorkoutTemplate:
    """Create a reusable workout template."""
    logger.info("Creating template user_id={} title={}", user_id, data.title)
    try:
        return await TemplateRepository.create_template(
            session=session,
            user_id=user_id,
            data=data,
        )
    except SQLAlchemyError as error:
        await session.rollback()
        logger.exception("Database error while creating template user_id={}", user_id)
        raise ValueError("Не удалось создать шаблон") from error


async def create_workout_from_template(
    session: AsyncSession,
    user_id: int,
    template_id: int,
    data: SWorkoutFromTemplate,
) -> WorkoutModel:
    """Schedule a new workout using a template's exercises."""
    logger.info(
        "Creating workout from template user_id={} template_id={}",
        user_id,
        template_id,
    )
    try:
        template = await TemplateRepository.get_template(
            session=session,
            user_id=user_id,
            template_id=template_id,
            load_exercises=True,
        )
        if template is None:
            raise ValueError("Шаблон не найден")

        return await TemplateRepository.create_workout_from_template(
            session=session,
            user_id=user_id,
            template=template,
            data=data,
        )

    except ValueError:
        await session.rollback()
        raise
    except SQLAlchemyError as error:
        await session.rollback()
        logger.exception(
            "Database error while creating workout from template user_id={} template_id={}",
            user_id,
            template_id,
        )
        raise ValueError("Не удалось создать тренировку из шаблона") from error


async def delete_template(
    session: AsyncSession,
    user_id: int,
    template_id: int,
) -> WorkoutTemplate:
    """Delete a workout template owned by the current user."""
    logger.info("Deleting template user_id={} template_id={}", user_id, template_id)
    try:
        template = await TemplateRepository.delete_template(
            session=session,
            user_id=user_id,
            template_id=template_id,
        )
    except SQLAlchemyError as error:
        await session.rollback()
        logger.exception("Database error while deleting template user_id={} template_id={}", user_id, template_id)
        raise ValueError("Не удалось удалить шаблон") from error

    if template is None:
        raise ValueError("Шаблон не найден")
    return template
