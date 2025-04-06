import kubernetes
import os
import pytest
import re
from copy import deepcopy
from pathlib import Path

from ocp_resources.namespace import Namespace

from ocp_resources.resource import get_client
from tests.utils import bash, get_crc_status


@pytest.fixture(scope="session")
def kubeconfig():
    assert not os.environ.get("KUBECONFIG"), "Please unset KUBECONFIG and only set CRC_PATH"


@pytest.fixture(scope="session")
def crc_dir(kubeconfig):
    crc_path = os.environ.get("CRC_PATH")
    assert crc_path, "Must set CRC_PATH in environment"
    return os.path.dirname(crc_path)


@pytest.fixture(scope="session")
def crc_status(crc_dir):
    crc_status_dict = get_crc_status(crc_dir=crc_dir)
    if not crc_status_dict["success"]:
        if crc_status_dict["error"] == "Machine does not exist. Use 'crc start' to create it":
            return_code, stdout, stderr = bash(command="./crc config get pull-secret-file", cwd=crc_dir, capture=True)
            assert not return_code, f"Error getting CRC config: {stderr}"
            if re.match(rb"^pull-secret-file : ", stdout):
                crc_status_dict["crcStatus"] = "Stopped"
            else:
                pytest.fail("CRC has not been fully configured. Please run 'crc start' to complete configuration.")
        else:
            pytest.fail(f"Invalid CRC Status: {crc_status_dict}")

    yield crc_status_dict


@pytest.fixture(scope="session")
def crc_cluster(crc_dir, crc_status):
    if crc_status["crcStatus"] == "Stopped":
        return_code, _, _ = bash(command="./crc start", cwd=crc_dir)
        assert not return_code, "Error starting CRC"

        os.environ["KUBECONFIG"] = os.path.join(Path.home(), ".crc/machines/crc/kubeconfig")
        yield
        return_code, _, _ = bash(command="./crc stop", cwd=crc_dir)
        assert not return_code, "Error stopping CRC"

        # TODO: Remove delete after https://issues.redhat.com/browse/CRC-1374 resolved
        return_code, _, _ = bash(command="./crc delete --force", cwd=crc_dir)
        assert not return_code, "Error deleting CRC instance"

    elif crc_status["crcStatus"] == "Running":
        yield
    else:
        pytest.fail(f"Invalid CRC status: {crc_status}")


@pytest.fixture(scope="session")
def running_crc_kubeconfig(crc_cluster):
    return os.path.join(Path.home(), ".kube/config")


@pytest.fixture(scope="session")
def crc_admin_client(running_crc_kubeconfig):
    return get_client(
        config_file=running_crc_kubeconfig,
        context="crc-admin",
    )


@pytest.fixture(scope="module")
def namespace(crc_admin_client):
    with Namespace(name="test-namespace", client=crc_admin_client) as ns:
        yield ns


@pytest.fixture(scope="module")
def scale_client_configuration(request):
    client_configuration = kubernetes.client.Configuration()
    client_configuration.connection_pool_maxsize = request.param["connection_pool_maxsize"]
    return client_configuration


@pytest.fixture(scope="module")
def crc_scale_admin_client(running_crc_kubeconfig, scale_client_configuration):
    return get_client(
        client_configuration=deepcopy(scale_client_configuration),
        config_file=running_crc_kubeconfig,
        context="crc-admin",
    )


@pytest.fixture(scope="module")
def crc_scale_developer_client(running_crc_kubeconfig, scale_client_configuration):
    return get_client(
        client_configuration=deepcopy(scale_client_configuration),
        config_file=running_crc_kubeconfig,
        context="crc-developer",
    )
