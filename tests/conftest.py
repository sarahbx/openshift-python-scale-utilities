import json
import logging
import os
import pytest
import re
from pathlib import Path

from ocp_resources.namespace import Namespace
from ocp_resources.resource import get_client
from tests.utils import bash


LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def kubeconfig():
    return os.environ.get("KUBECONFIG")


@pytest.fixture(scope="session")
def crc_dir():
    crc_path = os.environ.get("CRC_PATH", "")
    return os.path.dirname(crc_path)


@pytest.fixture(scope="session")
def crc_status(kubeconfig, crc_dir):
    if kubeconfig:
        yield
    else:
        return_code, stdout, stderr = bash(command="./crc status -o json", cwd=crc_dir, capture=True)
        assert not return_code, f"Error getting CRC status: {stderr}"

        crc_status_dict = json.loads(stdout)
        if not crc_status_dict["success"]:
            if crc_status_dict["error"] == "Machine does not exist. Use 'crc start' to create it":
                return_code, stdout, stderr = bash(
                    command="./crc config get pull-secret-file", cwd=crc_dir, capture=True
                )
                assert not return_code, f"Error getting CRC status: {stderr}"
                if re.match(rb"^pull-secret-file : ", stdout):
                    crc_status_dict["crcStatus"] = "Stopped"
                else:
                    pytest.fail("CRC has not been fully configured. Please run 'crc start' to complete configuration.")
            else:
                pytest.fail(f"Invalid CRC Status: {crc_status_dict}")

        yield crc_status_dict


@pytest.fixture(scope="session")
def crc_cluster(kubeconfig, crc_dir, crc_status):
    if kubeconfig:
        LOGGER.info("Skipping crc cluster setup, KUBECONFIG provided")
        yield
    else:
        if crc_status["crcStatus"] == "Stopped":
            return_code, _, _ = bash(command="./crc start", cwd=crc_dir)
            assert not return_code, "Error starting CRC"
            os.environ["KUBECONFIG"] = os.path.join(Path.home(), ".crc/machines/crc/kubeconfig")
        yield
        if crc_status["crcStatus"] == "Stopped":
            return_code, _, _ = bash(command="./crc stop", cwd=crc_dir)
            assert not return_code, "Error stopping CRC"
            # TODO: Remove delete after https://issues.redhat.com/browse/CRC-1374 resolved
            return_code, _, _ = bash(command="./crc delete --force", cwd=crc_dir)
            assert not return_code, "Error deleting CRC instance"


@pytest.fixture(scope="session")
def admin_client(crc_cluster):
    return get_client()


@pytest.fixture()
def namespace(admin_client):
    with Namespace(name="test-namespace", client=admin_client) as ns:
        yield ns
