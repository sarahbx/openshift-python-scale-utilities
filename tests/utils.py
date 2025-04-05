from __future__ import annotations

import logging
import sys
import shlex
import subprocess
from typing import Any, Optional

LOGGER = logging.getLogger(__name__)


def bash(
    command: str,
    timeout: Optional[int] = None,
    cwd: Optional[str] = None,
    env: Optional[dict] = None,
    capture: bool = False,
) -> tuple[int, Any, Any]:
    LOGGER.info(f"Running: {command!r}")

    args = shlex.split(f"/usr/bin/env bash -e -c {shlex.quote(command)}")
    with subprocess.Popen(
        args=args,
        stdout=subprocess.PIPE if capture else sys.stdout,
        stderr=subprocess.PIPE if capture else sys.stderr,
        cwd=cwd,
        env=env,
    ) as proc:
        proc.wait(timeout=timeout)
        if capture:
            return proc.returncode, proc.stdout.read(), proc.stderr.read()
        else:
            return proc.returncode, None, None
