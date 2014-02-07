#!/usr/bin/python
from __future__ import print_function
from common import *
import common
import socket
import os.path
import os
import shutil
import signal
import ctypes
import io

prefix = "/opt/bluez"
srcdir = os.path.expanduser("~/trees/bluez.git")
kernel_emulator = True
log_file = open("/tmp/android.log", "w")
haltest_log = open("/tmp/haltest.log", "w")
children = []

def monitor_children():
    sigset_t = 1024 / (8 * ctypes.sizeof(ctypes.c_ulong)) * ctypes.c_ulong
    mask = sigset_t()
    libc = ctypes.CDLL("libc.so.6")
    assert libc.sigemptyset(ctypes.pointer(mask)) == 0
    assert libc.sigaddset(ctypes.pointer(mask), signal.SIGCHLD) == 0
    assert libc.sigprocmask(0, ctypes.pointer(mask), 0) == 0
    fd = libc.signalfd(-1, ctypes.pointer(mask), os.O_NONBLOCK)
    print("INFO: signalfd() returned %d" % fd)
    assert fd >= 0

    def got_signal(fd, cb_condition):
        assert cb_condition == GLib.IO_IN

        buf = os.read(fd, 128)
        signo = ctypes.c_uint.from_buffer_copy(buf, 0)
        assert signo.value == signal.SIGCHLD
        pid = ctypes.c_uint.from_buffer_copy(buf, 12)
        status = ctypes.c_int.from_buffer_copy(buf, 40)
        print("INFO: PID %d has exited with status %d" % (pid.value,
            status.value))
        children.remove(pid.value)
        if not children:
            mainloop.quit()
            return False

        return True

    io_add_watch(fd, GLib.IO_IN, got_signal)

    return fd

def run_haltest():
    global backlog, next_command
    app = subprocess.Popen([srcdir + "/android/haltest", "-n"],
            stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
            stdin=subprocess.PIPE, close_fds=True)

    commands = [
        (">", "bluetooth init"),
        ("if_bluetooth->init: BT_STATUS_SUCCESS", "bluetooth enable"),
        ("adapter_state_changed_cb: state=BT_STATE_ON", "bluetooth start_discovery"),
        ("device_found_cb: num_properties=2", "bluetooth create_bond 12:34:12:34:12:34"),
        ("acl_state_changed_cb: status=BT_STATUS_SUCCESS remote_bd_addr=12:34:12:34:12:34 state=BT_ACL_STATE_CONNECTED",
            "bluetooth remove_bond 12:34:12:34:12:34"),
        ("if_bluetooth->remove_bond: BT_STATUS_SUCCESS", "bluetooth disable"),
        ("if_bluetooth->disable: BT_STATUS_SUCCESS", "bluetooth cleanup"),
        ("if_bluetooth->cleanup: void", "exit"),
    ]

    backlog = []
    next_command = None

    def haltest_output(fd, cb_condition):
        global backlog, next_command

        if cb_condition & GLib.IO_HUP:
            print("INFO: haltest has exited")
            return False

        assert cb_condition == GLib.IO_IN
        buf = os.read(fd, io.DEFAULT_BUFFER_SIZE)

        #print("XXX: %s" % repr(buf))

        backlog += map(str.strip, buf.strip().split("\n"))

        if commands and commands[0][0] in backlog:
            next_command = commands[0][1]
            commands.pop(0)

        if ">" in backlog and next_command:
            print("INFO: Executing \"%s\"" % next_command)
            app.stdin.write(next_command + "\n")
            next_command = None
            backlog = []

        return True

    io_add_watch(app.stdout.fileno(), GLib.IO_IN, haltest_output)
    print("haltest started with PID %d" % app.pid)
    children.append(app.pid)

def android_command(fd, cb_condition):
    assert cb_condition == GLib.IO_IN
    buf = sock.recv(io.DEFAULT_BUFFER_SIZE)
    print("INFO: Received command: %s" % buf)

    if buf.startswith("bluetooth.start=daemon"):
        app = run_application([srcdir + "/android/bluetoothd"], log_file,
                kernel_emulator)
        print("bluetoothd started with PID %d" % app.pid)
        children.append(app.pid)
    else:
        assert NotImplementedError, "Command not supported: %s" % buf

    return True

def create_android_socket():
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.setblocking(0)
    sock_name = "\0android_system"
    # Workaround: BlueZ (and apparently Android as well), does not pass the
    # correct addrlen to bind() when creating the UNIX socket (it always passes
    # the maximum length). Therefore, we have to fill remaining path field with
    # zeroes.
    sock.bind(sock_name + "\0" * (108 - len(sock_name)))

    return sock

sfd = monitor_children()

print("INFO: Cleaning bluetoothd storage")
shutil.rmtree(prefix + "/var/lib/bluetooth", ignore_errors=True)
os.makedirs(prefix + "/var/lib/bluetooth", mode=0755)

print("INFO: Starting Android system socket")
sock = create_android_socket()
io_add_watch(sock.fileno(), GLib.IO_IN, android_command)

dispatcher = Dispatcher(kernel_emulator)

mainloop = GObject.MainLoop()
common.mainloop = mainloop
GLib.idle_add(run_haltest)

try:
    mainloop.run()
except KeyboardInterrupt:
    pass

print("\nExiting...")
sock.close()
haltest_log.close()
log_file.close()
os.close(sfd)
