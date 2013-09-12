#  Copyright (C) 2013  Instituto Nokia de Tecnologia - INdT
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
from __future__ import print_function
import os
import sys
import dbus
import dbus.mainloop.glib
import struct
from gi.repository import GLib, GObject

class StatefulPacket(object):
    """These packets use data that is either derived from the OS, or from
    previous packets, and therefore are not "stateless" as the packets
    above."""

    local_name = "00" * 248
    cod = "000000"

    def process(self, packet):
        if packet.startswith("01130CF8"):
            # < HCI Command: Write Local Name (0x03|0x0013) plen 248
            self.local_name = packet[-248:]
            return "040E0401130C00"
        elif packet == "01140C00":
            # < HCI Command: Read Local Name (0x03|0x0014) plen 0
            return "040EFC01140C00" + self.local_name
        elif packet.startswith("010820"):
            # < HCI Command: LE Set Advertising Data (0x08|0x0008) plen 32
            # NOTE: Ignore Adv. data for now
            return "040E0401082000"
        elif packet == "01230C00":
            # < HCI Command: Read Class of Device (0x03|0x0023) plen 0
            return "040E0701230C00" + self.cod
        elif packet.startswith("01240C03"):
            # < HCI Command: Write Class of Device (0x03|0x0024) plen 3
            self.cod = packet[-3:]
            return "040E0401240C00"
        elif packet.startswith("01520CF1" + "00"):
            # < HCI Command: Write Extended Inquiry Response (0x03|0x0052) plen 241
            # NOTE: EIR data is ignored for now
            return "040E0401520C00"

def device_add_watch(bd_addr, callback):
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    def set_property(path, iface, name, value, success_cb):
        def reply_cb(*args):
            success_cb()

        def error_cb(error):
            print("Could not set property \"%s\": %s" % (name, error))

        obj = dbus.Interface(bus.get_object("org.bluez", path),
                "org.freedesktop.DBus.Properties")
        obj.Set(iface, name, value, reply_handler=reply_cb,
                error_handler=error_cb)

    def interfaces_added(path, ifaces):
        if "org.bluez.Adapter1" in ifaces:
            print("Found adapter %s" % path)
            global adapter
            adapter = dbus.Interface(bus.get_object("org.bluez", path),
                    "org.bluez.Adapter1")
            set_property(path, "org.bluez.Adapter1", "Powered",
                    dbus.Boolean(True), lambda: adapter.StartDiscovery())
        elif "org.bluez.Device1" in ifaces:
            d = ifaces["org.bluez.Device1"]
            if d["Adapter"] != adapter.object_path or d["Address"] != bd_addr:
                return
            print("Found device %s" % path)
            adapter.StopDiscovery()
            callback(adapter.proxy_object, bus.get_object("org.bluez", path))

    object_manager = dbus.Interface(bus.get_object("org.bluez", "/"),
            "org.freedesktop.DBus.ObjectManager")
    object_manager.connect_to_signal("InterfacesAdded", interfaces_added)

class Dispatcher(object):
    def __init__(self, packets, stateful):
        self.fd = os.open("/dev/vhci", os.O_RDWR | os.O_NONBLOCK)
        GLib.io_add_watch(self.fd, GLib.IO_IN, Dispatcher.read_data, packets,
                stateful)

    @staticmethod
    def read_data(fd, cb_condition, packets, stateful):
        assert cb_condition == GLib.IO_IN

        buf = os.read(fd, 4096)

        transport = struct.unpack_from("B", buf, 0)[0]
        if transport == 0x01:
            # HCI Command packet
            plen = struct.unpack_from("B", buf, 3)[0]
            hdr_len = 4
        elif transport == 0x02:
            # HCI ACL Data packet
            plen = struct.unpack_from("<H", buf, 3)[0]
            hdr_len = 5
        elif transport == 0xff:
            # HCI Vendor packet (currently used to set device type)
            # Assume device type to be HCI_BREDR and index 0
            assert buf == "\xff\x00\x00\x00"
            return True
        else:
            print("Unsupported transport: %#x" % transport)
            sys.exit(1)
            return False

        # check if buffer contains all data
        assert len(buf) >= plen + hdr_len

        buf = buf.encode("hex").upper()

        if packets.get(buf) is not None:
            for p in packets[buf]:
                os.write(fd, p.decode("hex"))
        else:
            p = stateful.process(buf)
            if p:
                os.write(fd, p.decode("hex"))
            else:
                print("Unsupported packet: %s" % buf)
                sys.exit(1)
                return False

        return True

class RFKill(object):
    def __init__(self):
        self.fd = os.open("/dev/rfkill", os.O_RDONLY | os.O_NONBLOCK)
        self.idx = None

        # Consume events of already present devices
        while True:
            try:
                os.read(self.fd, 8)
            except OSError, e:
                import errno
                if e.errno == errno.EAGAIN:
                    break
                else:
                    raise

        GLib.io_add_watch(self.fd, GLib.IO_IN, RFKill.read_data, self)

    @staticmethod
    def read_data(fd, cb_condition, self):
        assert cb_condition == GLib.IO_IN

        idx, type_, op, soft, hard = struct.unpack("<LBBBB", os.read(fd, 8))
        if op == 0 and type_ == 2:
            print("rfkill: Bluetooth device added, idx=%d, soft=%d, hard=%d" %
                    (idx, soft, hard))
            self.idx = idx
        elif self.idx is not None and self.idx == idx and op in (2, 3) and \
                type_ == 2 and soft == 1:
            print("ERROR: Emulated Bluetooth adapter was blocked using RF-kill")
            sys.exit(1)

        return True

def mainloop_run(packets):
    stateful = StatefulPacket()
    rfkill = RFKill()
    dispatcher = Dispatcher(packets, stateful)
    loop = GObject.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        print("\nExiting...")
