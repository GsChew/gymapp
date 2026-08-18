from fastapi import APIRouter, Depends
from loguru import logger

from src.auth.dependencies import get_current_user
from src.database import SessionDep
from src.models.user import User
from src.progress.service import (
    get_exercise_record as get_exercise_record_service,
    get_exercise_history as get_exercise_history_service,
    get_progress_summary as get_progress_summary_service,
    get_weekly_volume as get_weekly_volume_service,
)
from src.schemas.progress import SExerciseHistoryItem, SExerciseRecord, SProgressSummary, SWeeklyVolume

router = APIRouter(prefix="/progress", tags=["Progress"])


@router.get("/summary", response_model=SProgressSummary)
async def get_progress_summary(
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    """Return aggregate progress metrics for a user."""
    logger.info("Progress summary requested user_id={}", user.id)
    return await get_progress_summary_service(session=session, user_id=user.id)


@router.get("/weekly-volume", response_model=list[SWeeklyVolume])
async def get_weekly_volume(
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    """Return completed training volume grouped by week."""
    logger.info("Weekly volume requested user_id={}", user.id)
    return await get_weekly_volume_service(session=session, user_id=user.id)


@router.get("/exercises/{exercise_id}", response_model=SExerciseRecord)
async def get_exercise_record(
    exercise_id: int,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    """Return personal records for one exercise."""
    logger.info(
        "Exercise record requested user_id={} exercise_id={}",
        user.id,
        exercise_id,
    )
    return await get_exercise_record_service(
        session=session,
        user_id=user.id,
        exercise_id=exercise_id,
    )


@router.get("/exercises/{exercise_id}/history", response_model=list[SExerciseHistoryItem])
async def get_exercise_history(
    exercise_id: int,
    session: SessionDep,
    user: User = Depends(get_current_user),
):
    """Return completed history entries for an exercise."""
    logger.info(
        "Exercise history requested user_id={} exercise_id={}",
        user.id,
        exercise_id,
    )
    return await get_exercise_history_service(
        session=session,
        user_id=user.id,
        exercise_id=exercise_id,
    )
