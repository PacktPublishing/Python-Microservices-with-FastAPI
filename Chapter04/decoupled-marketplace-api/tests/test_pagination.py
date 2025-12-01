from app.dependencies.pagination import (
    ConfigurablePaginationHelper,
    PaginationHelper,
    PaginationParams,
    PaginationSettings,
)


class TestPaginationHelper:
    """Tests for PaginationHelper class."""

    def test_calculate_skip_first_page(self):
        helper = PaginationHelper()
        assert helper.calculate_skip(page=1, page_size=20) == 0

    def test_calculate_skip_second_page(self):
        helper = PaginationHelper()
        assert helper.calculate_skip(page=2, page_size=20) == 20

    def test_calculate_skip_large_page(self):
        helper = PaginationHelper()
        assert helper.calculate_skip(page=10, page_size=25) == 225

    def test_calculate_total_pages_exact_division(self):
        helper = PaginationHelper()
        assert helper.calculate_total_pages(100, 20) == 5

    def test_calculate_total_pages_with_remainder(self):
        helper = PaginationHelper()
        assert helper.calculate_total_pages(101, 20) == 6

    def test_calculate_total_pages_single_page(self):
        helper = PaginationHelper()
        assert helper.calculate_total_pages(15, 20) == 1

    def test_paginate_items_first_page(self):
        helper = PaginationHelper()
        items = list(range(100))

        result = helper.paginate_items(
            items, page=1, page_size=20
        )

        assert result["data"] == list(range(20))
        assert result["current_page"] == 1
        assert result["page_size"] == 20
        assert result["total_pages"] == 5
        assert result["total_items"] == 100

    def test_paginate_items_last_page_partial(self):
        helper = PaginationHelper()
        items = list(range(95))

        result = helper.paginate_items(
            items, page=5, page_size=20
        )

        assert result["data"] == list(range(80, 95))
        assert result["page_size"] == 15
        assert result["total_pages"] == 5

    def test_paginate_items_empty_list(self):
        helper = PaginationHelper()
        items = []

        result = helper.paginate_items(
            items, page=1, page_size=20
        )

        assert result["data"] == []
        assert result["total_items"] == 0
        assert result["total_pages"] == 0


class TestPaginationParams:
    """Tests for PaginationParams class-based dependency."""

    def test_default_values(self):
        params = PaginationParams()
        assert params.page == 1
        assert params.size == 10
        assert params.skip == 0
        assert params.limit == 10

    def test_custom_values(self):
        params = PaginationParams(page=3, size=25)
        assert params.page == 3
        assert params.size == 25
        assert params.skip == 50
        assert params.limit == 25

    def test_page_minimum_enforced(self):
        params = PaginationParams(page=0, size=10)
        assert params.page == 1

    def test_page_negative_enforced(self):
        params = PaginationParams(page=-5, size=10)
        assert params.page == 1

    def test_size_maximum_enforced(self):
        params = PaginationParams(page=1, size=200)
        assert params.size == 100

    def test_size_minimum_enforced(self):
        params = PaginationParams(page=1, size=0)
        assert params.size == 1


class TestPaginationSettings:
    """Tests for PaginationSettings configuration."""

    def test_default_settings(self):
        settings = PaginationSettings()
        assert settings.include_page_info is True
        assert settings.include_total_count is True
        assert settings.default_page_size == 20
        assert settings.max_page_size == 100

    def test_custom_settings(self):
        settings = PaginationSettings(
            include_page_info=False,
            include_total_count=False,
            default_page_size=10,
            max_page_size=50,
        )
        assert settings.include_page_info is False
        assert settings.include_total_count is False
        assert settings.default_page_size == 10
        assert settings.max_page_size == 50


class TestConfigurablePaginationHelper:
    """Tests for ConfigurablePaginationHelper."""

    def test_with_all_features_enabled(self):
        settings = PaginationSettings(
            include_page_info=True,
            include_total_count=True,
        )
        helper = ConfigurablePaginationHelper(settings)
        items = list(range(50))

        result = helper.paginate_items(
            items, page=1, page_size=20
        )

        assert "data" in result
        assert "current_page" in result
        assert "page_size" in result
        assert "total_pages" in result
        assert "total_items" in result

    def test_with_page_info_disabled(self):
        settings = PaginationSettings(
            include_page_info=False,
            include_total_count=True,
        )
        helper = ConfigurablePaginationHelper(settings)
        items = list(range(50))

        result = helper.paginate_items(
            items, page=1, page_size=20
        )

        assert "data" in result
        assert "current_page" not in result
        assert "page_size" not in result
        assert "total_pages" in result

    def test_with_total_count_disabled(self):
        settings = PaginationSettings(
            include_page_info=True,
            include_total_count=False,
        )
        helper = ConfigurablePaginationHelper(settings)
        items = list(range(50))

        result = helper.paginate_items(
            items, page=1, page_size=20
        )

        assert "data" in result
        assert "current_page" in result
        assert "total_pages" not in result
        assert "total_items" not in result

    def test_with_all_features_disabled(self):
        settings = PaginationSettings(
            include_page_info=False,
            include_total_count=False,
        )
        helper = ConfigurablePaginationHelper(settings)
        items = list(range(50))

        result = helper.paginate_items(
            items, page=1, page_size=20
        )

        assert result == {"data": list(range(20))}
