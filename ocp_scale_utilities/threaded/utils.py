from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from typing import Any, Optional

from ocp_resources.resource import Resource

from ocp_scale_utilities.constants import TIMEOUT_2MIN

LOGGER = logging.getLogger(__name__)


def threaded_clean_up_resources(resources: list[Resource]) -> list[Any]:
    """
    Call clean_up() for multiple resources via threads

    Args:
        resources (list): List of Resources

    Returns:
        list: Data related to the results of the threaded function
    """
    with ThreadPoolExecutor(max_workers=len(resources)) as executor:
        return list(executor.map(lambda x: x.clean_up(), resources))


def threaded_delete_resources(resources: list[Resource]) -> list[Any]:
    """
    Call delete() for multiple resources via threads

    Args:
        resources (list): List of Resources

    Returns:
        list: Data related to the results of the threaded function
    """
    with ThreadPoolExecutor(max_workers=len(resources)) as executor:
        return list(executor.map(lambda x: x.delete(), resources))


def threaded_wait_deleted_resources(resources: list[Resource]) -> list[Any]:
    """
    Call wait_deleted() for multiple resources via threads

    Args:
        resources (list): List of Resources

    Returns:
        list: Data related to the results of the threaded function
    """
    with ThreadPoolExecutor(max_workers=len(resources)) as executor:
        return list(executor.map(lambda x: x.wait_deleted(), resources))


def threaded_deploy_requested_resources(
    resources: list[Resource], request_resources: list[Resource], exit_stack: Optional[ExitStack] = None
) -> list[Any]:
    """
    Deploy multiple resources via threads

    Args:
        resources (list): List of Resources eg: Project
        request_resources (list): List of Request Resources eg: ProjectRequest
        exit_stack (ExitStack, optional): ExitStack if desired, will use enter_context to deploy Resources

    Returns:
        list: Data related to the results of the threaded function
    """

    def _deploy(_resource: tuple[Resource, Resource]) -> Any:
        _request_resource, _managed_resource = _resource
        if exit_stack:
            _request_resource.deploy()
            exit_stack.push(exit=_managed_resource.__exit__)
        else:
            return _request_resource.deploy()

    with ThreadPoolExecutor(max_workers=len(resources)) as executor:
        return list(executor.map(_deploy, zip(request_resources, resources)))


def threaded_deploy_resources(resources: list[Resource], exit_stack: Optional[ExitStack] = None) -> list[Any]:
    """
    Deploy multiple resources via threads

    Args:
        resources (list): List of Resources
        exit_stack (ExitStack, optional): ExitStack if desired, will use enter_context to deploy Resources

    Returns:
        list: Data related to the results of the threaded function
    """

    def _deploy(_resource: Resource) -> Any:
        if exit_stack:
            exit_stack.enter_context(cm=_resource)
        else:
            return _resource.deploy()

    with ThreadPoolExecutor(max_workers=len(resources)) as executor:
        return list(executor.map(_deploy, resources))


def threaded_wait_for_resources_status(
    resources: list[Resource], status: Resource.Status, timeout: int = TIMEOUT_2MIN
) -> list[Any]:
    """
    Wait for multiple resources to to reach status via threads

    Args:
        resources (list): List of Resources
        status: (Resource.Status): Status to wait for
        timeout: (int): Length of time for each thread to wait for resource to reach status

    Returns:
        list: Data related to the results of the threaded function
    """
    with ThreadPoolExecutor(max_workers=len(resources)) as executor:
        return list(executor.map(lambda x: x.wait_for_status(status=status, timeout=timeout), resources))
