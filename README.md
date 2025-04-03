# openshift-python-scale-utilities

WIP

## ocp_scale_utilities.threaded
* https://docs.python.org/3/library/concurrent.futures.html
* https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor


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

### Usage

```
from ocp_resources.virtual_machine import VirtualMachine
from ocp_scale_utilities.monitoring import MonitorResourceAPIServerRequests
from ocp_scale_utilities.threaded.scale import ThreadedScaleResources
from ocp_utilities.monitoring import Prometheus

monitor_api_requests = MonitorResourceAPIServerRequests(
    prometheus=Prometheus(...),
    resource_class=VirtualMachine,
    idle_requests_value=int(virtual_machine_resource_idle),
)

monitor_api_requests.wait_for_idle()
with ThreadedScaleResources(resources=vms):
    monitor_api_requests.wait_for_idle()
    yield vms
monitor_api_requests.wait_for_idle()

```
