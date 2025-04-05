import pytest
from ocp_resources.pod import Pod
from ocp_scale_utilities.threaded.scale import ThreadedScaleResources


@pytest.fixture()
def scaled_pods(admin_client, namespace):
    pods = [
        Pod(
            name=f"test-pod-{index}",
            namespace=namespace.name,
            client=admin_client,
            containers=[
                dict(
                    name="pause",
                    image="registry.k8s.io/pause:3.9",
                ),
            ],
        )
        for index in range(10)
    ]
    with ThreadedScaleResources(resources=pods, wait_for_status=Pod.Status.RUNNING):
        yield pods


def test_threaded_deploy_resources(scaled_pods):
    assert all([pod.exists and pod.status == Pod.Status.RUNNING for pod in scaled_pods])
