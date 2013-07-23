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
from construct_helpers import *

def Opcode(name):
    return Enum(ULInt8(name),
        ERROR_RESP = 0x01,
        MTU_REQ = 0x02,
        MTU_RESP = 0x03,
        FIND_INFO_REQ = 0x04,
        FIND_INFO_RESP = 0x05,
        FIND_BY_TYPE_REQ = 0x06,
        FIND_BY_TYPE_RESP = 0x07,
        READ_BY_TYPE_REQ = 0x08,
        READ_BY_TYPE_RESP = 0x09,
        READ_REQ = 0x0A,
        READ_RESP = 0x0B,
        READ_BLOB_REQ = 0x0C,
        READ_BLOB_RESP = 0x0D,
        READ_MULTI_REQ = 0x0E,
        READ_MULTI_RESP = 0x0F,
        READ_BY_GROUP_REQ = 0x10,
        READ_BY_GROUP_RESP = 0x11,
        WRITE_REQ = 0x12,
        WRITE_RESP = 0x13,
        WRITE_CMD = 0x52,
        PREP_WRITE_REQ = 0x16,
        PREP_WRITE_RESP = 0x17,
        EXEC_WRITE_REQ = 0x18,
        EXEC_WRITE_RESP = 0x19,
        HANDLE_NOTIFY = 0x1B,
        HANDLE_IND = 0x1D,
        HANDLE_CNF = 0x1E,
        SIGNED_WRITE_CMD = 0xD2,
    )

error_resp = Struct("error_resp",
    Opcode("request"),
    ULInt16("handle"),
    Enum(ULInt8("error"),
        INVALID_HANDLE = 0x01,
        READ_NOT_PERM = 0x02,
        WRITE_NOT_PERM = 0x03,
        INVALID_PDU = 0x04,
        AUTHENTICATION = 0x05,
        REQ_NOT_SUPP = 0x06,
        INVALID_OFFSET = 0x07,
        AUTHORIZATION = 0x08,
        PREP_QUEUE_FULL = 0x09,
        ATTR_NOT_FOUND = 0x0A,
        ATTR_NOT_LONG = 0x0B,
        INSUFF_ENCR_KEY_SIZE = 0x0C,
        INVAL_ATTR_VALUE_LEN = 0x0D,
        UNLIKELY = 0x0E,
        INSUFF_ENC = 0x0F,
        UNSUPP_GRP_TYPE = 0x10,
        INSUFF_RESOURCES = 0x11,
    ),
)

mtu_req = Struct("mtu_req",
    ULInt16("client_mtu")
)

mtu_resp = Struct("mtu_resp",
    ULInt16("server_mtu")
)

class BtUuidAdapter(Adapter):
    def _encode(self, obj, context):
        if isinstance(obj, int):
            return [ord(c) for c in ULInt16("uuid16").build(obj)]
        else:
            import uuid
            return [ord(c) for c in reversed(uuid.UUID(obj).bytes)]

    def _decode(self, obj, context):
        if len(obj) == 2:
            return "0x%04x" % ULInt16("uuid16").parse("".join(chr(c) for c in obj))
        else:
            import uuid
            return str(uuid.UUID(bytes="".join(chr(c) for c in reversed(obj))))

def BT_UUID(name):
    return BtUuidAdapter(GreedyRange(ULInt8(name)))

find_info_req = Struct("find_info_req",
    ULInt16("start_handle"),
    ULInt16("end_handle"),
)

find_info_resp = Struct("find_info_resp",
    ULInt8("format"),
    GreedyRange(Struct("data_list",
        ULInt16("handle"),
        BT_UUID("uuid"),
    )),
)

read_by_type_req = Struct("read_by_type_req",
    ULInt16("start_handle"),
    ULInt16("end_handle"),
    BT_UUID("type"),
)

read_by_type_resp = Struct("read_by_type_resp",
    ULInt8("length"),
    GreedyRange(Struct("data_list",
        ULInt16("handle"),
        MetaField("value", lambda ctx: ctx._.length - 2),
    )),
)

read_req = Struct("read_req",
    ULInt16("handle"),
)

read_resp = Struct("read_resp",
    GreedyRange(ULInt8("value")),
)

read_by_group_req = Struct("read_by_group_req",
    ULInt16("start_handle"),
    ULInt16("end_handle"),
    BT_UUID("group_type"),
)

read_by_group_resp = Struct("read_by_group_resp",
    ULInt8("length"),
    GreedyRange(Struct("data_list",
        ULInt16("handle"),
        ULInt16("end_handle"),
        MetaField("value", lambda ctx: ctx._.length - 4),
    )),
)

write_req = Struct("write_req",
    ULInt16("handle"),
    GreedyRange(ULInt8("value")),
)

write_cmd = Struct("write_cmd",
    ULInt16("handle"),
    GreedyRange(ULInt8("value")),
)

att = Struct("att",
    Opcode("opcode"),
    Switch("params", lambda ctx: ctx.opcode,
        {
            "ERROR_RESP": error_resp,
            "MTU_REQ": mtu_req,
            "MTU_RESP": mtu_resp,
            "FIND_INFO_REQ": find_info_req,
            "FIND_INFO_RESP": find_info_resp,
            "READ_BY_TYPE_REQ": read_by_type_req,
            "READ_BY_TYPE_RESP": read_by_type_resp,
            "READ_REQ": read_req,
            "READ_RESP": read_resp,
            "READ_BY_GROUP_REQ": read_by_group_req,
            "READ_BY_GROUP_RESP": read_by_group_resp,
            "WRITE_REQ": write_req,
            "WRITE_RESP": Pass,
            "WRITE_CMD": write_cmd,
        }
    ),
)
