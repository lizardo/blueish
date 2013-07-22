from __future__ import print_function
from common import *
from packets import *

def device_found(device_proxy):
    def properties_changed(interface, changed, invalidated):
        if interface != "org.bluez.Device1":
            return
        if not changed.get("UUIDs"):
            return
        for uuid in changed["UUIDs"]:
            print("UUID: %s" % uuid)

    def device_connect_reply():
        print("device connected")
        obj = dbus.Interface(device_proxy, "org.freedesktop.DBus.Properties")
        obj.connect_to_signal("PropertiesChanged", properties_changed)

    def device_connect_error(error):
        print("Device1.Connect failed: %s" % error)
        sys.exit(1)

    dev = dbus.Interface(device_proxy, "org.bluez.Device1")
    dev.Connect(reply_handler=device_connect_reply,
            error_handler=device_connect_error)

device_add_watch("CA:FE:CA:FE:CA:FE", device_found)
mainloop_run(packets)