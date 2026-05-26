from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0127b15b7f74"
down_revision: Union[str, Sequence[str], None] = "86cb489c998d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


userrole_enum = postgresql.ENUM(
    "user",
    "trainer",
    "admin",
    name="userrole",
)


def upgrade() -> None:
    userrole_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "role",
            userrole_enum,
            nullable=False,
            server_default="user",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "role")

    userrole_enum.drop(op.get_bind(), checkfirst=True)