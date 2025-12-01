"""
Dependency Injector container for advanced DI patterns.

This module demonstrates using the dependency-injector library
for more sophisticated dependency management with configuration
loading and provider types.
"""

import os
from typing import Annotated

from dependency_injector import containers, providers
from fastapi import Depends

from app.dependencies.pagination import (
    ConfigurablePaginationHelper,
    PaginationHelper,
    PaginationSettings,
)


class ApplicationContainer(containers.DeclarativeContainer):
    """
    Application container using dependency-injector.

    Demonstrates:
    - Configuration providers with YAML loading
    - Singleton providers for stateless services
    - Factory providers for configurable services
    """

    config = providers.Configuration()

    pagination_helper = providers.Singleton(PaginationHelper)

    pagination_settings = providers.Factory(
        PaginationSettings,
        include_page_info=config.pagination.include_page_info.as_(
            bool
        ),
        include_total_count=config.pagination.include_total_count.as_(
            bool
        ),
        default_page_size=config.pagination.default_page_size.as_(
            int
        ),
        max_page_size=config.pagination.max_page_size.as_(int),
    )

    configurable_pagination_helper = providers.Factory(
        ConfigurablePaginationHelper,
        settings=pagination_settings,
    )


def create_container() -> ApplicationContainer:
    """
    Create and configure the application container.

    Loads configuration from YAML files based on environment.
    """
    container = ApplicationContainer()

    environment = os.getenv("ENVIRONMENT", "development")
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "config",
        f"{environment}.yaml",
    )

    if os.path.exists(config_path):
        container.config.from_yaml(config_path)

    container.config.pagination.sitters_page_size.from_env(
        "SITTERS_PAGE_SIZE",
        default=20,
    )
    container.config.pagination.parents_page_size.from_env(
        "PARENTS_PAGE_SIZE",
        default=15,
    )

    return container


container = create_container()


def get_container_pagination_helper() -> PaginationHelper:
    """Get pagination helper from container."""
    return container.pagination_helper()


def get_container_configurable_pagination() -> (
    ConfigurablePaginationHelper
):
    """Get configurable pagination helper from container."""
    return container.configurable_pagination_helper()


ContainerPaginationDep = Annotated[
    PaginationHelper,
    Depends(get_container_pagination_helper),
]

ContainerConfigurablePaginationDep = Annotated[
    ConfigurablePaginationHelper,
    Depends(get_container_configurable_pagination),
]
