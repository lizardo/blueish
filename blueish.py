#!/usr/bin/python
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
import sys
import yaml
from construct import Container, ListContainer
from bt_lib.hci.transport import uart
from bt_lib.sdp import sdp

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: %s <testcase.py> <data1.yaml> [data2.yaml ...]" % sys.argv[0], file=sys.stderr)
        sys.exit(1)

    yaml.add_constructor('tag:yaml.org,2002:map',
            lambda l, n: Container(**l.construct_mapping(n)))
    yaml.add_constructor('tag:yaml.org,2002:seq',
            lambda l, n: ListContainer(l.construct_sequence(n)))
    yaml.add_constructor('!sdp',
            lambda l, n: sdp.build(Container(**l.construct_mapping(n))))

    print(open("common.py", "r").read())
    print("packets = {}")
    for data_file in sys.argv[2:]:
        print("\npackets.update({")
        with open(data_file, "r") as data:
            for doc in yaml.load_all(data):
                if doc is None:
                    print("Ignoring empty document!", file=sys.stderr)
                    continue
                p = map(lambda c: uart.build(c).encode("hex").upper(), doc)
                print("    '%s': %s," % (p[0], p[1:]))
        print("})")
    print("\n" + open(sys.argv[1], "r").read())
