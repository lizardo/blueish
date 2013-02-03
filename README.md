Blueish
=======

This tool allows to generate test scripts for the Linux Bluetooth stack.
Automation is done using BlueZ D-Bus API and a state machine built from
specification files written in YAML format.

The generated scripts use the VHCI module from the kernel to emulate a
Bluetooth controller. Therefore, no Bluetooth hardware is required.

Minimum Requirements
====================

Blueish generator:
- Python 2.7
- Construct: http://construct.readthedocs.org/
- PyYAML: http://pyyaml.org/

Generated scripts:
- Python 2.7
- Glib/D-Bus bindings
- Kernel with VHCI support enabled

Usage Instructions
==================

There is no installation procedure for Blueish yet, so be sure to keep the
source directory around when using it.

Generating tests
----------------

To generate a test script, you need a "testcase" (a snippet of Python code
which will use BlueZ's D-Bus API for test automation) and one or more data
files in YAML format.

Blueish comes with some testcases and data files which can be used as base for
writing new tests.

The `blueish.py` program is used for test generation:

	./blueish.py <testcase.py> <data1.yaml> [data2.yaml ...] > test.py

This will create a "test.py" standalone test script which uses the given
testcase and data files.

If more than one data file is given, they will be merged into a single state
machine. Data files can override entries from previously given ones (the last
files take precedence).

Running tests
-------------

1. Make sure BlueZ daemon is running. For troubleshooting, it is recommended to
   run bluetoothd with `-d` option.
2. If necessary, load the `hci_vhci` kernel module with:

	$ sudo modprobe hci_vhci

3. Run script (root required due to VHCI and BlueZ D-Bus access restrictions):

	$ sudo ./<script_name>

4. Check BlueZ logs (it is recommended to run BlueZ under Valgrind to look for
   memory errors and crash backtraces)
5. The script should terminate itself. If not, terminate it with CTRL+C, which
   will also remove the emulated adapter from the system.

Writing testcases
-----------------

Blueish ships with a number of testcases on the `testcases/` directory.

A minimum testcase script follows:

	def device_found(device_proxy):
	    def device_connect_reply():
	        print("device connected")
	        # Use any interfaces available for the device object here.
	        sys.exit(0)

	    def device_connect_error(error):
	        print("Device1.Connect failed: %s" % error)
	        sys.exit(1)

	    dev = dbus.Interface(device_proxy, "org.bluez.Device1")
	    dev.Connect(reply_handler=device_connect_reply,
	        error_handler=device_connect_error)

	wait_for_device(packets, "12:34:12:34:12:34", device_found)

This testcase uses `org.bluez.Device1.Connect()` to connect to a device.
`wait_for_device()` takes care of adapter setup and device discovery. The
callback is called after device object is created and is ready for use.

The `packets` argument passed to `wait_for_device()` contains a dictionary of
hex-encoded "raw" packets, whose key is the packet that should match with the
one received by the emulated controller (coming from the kernel), and the value
is a list of packets that will be sent to the kernel in response.

This dictionary is built by Blueish generator from the data files. It is not
recommended to manipulate the dictionary directly, instead write new data files
to extend it or override entries.

Writing data files
------------------

Blueish ships with a number of data files on the `data/` directory.

Data files use the [YAML][] format. Currently, PyYAML supports only the
[1.1][YAML11] format. This README will follow the YAML nomenclature where
possible.

Basically, a data file consists of one or more "documents", which are snippets
of YAML formatted text separated by "---" markers:

	<document-1>
	---
	<document-2>
	---
	<document-3>
	...

Specifically for Blueish, each document should be a sequence of nested
mappings:

	- key1:
	    key2: value2
	- key3: value3
	- key4: value4

Each sequence entry represents a packet. At least two packets must be provided:
the first one will be compared with a packet received from the kernel, and if
matched, the remaining packets from the document will be sent as response.

The key and values depend on the packet type being constructed: HCI command,
HCI event, ACL data or SCO data. This is specified on the `packet_indicator`
mapping entry, which can be one of:

* COMMAND
* ACLDATA
* SCODATA (not implemented yet)
* EVENT

All packet types have a "packet" entry whose sub-entries depend on the type:

* `COMMAND` packets: `opcode` (with `ogf` and `ocf` sub-entries) and `params`
  (command specific parameters)
* `ACLDATA` packets: `header` (with `handle` and `flags` sub-entries) and
  `data` (with `cid` and `data` sub-entries)
* `EVENT` packets: `evt` (event code) and `params` (event specific parameters)

As example, this is a complete data file that will expect a "Inquiry" HCI
command and reply with a "Command Status" event:

	- packet_indicator: COMMAND
	  packet:
	    opcode: &opcode {ocf: INQUIRY, ogf: LINK_CTL}
	    params:
	      lap: [51, 139, 158]
	      length: 4
	      num_rsp: 0
	- packet_indicator: EVENT
	  packet:
	    evt: CMD_STATUS
	    params:
	      ncmd: 1
	      opcode: *opcode
	      status: 0

The `&opcode` and `*opcode` annotations are just a YAML shortcut to avoid
duplicating information. `*opcode` will be replaced by `{ocf: INQUIRY, ogf:
LINK_CTL}`.

The key names and value types come from the packet parser implemented in
Blueish, which was based on C header files from BlueZ/kernel sources.
Hopefully, the provided data files, parser source code and Bluetooth Core
Specification will be enough for writing your own data files.

If you have raw packets and want to convert them to data files, the
`packet2yaml.py` tool may be helpful. Just pass the hex-encoded packets to it
(separated by space) and it will output YAML formatted text, e.g.:

	$ ./packet2yaml.py 01010405338B9E0400
	- packet:
	    opcode: {ocf: INQUIRY, ogf: LINK_CTL}
	    params:
	      lap: [51, 139, 158]
	      length: 4
	      num_rsp: 0
	  packet_indicator: COMMAND

HCI packet parser/builder library
---------------------------------

The `bt_lib/` directory contains the packet parser/builder used by Blueish to
generate scripts.

Here is a summary of the available modules and Core Spec parts where the
packets are described in detail:

* `sdp.py`: SDP related structures (Volume 3, Part B)
* `hci/transport.py`: HCI UART transport protocol (Volume 4, Part A, Section 2)
* `hci/l2cap.py`: L2CAP data and signaling packets (Volume 3, Part A)
* `hci/packet.py`: HCI commands and events (Volume 2, Part E)
* `hci/acldata.py`: ACL data packet (Volume 2, Part E, Section 5.4.2)
* `construct_helpers.py`: Construct related classes used by various modules

Troubleshooting
===============

As the test script runs, debugging messages are printed. They mostly consist of
the received HCI packet data. See below a list of common problems and how to
solve them.

Unsupported features
--------------------

If the test script ends with "Unsupported transport" or "Unsupported packet",
it means the packet did not match with any of the packets provided by the data
files. In this case, you can use `packet2yaml.py` to identify the packet and
add it to a data file, along with the response packet(s).

If `packet2yaml.py` returns a Construct error on the packet, it means it is not
implemented in the parser library yet. Support for more packets is being added
as necessary.

Feel free to report the problem on the [issue tracker][], along with your
BlueZ/kernel versions and the steps to reproduce it.

Missing /dev/vhci
-----------------

If you get this error:

	Traceback (most recent call last):
	  File "./hid_sdp_crash1.py", line 346, in <module>
	    fd = os.open("/dev/vhci", os.O_RDWR | os.O_NONBLOCK)
	OSError: [Errno 2] No such file or directory: '/dev/vhci'

Make sure the `hci_vhci` kernel module is loaded, by running:

	$ sudo modprobe hci_vhci

RF-kill blocking
----------------

Even though the controller created by VHCI is emulated, it is also sensitive to
RF-kill blocking. This blocking is usually done using some Desktop environment
option (e.g. "Turn Off Bluetooth" on Unity Bluetooth icon).

If the script gives this error:

	ERROR: Emulated Bluetooth adapter was blocked using RF-Kill

You need to unblock Bluetooth from RF-kill. The easiest way to do this is to
use rfkill tool:

	$ rfkill unblock bluetooth

If "rfkill" is not available on your system, look for some Bluetooth on/off
option on your Desktop settings.

License
=======

This program is licensed under the terms of the GNU GPLv3 (or later). See
COPYING for details.

Contact
=======

For issues/questions, send an e-mail to <anderson.lizardo@openbossa.org>.


[YAML]:   http://www.yaml.org/      "Official YAML Web Site"
[YAML11]: http://yaml.org/spec/1.1/ "YAML Version 1.1 Specification"
[issue tracker]: https://github.com/lizardo/blueish/issues "Blueish issue tracker"
