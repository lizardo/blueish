from __future__ import print_function
from common import *
from packets import *

def device_found(device_proxy):
    bus = dbus.SystemBus()

    def properties_changed(interface, changed, invalidated):
        if interface != "org.bluez.Device1":
            return
        if "UUIDs" in changed:
            for uuid in changed["UUIDs"]:
                print("UUID: %s" % uuid)
        if "Modalias" in changed:
            print("Modalias: %s" % changed["Modalias"])
            assert changed["Modalias"] == "bluetooth:v0002p0003d0004"

    def set_property(proxy, iface, name, value, success_cb):
        def reply_cb(*args):
            success_cb()

        def error_cb(error):
            print("Could not set property \"%s\": %s" % (name, error))

        obj = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")
        obj.Set(iface, name, value, reply_handler=reply_cb,
                error_handler=error_cb)

    def get_properties(proxy, iface, success_cb):
        def reply_cb(*args):
            success_cb(*args)

        def error_cb(error):
            print("Could not get properties: %s" % error)

        obj = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")
        obj.GetAll(iface, reply_handler=reply_cb, error_handler=error_cb)

    def interfaces_added(path, ifaces):
        if path != device_proxy.object_path:
            return

        def test_api():
            if "org.bluez.ProximityMonitor1" in ifaces:
                set_property(device_proxy, "org.bluez.ProximityMonitor1",
                        "ImmediateAlertLevel", "high",
                        lambda: print("IAS Alert Level set to high"))
            if "org.bluez.CyclingSpeed1" in ifaces:
                def show_properties(properties):
                    for p in ["WheelRevolutionDataSupported",
                            "MultipleLocationsSupported"]:
                        print("%s: %s" % (p, properties[p]))
                    assert properties["WheelRevolutionDataSupported"] == 1
                    assert properties["MultipleLocationsSupported"] == 0
                get_properties(device_proxy, "org.bluez.CyclingSpeed1",
                        show_properties)

        # FIXME: because the "exists" callback is missing on the D-Bus
        # property, delay property access so the necessary characteristics
        # can be read
        import glib
        glib.timeout_add_seconds(1, test_api)

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
