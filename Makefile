SHELL = /bin/bash

all:

kernel-emulator:
	./blueish.py data/{gatt_*,mgmt{_common,}}.yaml

kernel-emulator-android:
	./blueish.py data/{gatt_*,mgmt_{common,android}}.yaml

vhci:
	./blueish.py data/{device_le,device2,init,gatt_*}.yaml
