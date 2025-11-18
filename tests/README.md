# Running Tests

## Setup uv
https://github.com/astral-sh/uv

## OpenShift Local (CRC)

### Download CRC
https://console.redhat.com/openshift/create/local

### Setup CRC
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

### Set ENV vars to provide necessary paths to pytest

Set CRC_PATH only. If CRC is already running, will use it, otherwise will start/stop CRC.
```
unset KUBECONFIG
export CRC_PATH=~/openshift-local/crc-linux-2.49.0-amd64/crc
```

## Run tests
```
uv run pytest tests
```
