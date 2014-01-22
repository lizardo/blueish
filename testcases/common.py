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
import socket
from gi.repository import GLib, GObject, Gio
import packets

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
        elif packet.startswith("010920"):
            # < HCI Command: LE Set Scan Response Data (0x08|0x0009) plen 32
            # NOTE: Ignore Scan response data for now
            return "040E0401092000"
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

    def owner_changed(name, old, new):
        if name != "org.bluez":
            return
        if new == "":
            print("INFO: bluetoothd was terminated")
            mainloop.quit()
            return
        object_manager = dbus.Interface(bus.get_object("org.bluez", "/"),
                "org.freedesktop.DBus.ObjectManager")
        object_manager.connect_to_signal("InterfacesAdded", interfaces_added)

    print("INFO: Waiting for org.bluez service...")
    dbus_manager = dbus.Interface(bus.get_object("org.freedesktop.DBus",
            "/org/freedesktop/DBus"), "org.freedesktop.DBus")
    dbus_manager.connect_to_signal("NameOwnerChanged", owner_changed)

def io_add_watch(fd, cond, *args):
    return GLib.io_add_watch(fd, cond | GLib.IO_HUP | GLib.IO_ERR |
            GLib.IO_NVAL, *args)

def print_bdaddr(bdaddr):
    return ":".join(["%02X" % ord(c) for c in reversed(bdaddr)])

class Dispatcher(object):
    def __init__(self, kernel_emulator):
        stateful = StatefulPacket()
        if kernel_emulator:
            self.registered_sockets = {}
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            sock.setblocking(0)
            sock.bind("\0/bt_emulator")
            sock.listen(5)

            def accept_conn(fd, cb_condition):
                assert cb_condition == GLib.IO_IN
                conn_fd = sock.accept()[0]
                print("INFO: New connection (fd=%d)" % conn_fd.fileno())
                io_add_watch(conn_fd.fileno(), GLib.IO_IN,
                        Dispatcher.read_sock_data, stateful, conn_fd,
                        self.registered_sockets)
                return True

            io_add_watch(sock.fileno(), GLib.IO_IN, accept_conn)
        else:
            fd = os.open("/dev/vhci", os.O_RDWR | os.O_NONBLOCK)
            io_add_watch(fd, GLib.IO_IN, Dispatcher.read_data, stateful)

    @staticmethod
    def read_sock_data(fd, cb_condition, stateful, sock, registered_sockets):
        if cb_condition & GLib.IO_HUP:
            if registered_sockets.get(fd):
                del registered_sockets[fd]
            print("INFO: socket %d closed" % fd)
            return False

        assert cb_condition & GLib.IO_IN

        buf = sock.recv(4096)
        ofs = 0

        if registered_sockets.get(fd) is None:
            proto, = struct.unpack_from("i", buf, ofs)
            ofs += struct.calcsize("i")
            print("INFO: Registering new socket: sk=%d, proto=%d" % (fd, proto))
            registered_sockets[fd] = {"proto": proto}
            if proto == 0:
                # L2CAP socket
                family, psm, bdaddr, cid, bdaddr_type = \
                        struct.unpack_from("HH6sHBx", buf, ofs)
                ofs += struct.calcsize("HH6sHBx")
                print(("INFO: Registering L2CAP socket: family=%d, psm=%d, " +
                        "bdaddr=%s, cid=%d, bdaddr_type=%d") %
                        (family, psm, print_bdaddr(bdaddr), cid, bdaddr_type))
                registered_sockets[fd]["family"] = family
                registered_sockets[fd]["psm"] = psm
                registered_sockets[fd]["bdaddr"] = bdaddr
                registered_sockets[fd]["cid"] = cid
                registered_sockets[fd]["bdaddr_type"] = bdaddr_type
            elif proto == 1:
                # HCI socket
                family, dev, channel = struct.unpack_from("HHH", buf, ofs)
                ofs += struct.calcsize("HHH")
                print(("INFO: Registering HCI socket: family=%d, dev=%d, " +
                        "channel=%d") % (family, dev, channel))
                registered_sockets[fd]["family"] = family
                registered_sockets[fd]["dev"] = dev
                registered_sockets[fd]["channel"] = channel
            else:
                print("ERROR: Unsupported protocol %d (fd=%d)" %
                        (registered_sockets[fd]["proto"], fd))
                mainloop.quit()
                return False

            assert not buf[ofs:]
            return True

        if registered_sockets[fd]["proto"] == 1 and \
                registered_sockets[fd]["channel"] == 3:
            # mgmt socket
            hdr_len = struct.calcsize("<HHH")
            plen = struct.unpack_from("<HHH", buf, 0)[2]
            assert len(buf) == hdr_len + plen
            buf = buf.encode("hex").upper()

            if packets.mgmt.get(buf) is not None:
                for p in packets.mgmt[buf]:
                    l = sock.send(p.decode("hex"))
                    assert l == len(p.decode("hex"))
            else:
                print("ERROR: Unsupported mgmt packet: %s" % buf)
                mainloop.quit()
                return False
        elif registered_sockets[fd]["proto"] == 0:
            # L2CAP socket
            if registered_sockets[fd].get("peer_bdaddr") is None:
                # 1 byte of alignment padding
                family, psm, bdaddr, cid, bdaddr_type = \
                        struct.unpack("<HH6sHBx", buf)
                assert family == registered_sockets[fd]["family"]
                assert psm == registered_sockets[fd]["psm"]
                assert cid == registered_sockets[fd]["cid"]
                registered_sockets[fd]["peer_bdaddr"] = bdaddr
                registered_sockets[fd]["peer_bdaddr_type"] = bdaddr_type
                print(("INFO: New L2CAP connection: CID=%d, PSM=%d, " +
                    "peer_bdaddr=%s") % (psm, cid, print_bdaddr(bdaddr)))
            else:
                # L2CAP: CID
                dlen = struct.pack("<H", len(buf))
                buf = struct.pack("<H", registered_sockets[fd]["cid"]) + buf
                # L2CAP: data length
                buf = dlen + buf
                # ACL: data length
                buf = struct.pack("<H", len(buf)) + buf
                # ACL: header
                buf = "\x01\x00" + buf
                # HCI: packet indicator
                buf = "\x02" + buf

                buf = buf.encode("hex").upper()

                if packets.uart.get(buf) is not None:
                    for p in packets.uart[buf]:
                        rsp = p.decode("hex")
                        pkt_ind, = struct.unpack_from("<B", rsp, 0)
                        if pkt_ind != 0x02:
                            continue
                        acl_hdr, acl_dlen, l2cap_dlen, l2cap_cid = \
                                struct.unpack_from("<HHHH", rsp, 1)
                        assert acl_hdr == 0x2001 or acl_hdr == 0x0001
                        assert acl_dlen == l2cap_dlen + 4
                        assert l2cap_cid == registered_sockets[fd]["cid"]

                        ofs = struct.calcsize("<BHHHH")
                        l = sock.send(rsp[ofs:])
                        assert l == len(rsp[ofs:])
                else:
                    print("ERROR: Unsupported packet: %s" % buf)
                    mainloop.quit()
                    return False
        else:
            print("ERROR: Unsupported protocol %d (fd=%d)" %
                    (registered_sockets[fd]["proto"], fd))
            mainloop.quit()
            return False

        return True

    @staticmethod
    def read_data(fd, cb_condition, stateful):
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
            print("ERROR: Unsupported transport: %#x" % transport)
            mainloop.quit()
            return False

        # check if buffer contains all data
        assert len(buf) == plen + hdr_len

        buf = buf.encode("hex").upper()

        if packets.uart.get(buf) is not None:
            for p in packets.uart[buf]:
                l = os.write(fd, p.decode("hex"))
                assert l == len(p.decode("hex"))
        else:
            p = stateful.process(buf)
            if p:
                l = os.write(fd, p.decode("hex"))
                assert l == len(p.decode("hex"))
            else:
                print("ERROR: Unsupported packet: %s" % buf)
                mainloop.quit()
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
            mainloop.quit()

        return True

def mainloop_run(kernel_emulator=False):
    global mainloop

    if not kernel_emulator:
        rfkill = RFKill()
    dispatcher = Dispatcher(kernel_emulator)
    mainloop = GObject.MainLoop()
    try:
        mainloop.run()
    except KeyboardInterrupt:
        print("\nExiting...")

def mainloop_quit():
    mainloop.quit()

def run_bluetoothd(prefix="/usr", var="/var", clear_storage=True,
        log_file=None, kernel_emulator=False):
    import subprocess
    import shutil

    if clear_storage:
        print("INFO: Cleaning storage")
        shutil.rmtree(var + "/lib/bluetooth", ignore_errors=True)
        os.makedirs(var + "/lib/bluetooth", mode=0755)

    if log_file:
        stderr = subprocess.STDOUT
        stdout = log_file
    else:
        stderr = stdout = None

    sup_file = os.tmpfile()
    sup_file.write("\n".join([
            "{",
            "libc-exit",
            "Memcheck:Free",
            "fun:free",
            "fun:__libc_freeres",
            "fun:_Exit",
            "}"]))

    open_fds = filter(lambda fd: fd > 2, map(int, os.listdir("/dev/fd")))
    new_fd = max(open_fds) + 1

    def close_fds():
        # Close all FDs, but duplicate suppression file descriptor first.
        # Unfortunately, we can't use close_fds=True on Popen(), otherwise the
        # temporary file created above will also be closed.
        os.dup2(sup_file.fileno(), new_fd)
        for fd in open_fds:
            try:
                os.close(fd)
            except:
                pass

    env = {
        "G_SLICE": "always-malloc",
        "DBUS_SYSTEM_BUS_ADDRESS": os.environ["DBUS_SYSTEM_BUS_ADDRESS"],
    }

    if kernel_emulator:
        basedir = os.path.dirname(sys.argv[0])
        env["LD_PRELOAD"] = basedir + "/../valgrind/bt-kernel.so"

    return subprocess.Popen(["valgrind", "--track-fds=yes", "--leak-check=full",
            "--suppressions=/dev/fd/%d" % new_fd,
    #return subprocess.Popen(["/usr/bin/strace", "-x", "-v", "-ff", "-s", "200",
    #"/usr/bin/strace", "-x", "-v", "-ff", "-s", "200", "-o", "/tmp/strace.log",
            prefix + "/libexec/bluetooth/bluetoothd", "-n", "-d"],
            stderr=stderr, stdout=stdout, env=env, preexec_fn=close_fds)

def fake_dbus():
    test_dbus = Gio.TestDBus.new(Gio.TestDBusFlags.NONE)
    test_dbus.up()
    os.environ["DBUS_SYSTEM_BUS_ADDRESS"] = test_dbus.get_bus_address()

    return test_dbus
