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
from packet import command, event
from acldata import acldata

uart = Struct("uart",
    Enum(ULInt8("packet_indicator"),
        COMMAND = 0x01,
        ACLDATA = 0x02,
        SCODATA = 0x03,
        EVENT   = 0x04,
    ),
    Switch("packet", lambda ctx: ctx.packet_indicator,
        {
            "COMMAND": command,
            "ACLDATA": acldata,
            #"SCODATA": scodata,
            "EVENT": event,
        }
    ),
    Terminator,
)
