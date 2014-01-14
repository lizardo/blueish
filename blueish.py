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
import argparse
import yaml
from construct import Container, ListContainer
from bt_lib import mgmt
from bt_lib.hci.transport import uart
from bt_lib.sdp import sdp
from bt_lib.att import att

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse data files and generate a packets.py.")
    parser.add_argument("datafile", nargs="+", type=file,
            help="specify one or more data files in YAML format")
    args = parser.parse_args()

    yaml.add_constructor('tag:yaml.org,2002:map',
            lambda l, n: Container(**l.construct_mapping(n)))
    yaml.add_constructor('tag:yaml.org,2002:seq',
            lambda l, n: ListContainer(l.construct_sequence(n)))
    yaml.add_constructor('!sdp',
            lambda l, n: sdp.build(Container(**l.construct_mapping(n))))
    yaml.add_constructor('!att',
            lambda l, n: att.build(Container(**l.construct_mapping(n))))

    print("Generating testcases/packets.py...")

    packets = {"uart": {}, "mgmt": {}}
    for data in args.datafile:
        for doc in yaml.load_all(data):
            if doc is None:
                print("Ignoring empty document!", file=sys.stderr)
                continue
            if doc[0].get("packet_indicator") is not None:
                p = map(lambda c: uart.build(c), doc)
                packets["uart"][p[0]] = p[1:]
            else:
                # Assume first entry as command for mgmt datafiles, as it is
                # expected that BlueZ only send commands to kernel
                cmd = mgmt.command.build(doc[0])
                evts = map(lambda c: mgmt.event.build(c), doc[1:])
                packets["mgmt"][cmd] = evts

    with open("testcases/packets.py", "w") as modfile:
        for pkt_type in ["uart", "mgmt"]:
            print("%s = {" % pkt_type, file=modfile)
            for (k, v) in packets[pkt_type].iteritems():
                k = k.encode("hex").upper()
                v = map(lambda p: p.encode("hex").upper(), v)
                print("    '%s': %s," % (k, v), file=modfile)
            print("}", file=modfile)
