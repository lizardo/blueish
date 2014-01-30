SHELL = /bin/bash

all:

kernel-emulator:
	./blueish.py data/{gatt_*,mgmt}.yaml

vhci:
	./blueish.py data/{device1,init,gatt_*}.yaml
