#!/usr/bin/python
from __future__ import print_function
from common import *
from packets import *
import dbus.service
from gi.repository import GLib

# Timeout for terminating bluetoothd with CTRL+C
TIMEOUT = 10

gatt_services = set([
    "00001800-0000-1000-8000-00805f9b34fb",
    "00001801-0000-1000-8000-00805f9b34fb",
    "00001802-0000-1000-8000-00805f9b34fb",
    "00001803-0000-1000-8000-00805f9b34fb",
    "00001804-0000-1000-8000-00805f9b34fb",
    "00001809-0000-1000-8000-00805f9b34fb",
    "0000180a-0000-1000-8000-00805f9b34fb",
    "0000180d-0000-1000-8000-00805f9b34fb",
    "00001812-0000-1000-8000-00805f9b34fb",
    "00001813-0000-1000-8000-00805f9b34fb",
    "00001816-0000-1000-8000-00805f9b34fb",
    "00010203-0405-0607-0809-0a0b0c0d0e0f",
    "a585221e-ca51-4018-aae7-ce41c9342bb4",
    "b6eaac30-2a91-4b55-8039-d35f9cfaf159",
])

watchers = {}

# HID over GATT does not have a D-Bus API
def test_hog(command):
    with open("/tmp/hogsuspend", "w") as f:
        print("[HOG] Running command: %s" % command)
        f.write(command)

def device_found(adapter_proxy, device_proxy):
    global watchers
    bus = dbus.SystemBus()

    def properties_changed(interface, changed, invalidated):
        if interface == "org.bluez.Device1":
            if "UUIDs" in changed:
                for uuid in changed["UUIDs"]:
                    print("UUID: %s" % uuid)
                    if uuid == "00001812-0000-1000-8000-00805f9b34fb":
                        GLib.timeout_add_seconds(1, test_hog, "suspend")
                        GLib.timeout_add_seconds(2, test_hog, "resume")
                assert gatt_services == set(changed["UUIDs"])
            if "Modalias" in changed:
                print("Modalias: %s" % changed["Modalias"])
                assert changed["Modalias"] == "bluetooth:v0002p0003d0004"
        elif interface == "org.bluez.ProximityMonitor1":
            if "ImmediateAlertLevel" in changed:
                print("[IAS] ImmediateAlertLevel: %s" % changed["ImmediateAlertLevel"])
            if "LinkLossAlertLevel" in changed:
                print("[LLS] LinkLossAlertLevel: %s" % changed["LinkLossAlertLevel"])
        elif interface == "org.bluez.CyclingSpeed1":
            if "Location" in changed:
                print("[CSC] Location: %s" % changed["Location"])

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
                        "ImmediateAlertLevel", "mild",
                        lambda: print("[IAS] Alert Level set to mild"))
                set_property(device_proxy, "org.bluez.ProximityMonitor1",
                        "LinkLossAlertLevel", "mild",
                        lambda: print("[LLS] Alert Level set to mild"))
            if "org.bluez.CyclingSpeed1" in ifaces:
                class CscWatcher(dbus.service.Object):
                    @dbus.service.method("org.bluez.CyclingSpeedWatcher1", in_signature="oa{sv}", out_signature="")
                    def MeasurementReceived(self, device, measure):
                        print("[CSC] Measurement received from %s" % device)
                        manager = dbus.Interface(adapter_proxy, "org.bluez.CyclingSpeedManager1")
                        manager.UnregisterWatcher("/csc_watcher",
                                reply_handler=lambda *a: print("[CSC] Watcher unregistered"),
                                error_handler=lambda e: print("[CSC] Could not unregister watcher: %s" % e))

                obj = dbus.Interface(device_proxy, "org.bluez.CyclingSpeed1")

                def show_properties(properties):
                    for p in ["WheelRevolutionDataSupported",
                            "MultipleLocationsSupported", "Location", "SupportedLocations"]:
                        print("[CSC] %s: %s" % (p, properties[p]))
                    assert properties["WheelRevolutionDataSupported"] == 1
                    assert properties["MultipleLocationsSupported"] == 1
                    assert properties["Location"] == "other"
                    assert set(properties["SupportedLocations"]) == set(["other", "hip"])
                    GLib.timeout_add_seconds(1, set_property, device_proxy,
                            "org.bluez.CyclingSpeed1", "Location", "hip",
                            lambda: print("[CSC] Location set to hip"))

                get_properties(device_proxy, "org.bluez.CyclingSpeed1",
                        show_properties)
                obj.SetCumulativeWheelRevolutions(dbus.UInt32(0x1234),
                        reply_handler=lambda *a: print("[CSC] SetCumulativeWheelRevolutions() successful"),
                        error_handler=lambda e: print("[CSC] SetCumulativeWheelRevolutions() failed: %s" % e))

                watchers["csc"] = CscWatcher(bus, "/csc_watcher")
                manager = dbus.Interface(adapter_proxy, "org.bluez.CyclingSpeedManager1")
                manager.RegisterWatcher("/csc_watcher",
                        reply_handler=lambda *a: print("[CSC] Watcher registered"),
                        error_handler=lambda e: print("[CSC] Could not register watcher: %s" % e))

            if "org.bluez.HeartRate1" in ifaces:
                class HrsWatcher(dbus.service.Object):
                    @dbus.service.method("org.bluez.HeartRateWatcher1", in_signature="oa{sv}", out_signature="")
                    def MeasurementReceived(self, device, measure):
                        print("[HRS] Measurement received from %s" % device)
                        manager = dbus.Interface(adapter_proxy, "org.bluez.HeartRateManager1")
                        manager.UnregisterWatcher("/hrs_watcher",
                                reply_handler=lambda *a: print("[HRS] Watcher unregistered"),
                                error_handler=lambda e: print("[HRS] Could not unregister watcher: %s" % e))

                watchers["hrs"] = HrsWatcher(bus, "/hrs_watcher")
                manager = dbus.Interface(adapter_proxy, "org.bluez.HeartRateManager1")
                manager.RegisterWatcher("/hrs_watcher",
                        reply_handler=lambda *a: print("[HRS] Watcher registered"),
                        error_handler=lambda e: print("[HRS] Could not register watcher: %s" % e))

                obj = dbus.Interface(device_proxy, "org.bluez.HeartRate1")
                obj.Reset(reply_handler=lambda *a: print("[HRS] Reset() successful"),
                        error_handler=lambda e: print("[HRS] Reset() failed: %s" % e))

                def show_properties(properties):
                    for p in ["Location", "ResetSupported"]:
                        print("[HRS] %s: %s" % (p, properties[p]))
                    assert properties["Location"] == "other"
                    assert properties["ResetSupported"] == 1

                get_properties(device_proxy, "org.bluez.HeartRate1", show_properties)
            if "org.bluez.Thermometer1" in ifaces:
                class HtsWatcher(dbus.service.Object):
                    @dbus.service.method("org.bluez.ThermometerWatcher1", in_signature="oa{sv}", out_signature="")
                    def MeasurementReceived(self, device, measure):
                        print("[HTS] Measurement received from %s" % device)
                        manager = dbus.Interface(adapter_proxy, "org.bluez.ThermometerManager1")
                        manager.DisableIntermediateMeasurement("/hts_watcher",
                                reply_handler=lambda *a: print("[HTS] DisableIntermediateMeasurement() successful"),
                                error_handler=lambda e: print("[HTS] DisableIntermediateMeasurement() failed: %s" % e))
                        manager.UnregisterWatcher("/hts_watcher",
                                reply_handler=lambda *a: print("[HTS] Watcher unregistered"),
                                error_handler=lambda e: print("[HTS] Could not unregister watcher: %s" % e))

                watchers["hts"] = HtsWatcher(bus, "/hts_watcher")
                manager = dbus.Interface(adapter_proxy, "org.bluez.ThermometerManager1")
                manager.RegisterWatcher("/hts_watcher",
                        reply_handler=lambda *a: print("[HTS] Watcher registered"),
                        error_handler=lambda e: print("[HTS] Could not register watcher: %s" % e))
                manager.EnableIntermediateMeasurement("/hts_watcher",
                        reply_handler=lambda *a: print("[HTS] EnableIntermediateMeasurement() successful"),
                        error_handler=lambda e: print("[HTS] EnableIntermediateMeasurement() failed: %s" % e))

                def show_properties(properties):
                    for p in ["Maximum", "Minimum", "Intermediate", "Interval"]:
                        print("[HTS] %s: %s" % (p, properties[p]))
                    assert properties["Maximum"] == 0xffff
                    assert properties["Minimum"] == 0x0001
                    assert properties["Intermediate"] == 1
                    assert properties["Interval"] == 120
                    set_property(device_proxy, "org.bluez.Thermometer1",
                            "Interval", dbus.UInt16(240),
                            lambda: print("[HTS] Interval set to 240"))

                get_properties(device_proxy, "org.bluez.Thermometer1", show_properties)

        # FIXME: because the "exists" callback is missing on the D-Bus
        # property, delay property access so the necessary characteristics
        # can be read
        GLib.timeout_add_seconds(1, test_api)

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

def run_daemon():
    global bluetoothd, log_file

    print("INFO: bluetoothd will be terminated in %s seconds" % TIMEOUT)
    log_file = open("/tmp/bluetoothd.log", "w")
    bluetoothd = run_bluetoothd("/opt/bluez", "/opt/bluez/var", True, log_file)

def kill_daemon():
    bluetoothd.terminate()

test_dbus = fake_dbus()

GLib.idle_add(run_daemon)
GLib.timeout_add_seconds(TIMEOUT, kill_daemon)
device_add_watch("CA:FE:CA:FE:CA:FE", device_found)

mainloop_run(packets)

bluetoothd.wait()
log_file.close()
test_dbus.down()
