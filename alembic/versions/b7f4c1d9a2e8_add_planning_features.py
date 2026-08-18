"""add planning features

Revision ID: b7f4c1d9a2e8
Revises: 86cb489c998d, c4d2a8e91f3b
Create Date: 2026-07-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b7f4c1d9a2e8"
down_revision: Union[str, Sequence[str], None] = (
    "86cb489c998d",
    "c4d2a8e91f3b",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE workout_status_types ADD VALUE IF NOT EXISTS 'missed'")
    op.execute("ALTER TYPE status_types ADD VALUE IF NOT EXISTS 'missed'")

    op.add_column("workouts", sa.Column("wellness_energy", sa.Integer(), nullable=True))
    op.add_column("workouts", sa.Column("wellness_sleep", sa.Integer(), nullable=True))
    op.add_column("workouts", sa.Column("wellness_soreness", sa.Integer(), nullable=True))
    op.add_column("workouts", sa.Column("completion_notes", sa.String(length=1000), nullable=True))

    goal_status = postgresql.ENUM(
        "active",
        "done",
        "archived",
        name="goal_status_types",
        create_type=False,
    )
    goal_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "workout_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workout_templates_user_id", "workout_templates", ["user_id"])

    op.create_table(
        "workout_template_exercises",
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("sets", sa.Integer(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("notes", sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"]),
        sa.ForeignKeyConstraint(["template_id"], ["workout_templates.id"]),
        sa.PrimaryKeyConstraint("template_id", "exercise_id"),
    )

    op.create_table(
        "user_goals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("metric", sa.String(length=80), nullable=False),
        sa.Column("target_value", sa.Float(), nullable=False),
        sa.Column("current_value", sa.Float(), nullable=False),
        sa.Column("status", goal_status, nullable=False),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_goals_user_id", "user_goals", ["user_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_user_goals_user_id", table_name="user_goals")
    op.drop_table("user_goals")
    op.drop_table("workout_template_exercises")
    op.drop_index("ix_workout_templates_user_id", table_name="workout_templates")
    op.drop_table("workout_templates")
    op.drop_column("workouts", "completion_notes")
    op.drop_column("workouts", "wellness_soreness")
    op.drop_column("workouts", "wellness_sleep")
    op.drop_column("workouts", "wellness_energy")
    sa.Enum(name="goal_status_types").drop(op.get_bind(), checkfirst=True)
