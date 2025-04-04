# openshift-python-scale-utilities

Pypi: [openshift-python-scale-utilities](https://pypi.org/project/openshift-python-scale-utilities/)

Utilities to assist in scaling [openshift-python-wrapper](https://github.com/RedHatQE/openshift-python-wrapper) resources

## ocp_scale_utilities.threaded

Utilizes [ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor)
to operate on many resources in parallel across multiple threads.


### Usage
```
from ocp_resources.virtual_machine import VirtualMachine
from ocp_scale_utilities.threaded.utils import (
    threaded_deploy_resources,
    threaded_delete_resources,
    threaded_wait_deleted_resources,
)
from ocp_scale_utilities.threaded.scale import ThreadedScaleResources

# Create iterable of VirtualMachine python objects to deploy
# Be sure to use deepcopy() when passing dicts to objects to avoid collisions
vms = [VirtualMachine(..., body=deepcopy(body))]

# Option A:

def funcA():
    threaded_deploy_resources(resources=vms)
    yield vms
    threaded_delete_resources(resources=vms)
    threaded_wait_deleted_resources(resources=vms)

# Option B:

def funcB():
    with ThreadedScaleResources(resources=vms, wait_for_status=VirtualMachine.Status.RUNNING):
        yield vms
```

## ocp_scale_utilities.monitoring

`MonitorResourceAPIServerRequests` provides a way to monitor a specific resource to determine if it is being actively used.  
This allows the ability to wait for resources to settle after a major scale action,
improving reliability, and increasing readability in prometheus data.

### Usage

```
from ocp_resources.virtual_machine import VirtualMachine
from ocp_scale_utilities.monitoring import MonitorResourceAPIServerRequests
from ocp_scale_utilities.threaded.scale import ThreadedScaleResources
from ocp_utilities.monitoring import Prometheus

monitor_api_requests = MonitorResourceAPIServerRequests(
    prometheus=Prometheus(...),
    resource_class=VirtualMachine,
    idle_requests_value=float(...),  # Based on apiserver_request_total metric
)

monitor_api_requests.wait_for_idle()
with ThreadedScaleResources(resources=vms):
    monitor_api_requests.wait_for_idle()
    yield vms
monitor_api_requests.wait_for_idle()

```

## Contributing

Please use pre-commit to check the code before commiting
```
pre-commit install
```
