from fastapi import APIRouter, Query

from app.dependencies import PaginationDep

router = APIRouter(prefix="/parents", tags=["parents"])

MOCK_PARENTS = [
    {
        "id": i,
        "name": f"Parent {i}",
        "children_count": (i % 4) + 1,
    }
    for i in range(1, 5001)
]


@router.get("/")
async def get_parents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        15, ge=1, le=50, description="Items per page"
    ),
    pagination: PaginationDep = None,
) -> dict:
    """
    Get paginated list of parents.

    Uses PaginationHelper dependency to handle pagination logic,
    demonstrating how the same dependency can be reused across
    different endpoints.
    """
    return pagination.paginate_items(
        MOCK_PARENTS, page, page_size
    )


@router.get("/{parent_id}")
async def get_parent(parent_id: int) -> dict:
    """Get a specific parent by ID."""
    for parent in MOCK_PARENTS:
        if parent["id"] == parent_id:
            return parent
    return {"error": "Parent not found"}
