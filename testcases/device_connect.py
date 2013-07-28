from __future__ import print_function
from common import *
from packets import *

def device_found(adapter_proxy, device_proxy):
    def device_connect_reply():
        print("device connected")
        sys.exit(0)

    def device_connect_error(error):
        print("Device1.Connect failed: %s" % error)
        sys.exit(1)

    dev = dbus.Interface(device_proxy, "org.bluez.Device1")
    dev.Connect(reply_handler=device_connect_reply,
            error_handler=device_connect_error)

device_add_watch("CA:FE:CA:FE:CA:FE", device_found)
mainloop_run(packets)
