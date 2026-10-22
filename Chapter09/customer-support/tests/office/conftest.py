import shutil
from pathlib import Path

import pytest


@pytest.fixture
def office_sources(
    source_dir: Path, tests_dir: Path
) -> list[str]:
    """Copy a two-page PDF and a Word file into the folder."""
    sources = ["faq/shipping.docx", "policies/refunds.pdf"]
    for source in sources:
        name = Path(source).name
        shutil.copy(
            tests_dir / "data" / name, source_dir / source
        )
    return sources


@pytest.fixture
def refund_query() -> str:
    """Question that the refund policy PDF answers."""
    return "How long does a refund take?"


@pytest.fixture
def refund_source() -> str:
    """Relative path of the refund policy PDF."""
    return "policies/refunds.pdf"


@pytest.fixture
def second_page_text() -> str:
    """Sentence that only appears on page two of the PDF."""
    return "Gift cards are never refunded."
