import pytest
from ocp_resources.pod import Pod
from ocp_scale_utilities.threaded.scale import ThreadedScaleResources


@pytest.fixture(scope="class")
def pods_for_test(crc_admin_client, namespace):
    yield [
        Pod(
            name=f"test-pod-{index}",
            namespace=namespace.name,
            client=crc_admin_client,
            containers=[
                dict(
                    name="pause",
                    image="registry.k8s.io/pause:3.9",
                ),
            ],
        )
        for index in range(10)
    ]


@pytest.fixture()
def scaled_pods(pods_for_test):
    with ThreadedScaleResources(resources=pods_for_test, wait_for_status=Pod.Status.RUNNING):
        yield pods_for_test


@pytest.fixture(scope="class")
def created_scaled_pods(pods_for_test):
    with ThreadedScaleResources(
        resources=pods_for_test, wait_for_status=Pod.Status.RUNNING, flags=ThreadedScaleResources.Flags.CREATE
    ):
        ...
    yield pods_for_test


@pytest.fixture(scope="class")
def created_scaled_pods_with_cleanup_on_error(pods_for_test):
    with ThreadedScaleResources(
        resources=pods_for_test,
        wait_for_status=Pod.Status.RUNNING,
        flags=ThreadedScaleResources.Flags.CREATE | ThreadedScaleResources.Flags.CLEANUP_ON_ERROR,
    ):
        ...
    yield pods_for_test


@pytest.fixture(scope="class")
def deleted_scaled_pods(created_scaled_pods):
    with ThreadedScaleResources(resources=created_scaled_pods, flags=ThreadedScaleResources.Flags.DELETE):
        ...
    yield created_scaled_pods


@pytest.fixture(scope="class")
def deleted_scaled_pods_with_cleanup_on_error(created_scaled_pods):
    with ThreadedScaleResources(
        resources=created_scaled_pods,
        flags=ThreadedScaleResources.Flags.DELETE | ThreadedScaleResources.Flags.CLEANUP_ON_ERROR,
    ):
        ...
    yield created_scaled_pods


class TestThreadedScaleResourceFlags:
    def test_threaded_deploy_resources(self, scaled_pods):
        assert all([pod.exists and pod.status == Pod.Status.RUNNING for pod in scaled_pods])

    @pytest.mark.order(after="TestThreadedScaleResourceFlags::test_threaded_deploy_resources")
    def test_create_flag(self, created_scaled_pods):
        assert all([pod.exists and pod.status == Pod.Status.RUNNING for pod in created_scaled_pods])

    @pytest.mark.order(after="TestThreadedScaleResourceFlags::test_create_flag")
    def test_delete_flag(self, deleted_scaled_pods):
        assert all([not pod.exists for pod in deleted_scaled_pods])

    @pytest.mark.order(after="TestThreadedScaleResourceFlags::test_delete_flag")
    def test_create_flag_with_cleanup_on_error(self, created_scaled_pods_with_cleanup_on_error):
        assert all([
            pod.exists and pod.status == Pod.Status.RUNNING for pod in created_scaled_pods_with_cleanup_on_error
        ])

    @pytest.mark.order(after="TestThreadedScaleResourceFlags::test_create_flag_with_cleanup_on_error")
    def test_delete_flag_with_cleanup_on_error(self, deleted_scaled_pods_with_cleanup_on_error):
        assert all([not pod.exists for pod in deleted_scaled_pods_with_cleanup_on_error])
