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
from six import BytesIO

# FIXME: Without this hack, context inside If/Switch is incorrectly placed
# inside "_" (just for sizeof())
class FixedSwitch(Switch):
    def _sizeof(self, ctx):
        while ctx.get("_"):
            ctx = ctx._
        return Switch._sizeof(self, ctx)

def FixedIf(predicate, subcon):
    return FixedSwitch(subcon.name, lambda ctx: bool(predicate(ctx)),
        {
            True: subcon,
            False: Pass,
        }
    )

class SwapAdapter(Adapter):
    def _encode(self, obj, context):
        return "".join(reversed(obj))

    def _decode(self, obj, context):
        return "".join(reversed(obj))

class _DataAdapter(Adapter):
    def __init__(self, subcon, data_field = "data", len_field = "dlen"):
        Adapter.__init__(self, subcon)
        self.data_field = data_field
        self.len_field = len_field

    def _encode(self, obj, ctx):
        if isinstance(obj[self.data_field], str):
            obj[self.len_field] = len(obj[self.data_field])
            return obj

        obj[self.len_field] = 0
        self.subcon._build(obj, BytesIO(), ctx)
        s = BytesIO()
        data = filter(lambda x: x.name == self.data_field, self.subcon.subcons)[0]
        data._build(obj[self.data_field], s, obj)
        obj[self.len_field] = len(s.getvalue())

        return obj

    def _decode(self, obj, ctx):
        del obj[self.len_field]

        return obj

def DataStruct(name, *subcons, **kwds):
    return _DataAdapter(Struct(name, *subcons), **kwds)

class AssertEof(Subconstruct):
    def _parse(self, stream, context):
        obj = self.subcon._parse(stream, context)
        pos = stream.tell()
        stream.seek(0, 2)
        eof = stream.tell()
        stream.seek(pos)
        if pos != eof:
            self.subcon.subcon._parse(stream, context)

        return obj

def pprint_container(obj, indent=0):
    s = ""
    if isinstance(obj, Container):
        s += "Container(\n"
        for k in sorted(obj.keys()):
            s += "    " * (indent + 1) + "%s = %s,\n" % (k, pprint_container(obj[k], indent + 1))
        s += "    " * indent + ")"
    elif isinstance(obj, str):
        s += repr(obj)
    elif isinstance(obj, bool):
        s += "True" if obj else "False"
    elif isinstance(obj, int):
        s += "%d" % obj
    elif isinstance(obj, list):
        s += "[\n"
        for i in obj:
            s += "    " * (indent + 1) + "%s,\n" % pprint_container(i, indent + 1)
        s += "    " * indent + "]"
    else:
        assert NotImplementedError, "Not supported: %s" % obj

    return s
