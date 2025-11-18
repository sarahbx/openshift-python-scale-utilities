import pytest
import multiprocessing

from ocp_resources.namespace import Namespace
from ocp_resources.pod import Pod
from ocp_resources.project_request import ProjectRequest
from ocp_resources.project_project_openshift_io import Project
from ocp_scale_utilities.threaded.utils import (
    threaded_deploy_resources,
    threaded_delete_resources,
    threaded_clean_up_resources,
    threaded_wait_for_resources_status,
    threaded_wait_deleted_resources,
    threaded_deploy_requested_resources,
)


SCALE_RESOURCE_COUNT = 10
DEFAULT_CONNECTION_POOL_MAXSIZE = multiprocessing.cpu_count() * 5


pytestmark = [
    pytest.mark.usefixtures(
        "scale_client_configuration",
        "crc_scale_admin_client",
        "crc_scale_developer_client",
    ),
    pytest.mark.parametrize(
        "scale_client_configuration",
        [
            pytest.param(
                {"connection_pool_maxsize": max(SCALE_RESOURCE_COUNT, DEFAULT_CONNECTION_POOL_MAXSIZE)},
            ),
        ],
        indirect=True,
    ),
]


@pytest.fixture(scope="class")
def utils_test_namespace(crc_admin_client):
    with Namespace(name="test-utils-namespace", client=crc_admin_client) as ns:
        yield ns


@pytest.fixture(scope="class")
def deployed_pods(crc_scale_admin_client, utils_test_namespace):
    pods = [
        Pod(
            name=f"test-pod-{index}",
            namespace=utils_test_namespace.name,
            client=crc_scale_admin_client,
            containers=[
                dict(
                    name="pause",
                    image="registry.k8s.io/pause:3.9",
                ),
            ],
        )
        for index in range(SCALE_RESOURCE_COUNT)
    ]
    threaded_deploy_resources(resources=pods)
    yield pods


@pytest.fixture(scope="class")
def running_pods(deployed_pods):
    threaded_wait_for_resources_status(resources=deployed_pods, status=Pod.Status.RUNNING)
    yield deployed_pods


@pytest.fixture(scope="class")
def deleted_pods(deployed_pods):
    threaded_delete_resources(resources=deployed_pods)
    threaded_wait_deleted_resources(resources=deployed_pods)
    yield deployed_pods


@pytest.fixture(scope="class")
def cleaned_up_pods(deployed_pods):
    threaded_clean_up_resources(resources=deployed_pods)
    threaded_wait_deleted_resources(resources=deployed_pods)
    yield deployed_pods


@pytest.fixture()
def created_projects(crc_scale_developer_client):
    project_requests = []
    projects = []
    scale_namespace_prefix = "test-scale-projects"

    for index in range(SCALE_RESOURCE_COUNT):
        name = f"{scale_namespace_prefix}-{index}"
        project_requests.append(
            ProjectRequest(
                name=name,
                client=crc_scale_developer_client,
            ),
        )
        projects.append(
            Project(
                name=name,
                client=crc_scale_developer_client,
            )
        )

    threaded_deploy_requested_resources(resources=projects, request_resources=project_requests)
    threaded_wait_for_resources_status(resources=projects, status=Project.Status.ACTIVE)
    yield projects
    threaded_delete_resources(resources=projects)
    threaded_wait_deleted_resources(resources=projects)


@pytest.mark.usefixtures("utils_test_namespace")
class TestThreadedUtilsDelete:
    def test_threaded_deploy_resources(self, deployed_pods):
        assert all([pod.exists for pod in deployed_pods])

    @pytest.mark.order(after="TestThreadedUtilsDelete::test_threaded_deploy_resources")
    def test_threaded_wait_for_resources_status(self, running_pods):
        assert all([pod.status == Pod.Status.RUNNING for pod in running_pods])

    @pytest.mark.order(after="TestThreadedUtilsDelete::test_threaded_wait_for_resources_status")
    def test_threaded_delete_resources(self, deleted_pods):
        assert all([not pod.exists for pod in deleted_pods])


@pytest.mark.usefixtures("utils_test_namespace")
class TestThreadedUtilsCleanUp:
    def test_threaded_wait_for_resources_status(self, running_pods):
        assert all([pod.exists and pod.status == Pod.Status.RUNNING for pod in running_pods])

    @pytest.mark.order(after="TestThreadedUtilsCleanUp::test_threaded_wait_for_resources_status")
    def test_threaded_clean_up_resources(self, cleaned_up_pods):
        assert all([not pod.exists for pod in cleaned_up_pods])


def test_threaded_wait_for_resources_status(created_projects):
    assert all([project.exists and project.status == Project.Status.ACTIVE for project in created_projects])
