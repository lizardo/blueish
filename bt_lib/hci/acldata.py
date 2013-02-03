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

from construct import *
from bt_lib.construct_helpers import *
from l2cap import l2cap

Header = TunnelAdapter(
    SwapAdapter(Bytes("header", 2)),
    EmbeddedBitStruct(
        Enum(BitField("flags", 4),
            START_NO_FLUSH = 0x00,
            CONT = 0x01,
            START = 0x02,
            COMPLETE = 0x03,
            #ACTIVE_BCAST = 0x04,
            #PICO_BCAST = 0x08,
        ),
        BitField("handle", 12),
    )
)

acldata = DataStruct("acldata",
    Header,
    ULInt16("dlen"),
    Rename("data", l2cap),
)
