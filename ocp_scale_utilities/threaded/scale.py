from __future__ import annotations

import time
from contextlib import ExitStack, contextmanager
from typing import Any, Optional

import pytest
from ocp_resources.resource import Resource

from ocp_scale_utilities.threaded.utils import (
    threaded_delete_resources,
    threaded_deploy_requested_resources,
    threaded_deploy_resources,
    threaded_wait_deleted_resources,
    threaded_wait_for_resources_status,
)


class ThreadedScaleResources(ExitStack):
    def __init__(
        self,
        resources: list[Resource],
        request_resources: Optional[list[Resource]] = None,
        pytest_cache: Optional[pytest.Cache] = None,
        cache_key_prefix: Optional[str] = None,
        wait_for_status: Optional[Resource.Status] = None,
    ):
        """
        Args:
            resources (list): List of Resource objects to be managed
            pytest_cache (pytest.Cache): config.cache from python run to store results in
            cache_key_prefix (str): prefix to use for cache_keys
            wait_for_status (Resource.Status): Wait for provided status upon deploy
        """
        super().__init__()
        self.resources = resources
        self.request_resources = request_resources
        self.pytest_cache = pytest_cache
        self.cache_key_prefix = cache_key_prefix
        self.wait_for_status = wait_for_status

    @contextmanager
    def _cleanup_on_error(self, stack_exit):
        with ExitStack() as stack:
            stack.push(exit=stack_exit)
            yield
            stack.pop_all()

    def __enter__(self) -> ThreadedScaleResources:
        with self._cleanup_on_error(stack_exit=super().__exit__):
            start_time = time.time()
            if self.request_resources:
                threaded_deploy_requested_resources(
                    resources=self.resources, request_resources=self.request_resources, exit_stack=self
                )
            else:
                threaded_deploy_resources(resources=self.resources, exit_stack=self)

            if self.wait_for_status:
                threaded_wait_for_resources_status(resources=self.resources, status=self.wait_for_status)

            stop_time = time.time()
            if self.pytest_cache and self.cache_key_prefix:
                self.pytest_cache.set(f"{self.cache_key_prefix}-deploy-start", start_time)
                self.pytest_cache.set(f"{self.cache_key_prefix}-deploy-stop", stop_time)
                self.pytest_cache.set(f"{self.cache_key_prefix}-deploy-elapsed", stop_time - start_time)
        return self

    def __exit__(self: ThreadedScaleResources, *exc_arguments: Any) -> Any:
        """
        Delete all resources, mark the start and end fields.
        Deletion when exiting context manager will unwind ExitStack,
        including any sleeps between batches.
        Wait for resources to be deleted in reverse order of creation.
        """
        with self._cleanup_on_error(stack_exit=super().__exit__):
            start_time = time.time()
            threaded_delete_resources(resources=self.resources)
            threaded_wait_deleted_resources(resources=self.resources)
            stop_time = time.time()
            if self.pytest_cache and self.cache_key_prefix:
                self.pytest_cache.set(f"{self.cache_key_prefix}-delete-start", start_time)
                self.pytest_cache.set(f"{self.cache_key_prefix}-delete-stop", stop_time)
                self.pytest_cache.set(f"{self.cache_key_prefix}-delete-elapsed", stop_time - start_time)
