from typing import Annotated

from fastapi import Depends


class PaginationSettings:
    """Configuration for pagination behavior."""

    def __init__(
        self,
        include_page_info: bool = True,
        include_total_count: bool = True,
        default_page_size: int = 20,
        max_page_size: int = 100,
    ):
        self.include_page_info = include_page_info
        self.include_total_count = include_total_count
        self.default_page_size = default_page_size
        self.max_page_size = max_page_size


class PaginationHelper:
    """Basic pagination helper with calculation methods."""

    def __init__(self):
        pass

    def calculate_skip(self, page: int, page_size: int) -> int:
        """Calculate how many items to skip for pagination."""
        return (page - 1) * page_size

    def calculate_total_pages(
        self, total_items: int, page_size: int
    ) -> int:
        """Calculate total number of pages."""
        return (total_items + page_size - 1) // page_size

    def paginate_items(
        self, items: list, page: int, page_size: int
    ) -> dict:
        """Apply pagination to a list of items."""
        skip = self.calculate_skip(page, page_size)

        paginated_items = items[skip : skip + page_size]
        total_items = len(items)
        total_pages = self.calculate_total_pages(
            total_items, page_size
        )
        actual_page_size = len(paginated_items)

        return {
            "data": paginated_items,
            "current_page": page,
            "page_size": actual_page_size,
            "total_pages": total_pages,
            "total_items": total_items,
        }


class PaginationParams:
    """Class-based dependency for pagination parameters."""

    def __init__(self, page: int = 1, size: int = 10):
        self.page = max(1, page)
        self.size = min(100, max(1, size))
        self.skip = (self.page - 1) * self.size
        self.limit = self.size


class ConfigurablePaginationHelper:
    """Pagination helper with configurable settings."""

    def __init__(self, settings: PaginationSettings):
        self.settings = settings

    def paginate_items(
        self, items: list, page: int, page_size: int
    ) -> dict:
        """Apply pagination with configurable features."""
        skip = (page - 1) * page_size
        paginated_items = items[skip : skip + page_size]

        result: dict = {"data": paginated_items}

        if self.settings.include_page_info:
            result["current_page"] = page
            result["page_size"] = len(paginated_items)

        if self.settings.include_total_count:
            total_items = len(items)
            partial_sum = total_items + page_size - 1
            total_pages = partial_sum // page_size
            result["total_pages"] = total_pages
            result["total_items"] = total_items

        return result


def get_pagination_settings() -> PaginationSettings:
    """Dependency that provides pagination settings."""
    return PaginationSettings()


def get_pagination_helper() -> PaginationHelper:
    """Dependency that provides pagination helper services."""
    return PaginationHelper()


def get_configurable_pagination_helper(
    settings: Annotated[
        PaginationSettings, Depends(get_pagination_settings)
    ],
) -> ConfigurablePaginationHelper:
    """Dependency with nested dependency on settings."""
    return ConfigurablePaginationHelper(settings)


PaginationDep = Annotated[
    PaginationHelper, Depends(get_pagination_helper)
]

ConfigurablePaginationDep = Annotated[
    ConfigurablePaginationHelper,
    Depends(get_configurable_pagination_helper),
]
