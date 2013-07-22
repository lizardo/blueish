from __future__ import print_function
from common import *
from packets import *

def device_found(device_proxy):
    bus = dbus.SystemBus()

    def properties_changed(interface, changed, invalidated):
        if interface != "org.bluez.Device1":
            return
        if not changed.get("UUIDs"):
            return
        for uuid in changed["UUIDs"]:
            print("UUID: %s" % uuid)

    def set_property(proxy, iface, name, value, success_cb):
        def reply_cb(*args):
            success_cb()

        def error_cb(error):
            print("Could not set property \"%s\": %s" % (name, error))

        obj = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")
        obj.Set(iface, name, value, reply_handler=reply_cb,
                error_handler=error_cb)

    def interfaces_added(path, ifaces):
        if path != device_proxy.object_path:
            return
        if "org.bluez.ProximityMonitor1" in ifaces:
            print("Testing Proximity IAS...")
            set_property(device_proxy, "org.bluez.ProximityMonitor1",
                    "ImmediateAlertLevel", "high", lambda: None)

    def device_connect_reply():
        print("device connected")
        obj = dbus.Interface(device_proxy, "org.freedesktop.DBus.Properties")
        obj.connect_to_signal("PropertiesChanged", properties_changed)

        bus = dbus.SystemBus()
        obj = dbus.Interface(bus.get_object("org.bluez", "/"),
                "org.freedesktop.DBus.ObjectManager")
        obj.connect_to_signal("InterfacesAdded", interfaces_added)

    def device_connect_error(error):
        print("Device1.Connect failed: %s" % error)
        sys.exit(1)

    dev = dbus.Interface(device_proxy, "org.bluez.Device1")
    dev.Connect(reply_handler=device_connect_reply,
            error_handler=device_connect_error)

device_add_watch("CA:FE:CA:FE:CA:FE", device_found)
mainloop_run(packets)
