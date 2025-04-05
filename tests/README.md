# Running Tests

## Pre-configuration

### Existing Running Cluster (CRC or otherwise)
Simply set the KUBECONFIG environment variable
```
export KUBECONFIG=...
```

### OpenShift Local (CRC)

#### Download CRC
https://console.redhat.com/openshift/create/local

#### Setup CRC
https://crc.dev/docs/installing/
https://crc.dev/docs/configuring/

Example setup:
```
./crc config set pull-secret-file ~/openshift-local/pull-secret.txt
./crc config set disk-size 100
./crc config set memory 25165
./crc config set network-mode user
./crc cleanup
./crc setup
```

#### Set ENV vars to provide necessary paths to pytest

If you wish to use a running CRC cluster set the KUBECONFIG path only
```
unset CRC_PATH
export KUBECONFIG=~/.crc/machines/crc/kubeconfig
```

If you want the test automation to start and stop CRC, set the CRC_PATH only
```
unset KUBECONFIG
export CRC_PATH=~/openshift-local/crc-linux-2.49.0-amd64/crc
```
