blueish
=======

This tool allows to generate test scripts for the Linux Bluetooth stack.
Automation is done using BlueZ D-Bus API and a state machine built from
specification files written in YAML format.

The generated scripts use the VHCI module from the kernel to emulate a
Bluetooth controller. They are "standalone", requiring only the Python standard
libraries, GLib and D-Bus bindings, which are available on most modern
distributions.

Requirements
============

Although the generated scripts require only GLib and D-Bus Python bindings, the
generator has the following requirements:

- Construct: http://construct.readthedocs.org/
- PyYAML: http://pyyaml.org/

License
=======

This program is licensed under the terms of the GNU GPLv3 (or later). See
COPYING for details.

Contact
=======

For issues/questions, send an e-mail to: *anderson.lizardo AT openbossa.org*
