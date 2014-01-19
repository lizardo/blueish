#  Copyright (C) 2014  Instituto Nokia de Tecnologia - INdT
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

def CommandCode(name):
    return Enum(ULInt16(name),
        READ_VERSION = 0x0001,
        READ_COMMANDS = 0x0002,
        READ_INDEX_LIST = 0x0003,
        READ_INFO = 0x0004,
        SET_POWERED = 0x0005,
        SET_DISCOVERABLE = 0x0006,
        SET_CONNECTABLE = 0x0007,
        SET_FAST_CONNECTABLE = 0x0008,
        SET_PAIRABLE = 0x0009,
        SET_LINK_SECURITY = 0x000A,
        SET_SSP = 0x000B,
        SET_HS = 0x000C,
        SET_LE = 0x000D,
        SET_DEV_CLASS = 0x000E,
        SET_LOCAL_NAME = 0x000F,
        ADD_UUID = 0x0010,
        REMOVE_UUID = 0x0011,
        LOAD_LINK_KEYS = 0x0012,
        LOAD_LONG_TERM_KEYS = 0x0013,
        DISCONNECT = 0x0014,
        GET_CONNECTIONS = 0x0015,
        PIN_CODE_REPLY = 0x0016,
        PIN_CODE_NEG_REPLY = 0x0017,
        SET_IO_CAPABILITY = 0x0018,
        PAIR_DEVICE = 0x0019,
        CANCEL_PAIR_DEVICE = 0x001A,
        UNPAIR_DEVICE = 0x001B,
        USER_CONFIRM_REPLY = 0x001C,
        USER_CONFIRM_NEG_REPLY = 0x001D,
        USER_PASSKEY_REPLY = 0x001E,
        USER_PASSKEY_NEG_REPLY = 0x001F,
        READ_LOCAL_OOB_DATA = 0x0020,
        ADD_REMOTE_OOB_DATA = 0x0021,
        REMOVE_REMOTE_OOB_DATA = 0x0022,
        START_DISCOVERY = 0x0023,
        STOP_DISCOVERY = 0x0024,
        CONFIRM_NAME = 0x0025,
        BLOCK_DEVICE = 0x0026,
        UNBLOCK_DEVICE = 0x0027,
        SET_DEVICE_ID = 0x0028,
        SET_ADVERTISING = 0x0029,
        SET_BREDR = 0x002A,
        SET_STATIC_ADDRESS = 0x002B,
        SET_SCAN_PARAMS = 0x002C,
        SET_SECURE_CONN = 0x002D,
    )

def EventCode(name):
    return Enum(ULInt16(name),
        CMD_COMPLETE = 0x0001,
        CMD_STATUS = 0x0002,
        CONTROLLER_ERROR = 0x0003,
        INDEX_ADDED = 0x0004,
        INDEX_REMOVED = 0x0005,
        NEW_SETTINGS = 0x0006,
        CLASS_OF_DEV_CHANGED = 0x0007,
        LOCAL_NAME_CHANGED = 0x0008,
        NEW_LINK_KEY = 0x0009,
        NEW_LONG_TERM_KEY = 0x000A,
        DEVICE_CONNECTED = 0x000B,
        DEVICE_DISCONNECTED = 0x000C,
        CONNECT_FAILED = 0x000D,
        PIN_CODE_REQUEST = 0x000E,
        USER_CONFIRM_REQUEST = 0x000F,
        USER_PASSKEY_REQUEST = 0x0010,
        AUTH_FAILED = 0x0011,
        DEVICE_FOUND = 0x0012,
        DISCOVERING = 0x0013,
        DEVICE_BLOCKED = 0x0014,
        DEVICE_UNBLOCKED = 0x0015,
        DEVICE_UNPAIRED = 0x0016,
        PASSKEY_NOTIFY = 0x0017,
    )

def AddrInfo(name):
    return Struct(name,
        BdAddr("bdaddr"),
        ULInt8("type"),
    )

mgmt_rp_read_version = Struct("mgmt_rp_read_version",
    ULInt8("version"),
    ULInt16("revision"),
)

mgmt_rp_read_commands = Struct("mgmt_rp_read_commands",
    ULInt16("num_commands"),
    ULInt16("num_events"),
    Array(lambda ctx: ctx.num_commands, CommandCode("cmd_opcodes")),
    Array(lambda ctx: ctx.num_events, EventCode("evt_opcodes")),
)

mgmt_rp_read_index_list = Struct("mgmt_rp_read_index_list",
    ULInt16("num_controllers"),
    Array(lambda ctx: ctx.num_controllers, ULInt16("index")),
)

mgmt_rp_read_info = Struct("mgmt_rp_read_info",
    BdAddr("bdaddr"),
    ULInt8("version"),
    ULInt16("manufacturer"),
    ULInt32("supported_settings"),
    ULInt32("current_settings"),
    Array(3, ULInt8("dev_class")),
    String("name", 249, padchar="\x00"),
    String("short_name", 11, padchar="\x00"),
)

mgmt_cp_set_powered = Struct("mgmt_cp_set_powered",
    ULInt8("enable"),
)

mgmt_rp_set_powered = Struct("mgmt_rp_set_powered",
    ULInt32("current_settings"),
)

mgmt_cp_set_connectable = Struct("mgmt_cp_set_connectable",
    ULInt8("enable"),
)

mgmt_rp_set_connectable = Struct("mgmt_rp_set_connectable",
    ULInt32("current_settings"),
)

mgmt_cp_set_pairable = Struct("mgmt_cp_set_pairable",
    ULInt8("enable"),
)

mgmt_rp_set_pairable = Struct("mgmt_rp_set_pairable",
    ULInt32("current_settings"),
)

mgmt_cp_set_ssp = Struct("mgmt_cp_set_ssp",
    ULInt8("enable"),
)

mgmt_rp_set_ssp = Struct("mgmt_rp_set_ssp",
    ULInt32("current_settings"),
)

mgmt_cp_set_le = Struct("mgmt_cp_set_le",
    ULInt8("enable"),
)

mgmt_rp_set_le = Struct("mgmt_rp_set_le",
    ULInt32("current_settings"),
)

mgmt_cp_set_dev_class = Struct("mgmt_cp_set_dev_class",
    ULInt8("major"),
    ULInt8("minor"),
)

mgmt_rp_set_dev_class = Struct("mgmt_rp_set_dev_class",
    Array(3, ULInt8("dev_class")),
)

mgmt_cp_set_local_name = Struct("mgmt_cp_set_local_name",
    String("name", 249, padchar="\x00"),
    String("short_name", 11, padchar="\x00"),
)

mgmt_rp_set_local_name = Struct("mgmt_rp_set_local_name",
    String("name", 249, padchar="\x00"),
    String("short_name", 11, padchar="\x00"),
)

mgmt_cp_add_uuid = Struct("mgmt_cp_add_uuid",
    BtUuidAdapter(Array(16, ULInt8("uuid"))),
    ULInt8("svc_hint"),
)

mgmt_rp_add_uuid = Struct("mgmt_rp_add_uuid",
    Array(3, ULInt8("dev_class")),
)

mgmt_cp_remove_uuid = Struct("mgmt_cp_remove_uuid",
    BtUuidAdapter(Array(16, ULInt8("uuid"))),
)

mgmt_rp_remove_uuid = Struct("mgmt_rp_remove_uuid",
    Array(3, ULInt8("dev_class")),
)

mgmt_cp_start_discovery = Struct("mgmt_cp_start_discovery",
    ULInt8("type"),
)

mgmt_rp_start_discovery = Struct("mgmt_rp_start_discovery",
    ULInt8("type"),
)

mgmt_cp_stop_discovery = Struct("mgmt_cp_stop_discovery",
    ULInt8("type"),
)

mgmt_rp_stop_discovery = Struct("mgmt_rp_stop_discovery",
    ULInt8("type"),
)

mgmt_cp_unblock_device = Struct("mgmt_cp_unblock_device",
    AddrInfo("addr"),
)

mgmt_rp_unblock_device = Struct("mgmt_rp_unblock_device",
    AddrInfo("addr"),
)

def LinkKeyInfo(name):
    return Struct(name,
        AddrInfo("addr"),
        ULInt8("type"),
        Array(16, ULInt8("val")),
        ULInt8("pin_len"),
    )

mgmt_cp_load_link_keys = Struct("mgmt_cp_load_link_keys",
    ULInt8("debug_keys"),
    ULInt16("key_count"),
    Array(lambda ctx: ctx.key_count, LinkKeyInfo("link_keys")),
)

def LTKInfo(name):
    return Struct(name,
        AddrInfo("addr"),
        ULInt8("authenticated"),
        ULInt8("master"),
        ULInt8("enc_size"),
        ULInt16("ediv"),
        Array(8, ULInt8("rand")),
        Array(16, ULInt8("val")),
    )

mgmt_cp_load_long_term_keys = Struct("mgmt_cp_load_long_term_keys",
    ULInt16("key_count"),
    Array(lambda ctx: ctx.key_count, LinkKeyInfo("ltk_keys")),
)

mgmt_cp_set_device_id = Struct("mgmt_cp_set_device_id",
    ULInt16("source"),
    ULInt16("vendor"),
    ULInt16("product"),
    ULInt16("version"),
)

command = Struct("command",
    CommandCode("opcode"),
    ULInt16("index"),
    TunnelAdapter(PascalString("params", ULInt16("plen")),
        Switch("params", lambda ctx: ctx.opcode,
            {
                "READ_VERSION": Pass,
                "READ_COMMANDS": Pass,
                "READ_INDEX_LIST": Pass,
                "READ_INFO": Pass,
                "SET_POWERED": mgmt_cp_set_powered,
                "SET_CONNECTABLE": mgmt_cp_set_connectable,
                "SET_PAIRABLE": mgmt_cp_set_pairable,
                "SET_SSP": mgmt_cp_set_ssp,
                "SET_LE": mgmt_cp_set_le,
                "SET_DEV_CLASS": mgmt_cp_set_dev_class,
                "SET_LOCAL_NAME": mgmt_cp_set_local_name,
                "ADD_UUID": mgmt_cp_add_uuid,
                "REMOVE_UUID": mgmt_cp_remove_uuid,
                "START_DISCOVERY": mgmt_cp_start_discovery,
                "STOP_DISCOVERY": mgmt_cp_stop_discovery,
                "UNBLOCK_DEVICE": mgmt_cp_unblock_device,
                "LOAD_LINK_KEYS": mgmt_cp_load_link_keys,
                "LOAD_LONG_TERM_KEYS": mgmt_cp_load_long_term_keys,
                "SET_DEVICE_ID": mgmt_cp_set_device_id,
            }
        ),
    ),
)

mgmt_ev_cmd_complete = Struct("mgmt_ev_cmd_complete",
    CommandCode("opcode"),
    ULInt8("status"),
    Switch("rparams", lambda ctx: ctx.opcode,
        {
            "READ_VERSION": mgmt_rp_read_version,
            "READ_COMMANDS": mgmt_rp_read_commands,
            "READ_INDEX_LIST": mgmt_rp_read_index_list,
            "READ_INFO": mgmt_rp_read_info,
            "SET_POWERED": mgmt_rp_set_powered,
            "SET_CONNECTABLE": mgmt_rp_set_connectable,
            "SET_PAIRABLE": mgmt_rp_set_pairable,
            "SET_SSP": mgmt_rp_set_ssp,
            "SET_LE": mgmt_rp_set_le,
            "SET_DEV_CLASS": mgmt_rp_set_dev_class,
            "SET_LOCAL_NAME": mgmt_rp_set_local_name,
            "ADD_UUID": mgmt_rp_add_uuid,
            "REMOVE_UUID": mgmt_rp_remove_uuid,
            "START_DISCOVERY": mgmt_rp_start_discovery,
            "STOP_DISCOVERY": mgmt_rp_stop_discovery,
            "UNBLOCK_DEVICE": mgmt_rp_unblock_device,
            "LOAD_LINK_KEYS": Pass,
            "LOAD_LONG_TERM_KEYS": Pass,
            "SET_DEVICE_ID": Pass,
        }
    ),
)

mgmt_ev_device_found = Struct("mgmt_ev_device_found",
    AddrInfo("addr"),
    SLInt8("rssi"),
    ULInt32("flags"),
    PascalString("eir", ULInt16("eir_len")),
)

event = Struct("event",
    EventCode("opcode"),
    ULInt16("index"),
    TunnelAdapter(PascalString("params", ULInt16("plen")),
        Switch("params", lambda ctx: ctx.opcode,
            {
                "CMD_COMPLETE": mgmt_ev_cmd_complete,
                "DEVICE_FOUND": mgmt_ev_device_found,
            }
        ),
    ),
)
