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
from bt_lib.hci.transport import uart
from construct import Container, ListContainer

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: %s <packet-in-hex> [<packet-in-hex> ...]")
        sys.exit(1)

    yaml.add_representer(ListContainer,
        lambda dumper, data: dumper.represent_sequence('tag:yaml.org,2002:seq', data))
    yaml.add_representer(Container,
        lambda dumper, data: dumper.represent_mapping('tag:yaml.org,2002:map', data))
    data = map(lambda d: uart.parse(d.decode("hex")), sys.argv[1:])
    print(yaml.dump(data))
