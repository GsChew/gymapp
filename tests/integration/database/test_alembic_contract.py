from alembic.config import Config
from alembic.script import ScriptDirectory
import pytest


pytestmark = [pytest.mark.integration, pytest.mark.database]


def test_alembic_has_one_expected_head() -> None:
    scripts = ScriptDirectory.from_config(Config("alembic.ini"))

    assert scripts.get_heads() == ["b7f4c1d9a2e8"]
    assert scripts.get_current_head() == "b7f4c1d9a2e8"


def test_alembic_revision_chain_contains_initial_and_merge() -> None:
    scripts = ScriptDirectory.from_config(Config("alembic.ini"))
    revision_ids = {revision.revision for revision in scripts.walk_revisions()}

    assert "a6c9bfa7d195" in revision_ids
    assert "0127b15b7f74" in revision_ids
    assert "b7f4c1d9a2e8" in revision_ids
