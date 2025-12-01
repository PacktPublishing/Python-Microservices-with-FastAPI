from fastapi import APIRouter, Query

from app.dependencies import (
    ConfigurablePaginationDep,
    PaginationDep,
)

router = APIRouter(prefix="/sitters", tags=["sitters"])

MOCK_SITTERS = [
    {
        "id": i,
        "name": f"Sitter {i}",
        "hourly_rate": 20 + (i % 10),
    }
    for i in range(1, 10001)
]


@router.get("/")
async def get_sitters(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        20, ge=1, le=100, description="Items per page"
    ),
    pagination: PaginationDep = None,
) -> dict:
    """
    Get paginated list of sitters.

    Uses PaginationHelper dependency to handle pagination logic.
    """
    return pagination.paginate_items(
        MOCK_SITTERS, page, page_size
    )


@router.get("/configurable")
async def get_sitters_configurable(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        20, ge=1, le=100, description="Items per page"
    ),
    pagination: ConfigurablePaginationDep = None,
) -> dict:
    """
    Get paginated list of sitters with configurable pagination.

    Uses ConfigurablePaginationHelper which depends on
    PaginationSettings, demonstrating nested dependencies.
    """
    return pagination.paginate_items(
        MOCK_SITTERS, page, page_size
    )


@router.get("/{sitter_id}")
async def get_sitter(sitter_id: int) -> dict:
    """Get a specific sitter by ID."""
    for sitter in MOCK_SITTERS:
        if sitter["id"] == sitter_id:
            return sitter
    return {"error": "Sitter not found"}
