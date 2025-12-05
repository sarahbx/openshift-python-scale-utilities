from __future__ import annotations

import logging
import time
from contextlib import ExitStack, contextmanager
from enum import Flag, auto
from typing import Any, Optional, Sequence

import pytest
from ocp_resources.resource import Resource

from ocp_scale_utilities.threaded.utils import (
    threaded_delete_resources,
    threaded_deploy_requested_resources,
    threaded_deploy_resources,
    threaded_wait_deleted_resources,
    threaded_wait_for_resources_status,
)

LOGGER = logging.getLogger(__name__)


class ThreadedScaleResources(ExitStack):
    class Flags(Flag):
        CREATE = auto()
        DELETE = auto()
        CLEANUP_ON_ERROR = auto()

    def __init__(
        self,
        resources: Sequence[Resource],
        request_resources: Optional[Sequence[Resource]] = None,
        pytest_cache: Optional[pytest.Cache] = None,
        cache_key_prefix: Optional[str] = None,
        wait_for_status: Optional[str] = None,
        flags: Optional[Flags] = None,
    ):
        """
        Args:
            resources (Sequence): List of Resource objects to be managed
            pytest_cache (pytest.Cache): config.cache from python run to store results in
            cache_key_prefix (str): prefix to use for cache_keys
            wait_for_status (str): Wait for provided status upon deploy
            flags (Flags): Optional flags to direct behavior, eg: CREATE|DELETE|CLEANUP_ON_ERROR (default)
        """
        super().__init__()
        self.resources = resources
        self.request_resources = request_resources
        self.pytest_cache = pytest_cache
        self.cache_key_prefix = cache_key_prefix
        self.wait_for_status = wait_for_status

        if flags is None:
            self.flags = self.Flags.CREATE | self.Flags.DELETE | self.Flags.CLEANUP_ON_ERROR
        else:
            self.flags = flags

        self.collect_data_start_time = time.time()

    @contextmanager
    def _cleanup_on_error(self, stack_exit):
        if self.Flags.CLEANUP_ON_ERROR in self.flags:
            with ExitStack() as stack:
                stack.push(exit=stack_exit)
                yield
                self.collect_data(id="cleanup-on-error", start_time=self.collect_data_start_time)
                stack.pop_all()
        else:
            yield

    def __enter__(self) -> ThreadedScaleResources:
        if self.Flags.CREATE in self.flags:
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

                self.collect_data_start_time = stop_time = time.time()
                if self.pytest_cache and self.cache_key_prefix:
                    self.pytest_cache.set(f"{self.cache_key_prefix}-deploy-count", len(self.resources))
                    self.pytest_cache.set(f"{self.cache_key_prefix}-deploy-start", start_time)
                    self.pytest_cache.set(f"{self.cache_key_prefix}-deploy-stop", stop_time)
                    self.pytest_cache.set(f"{self.cache_key_prefix}-deploy-elapsed", stop_time - start_time)

                self.collect_data(id="post-enter", start_time=start_time)

        else:
            for resource in self.resources:
                self.push(resource.__exit__)

        return self

    def __exit__(self: ThreadedScaleResources, *exc_arguments: Any) -> Any:
        """
        Delete all resources, mark the start and end fields.
        Deletion when exiting context manager will unwind ExitStack,
        including any sleeps between batches.
        Wait for resources to be deleted in reverse order of creation.
        """
        if self.Flags.DELETE in self.flags:
            with self._cleanup_on_error(stack_exit=super().__exit__):
                self.collect_data(id="pre-exit", start_time=self.collect_data_start_time)
                start_time = time.time()
                threaded_delete_resources(resources=self.resources)
                threaded_wait_deleted_resources(resources=self.resources)
                stop_time = time.time()
                if self.pytest_cache and self.cache_key_prefix:
                    self.pytest_cache.set(f"{self.cache_key_prefix}-delete-start", start_time)
                    self.pytest_cache.set(f"{self.cache_key_prefix}-delete-stop", stop_time)
                    self.pytest_cache.set(f"{self.cache_key_prefix}-delete-elapsed", stop_time - start_time)

    def collect_data(self, id: str, start_time: float):
        # Placeholder to be defined by child classes for any data collection required
        #
        # Args:
        #    id (str): A string to be utilized to identify where the call occured
        #    start_time (float): Beginning time to collect data from
        LOGGER.warning("No data collected. collect_data() should be defined by child classes")
