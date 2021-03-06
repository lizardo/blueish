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

# Link Control (OGF 0x01)

link_ctl_commands = Enum(BitField("ocf", 10),
    INQUIRY = 0x0001,
    INQUIRY_CANCEL = 0x0002,
    CREATE_CONN = 0x0005,
    DISCONNECT = 0x0006,
    LINK_KEY_REQUEST_NEG_REPLY = 0x000c,
    AUTH_REQUESTED = 0x0011,
    SET_CONN_ENCRYPT = 0x0013,
    REMOTE_NAME_REQ = 0x0019,
    REMOTE_NAME_REQ_CANCEL = 0x001a,
    READ_REMOTE_FEATURES = 0x001b,
    READ_REMOTE_EXT_FEATURES = 0x001c,
    READ_REMOTE_VERSION = 0x001d,
)

inquiry_cp = Struct("inquiry_cp",
    Array(3, ULInt8("lap")),
    ULInt8("length"),
    ULInt8("num_rsp"),
)

inquiry_cancel_rp = Struct("inquiry_cancel_rp",
    ULInt8("status"),
)

create_conn_cp = Struct("create_conn_cp",
    BdAddr("bdaddr"),
    ULInt16("pkt_type"),
    ULInt8("pscan_rep_mode"),
    ULInt8("reserved"),
    ULInt16("clock_offset"),
    ULInt8("role_switch"),
)

disconnect_cp = Struct("disconnect_cp",
    ULInt16("handle"),
    ULInt8("reason"),
)

link_key_request_neg_reply_cp = Struct("link_key_request_neg_reply_cp",
    BdAddr("bdaddr"),
)

link_key_request_neg_reply_rp = Struct("link_key_request_neg_reply_rp",
    ULInt8("status"),
    BdAddr("bdaddr"),
)

auth_requested_cp = Struct("auth_requested_cp",
    ULInt16("handle"),
)

set_conn_encrypt_cp = Struct("set_conn_encrypt_cp",
    ULInt16("handle"),
    ULInt8("encrypt"),
)

remote_name_req_cp = Struct("remote_name_req_cp",
    BdAddr("bdaddr"),
    ULInt8("pscan_rep_mode"),
    ULInt8("reserved"),
    ULInt16("clock_offset"),
)

remote_name_req_cancel_cp = Struct("remote_name_req_cancel_cp",
    BdAddr("bdaddr"),
)

remote_name_req_cancel_rp = Struct("remote_name_req_cancel_rp",
    ULInt8("status"),
    BdAddr("bdaddr"),
)

read_remote_features_cp = Struct("read_remote_features_cp",
    ULInt16("handle"),
)

read_remote_ext_features_cp = Struct("read_remote_ext_features_cp",
    ULInt16("handle"),
    ULInt8("page_num"),
)

read_remote_version_cp = Struct("read_remote_version_cp",
    ULInt16("handle"),
)

# Link Policy (OGF 0x02)

link_policy_commands = Enum(BitField("ocf", 10),
    WRITE_DEFAULT_LINK_POLICY = 0x000f,
)

write_default_link_policy_cp = Struct("write_default_link_policy_cp",
    ULInt16("policy"),
)

write_default_link_policy_rp = Struct("write_default_link_policy_rp",
    ULInt8("status"),
)

# Controller & Baseband (OGF 0x03)

host_ctl_commands = Enum(BitField("ocf", 10),
    SET_EVENT_MASK = 0x0001,
    RESET = 0x0003,
    SET_EVENT_FLT = 0x0005,
    READ_STORED_LINK_KEY = 0x000d,
    DELETE_STORED_LINK_KEY = 0x0012,
    CHANGE_LOCAL_NAME = 0x0013,
    READ_LOCAL_NAME = 0x0014,
    WRITE_CONN_ACCEPT_TIMEOUT = 0x0016,
    WRITE_PAGE_TIMEOUT = 0x0018,
    READ_SCAN_ENABLE = 0x0019,
    WRITE_SCAN_ENABLE = 0x001a,
    READ_PAGE_ACTIVITY = 0x001b,
    READ_CLASS_OF_DEV = 0x0023,
    WRITE_CLASS_OF_DEV = 0x0024,
    READ_VOICE_SETTING = 0x0025,
    READ_NUM_SUPPORTED_IAC = 0x0038,
    READ_CURRENT_IAC_LAP = 0x0039,
    WRITE_INQUIRY_MODE = 0x0045,
    READ_PAGE_SCAN_TYPE = 0x0046,
    WRITE_EXT_INQUIRY_RESPONSE = 0x0052,
    READ_SIMPLE_PAIRING_MODE = 0x0055,
    WRITE_SIMPLE_PAIRING_MODE = 0x0056,
    READ_INQ_RESPONSE_TX_POWER_LEVEL = 0x0058,
    WRITE_LE_HOST_SUPPORTED = 0x006d,
)

set_event_mask_cp = Struct("set_event_mask_cp",
    Array(8, ULInt8("mask")),
)

set_event_mask_rp = Struct("set_event_mask_rp",
    ULInt8("status"),
)

reset_rp = Struct("reset_rp",
    ULInt8("status"),
)

set_event_flt_cp = Struct("set_event_flt_cp",
    Enum(ULInt8("flt_type"),
        CLEAR_ALL = 0x00,
        INQ_RESULT = 0x01,
        CONN_SETUP = 0x02,
    ),
    FixedIf(lambda ctx: ctx.flt_type != "CLEAR_ALL",
        Switch("cond_type", lambda ctx: ctx.flt_type,
            {
                "INQ_RESULT": Enum(ULInt8("cond_type"),
                    RETURN_ALL = 0x00,
                    RETURN_CLASS = 0x01,
                    RETURN_BDADDR = 0x02,
                ),
                "CONN_SETUP": Enum(ULInt8("cond_type"),
                    ALLOW_ALL = 0x00,
                    ALLOW_CLASS = 0x01,
                    ALLOW_BDADDR = 0x02,
                ),
            }
        ),
    ),
    FixedIf(lambda ctx: ctx.flt_type != "CLEAR_ALL",
        Switch("condition", lambda ctx: ctx.cond_type,
            {
                "RETURN_ALL": Pass,
                "RETURN_CLASS": Struct("cond_class",
                    Array(3, ULInt8("dev_class")),
                    Array(3, ULInt8("dev_class_mask")),
                ),
                "RETURN_BDADDR": BdAddr("bdaddr"),
                "ALLOW_ALL": ULInt8("auto_accept_flag"),
                "ALLOW_CLASS": Struct("cond_class",
                    Array(3, ULInt8("dev_class")),
                    Array(3, ULInt8("dev_class_mask")),
                    ULInt8("auto_accept_flag"),
                ),
                "ALLOW_BDADDR": Struct("cond_bdaddr",
                    BdAddr("bdaddr"),
                    ULInt8("auto_accept_flag"),
                ),
            }
        ),
    ),
)

set_event_flt_rp = Struct("set_event_flt_rp",
    ULInt8("status"),
)

read_stored_link_key_cp = Struct("read_stored_link_key_cp",
    BdAddr("bdaddr"),
    ULInt8("read_all"),
)

read_stored_link_key_rp = Struct("read_stored_link_key_rp",
    ULInt8("status"),
    ULInt16("max_keys"),
    ULInt16("num_keys"),
)

delete_stored_link_key_cp = Struct("delete_stored_link_key_cp",
    BdAddr("bdaddr"),
    ULInt8("delete_all"),
)

delete_stored_link_key_rp = Struct("delete_stored_link_key_rp",
    ULInt8("status"),
    ULInt16("num_keys"),
)

HCI_MAX_NAME_LENGTH = 248

change_local_name_cp = Struct("change_local_name_cp",
    String("name", HCI_MAX_NAME_LENGTH, padchar="\x00"),
)

change_local_name_rp = Struct("change_local_name_rp",
    ULInt8("status"),
)

read_local_name_rp = Struct("read_local_name_rp",
    ULInt8("status"),
    String("name", HCI_MAX_NAME_LENGTH, padchar="\x00"),
)

write_conn_accept_timeout_cp = Struct("write_conn_accept_timeout_cp",
    ULInt16("timeout"),
)

write_conn_accept_timeout_rp = Struct("write_conn_accept_timeout_rp",
    ULInt8("status"),
)

write_page_timeout_cp = Struct("write_page_timeout_cp",
    ULInt16("timeout"),
)

write_page_timeout_rp = Struct("write_page_timeout_rp",
    ULInt8("status"),
)

read_scan_enable_rp = Struct("read_scan_enable_rp",
    ULInt8("status"),
    ULInt8("enable"),
)

write_scan_enable_cp = Struct("write_scan_enable_cp",
    ULInt8("enable"),
)

write_scan_enable_rp = Struct("write_scan_enable_rp",
    ULInt8("status"),
)

read_page_activity_rp = Struct("read_page_activity_rp",
    ULInt8("status"),
    ULInt16("interval"),
    ULInt16("window"),
)

read_class_of_dev_rp = Struct("read_class_of_dev_rp",
    ULInt8("status"),
    Array(3, ULInt8("dev_class")),
)

write_class_of_dev_cp = Struct("write_class_of_dev_cp",
    Array(3, ULInt8("dev_class")),
)

write_class_of_dev_rp = Struct("write_class_of_dev_rp",
    ULInt8("status"),
)

read_voice_setting_rp = Struct("read_voice_setting_rp",
    ULInt8("status"),
    ULInt16("voice_setting"),
)

read_num_supported_iac_rp = Struct("read_num_supported_iac_rp",
    ULInt8("status"),
    ULInt8("num_iac"),
)

read_current_iac_lap_rp = Struct("read_current_iac_lap_rp",
    ULInt8("status"),
    ULInt8("num_iac"),
    Bytes("iac_lap", lambda ctx: ctx.num_iac * 3),
)

write_inquiry_mode_cp = Struct("write_inquiry_mode_cp",
    ULInt8("mode"),
)

write_inquiry_mode_rp = Struct("write_inquiry_mode_rp",
    ULInt8("status"),
)

read_page_scan_type_rp = Struct("read_page_scan_type_rp",
    ULInt8("status"),
    ULInt8("type"),
)

HCI_MAX_EIR_LENGTH = 240

write_ext_inquiry_response_cp = Struct("write_ext_inquiry_response_cp",
    ULInt8("fec"),
    Array(HCI_MAX_EIR_LENGTH, ULInt8("data")),
)

write_ext_inquiry_response_rp = Struct("write_ext_inquiry_response_rp",
    ULInt8("status"),
)

read_simple_pairing_mode_rp = Struct("read_simple_pairing_mode_rp",
    ULInt8("status"),
    ULInt8("mode"),
)

write_simple_pairing_mode_cp = Struct("write_simple_pairing_mode_cp",
    ULInt8("mode"),
)

write_simple_pairing_mode_rp = Struct("write_simple_pairing_mode_rp",
    ULInt8("status"),
)

read_inq_response_tx_power_level_rp = Struct("read_inq_response_tx_power_level_rp",
    ULInt8("status"),
    SLInt8("level"),
)

write_le_host_supported_cp = Struct("write_le_host_supported_cp",
    ULInt8("le"),
    ULInt8("simul"),
)

write_le_host_supported_rp = Struct("write_le_host_supported_rp",
    ULInt8("status"),
)

# Informational Parameters (OGF 0x04)

info_param_commands = Enum(BitField("ocf", 10),
    READ_LOCAL_VERSION = 0x0001,
    READ_LOCAL_COMMANDS = 0x0002,
    READ_LOCAL_FEATURES = 0x0003,
    READ_LOCAL_EXT_FEATURES = 0x0004,
    READ_BUFFER_SIZE = 0x0005,
    READ_BD_ADDR = 0x0009,
)

read_local_version_rp = Struct("read_local_version_rp",
    ULInt8("status"),
    ULInt8("hci_ver"),
    ULInt16("hci_rev"),
    ULInt8("lmp_ver"),
    ULInt16("manufacturer"),
    ULInt16("lmp_subver"),
)

read_local_commands_rp = Struct("read_local_commands_rp",
    ULInt8("status"),
    Array(64, ULInt8("commands")),
)

read_local_features_rp = Struct("read_local_features_rp",
    ULInt8("status"),
    Array(8, ULInt8("features")),
)

read_local_ext_features_cp = Struct("read_local_ext_features_cp",
    ULInt8("page_num"),
)

read_local_ext_features_rp = Struct("read_local_ext_features_rp",
    ULInt8("status"),
    ULInt8("page_num"),
    ULInt8("max_page_num"),
    Array(8, ULInt8("features")),
)

read_buffer_size_rp = Struct("read_buffer_size_rp",
    ULInt8("status"),
    ULInt16("acl_mtu"),
    ULInt8("sco_mtu"),
    ULInt16("acl_max_pkt"),
    ULInt16("sco_max_pkt"),
)

read_bd_addr_rp = Struct("read_bd_addr_rp",
    ULInt8("status"),
    BdAddr("bdaddr"),
)

# LE Controller (OGF 0x08)

le_ctl_commands = Enum(BitField("ocf", 10),
    LE_SET_EVENT_MASK = 0x0001,
    LE_READ_BUFFER_SIZE = 0x0002,
    LE_READ_LOCAL_SUPPORTED_FEATURES = 0x0003,
    LE_READ_ADVERTISING_CHANNEL_TX_POWER = 0x0007,
    LE_SET_ADVERTISING_DATA = 0x0008,
    LE_SET_SCAN_RSP_DATA = 0x0009,
    LE_SET_SCAN_PARAMETERS = 0x000b,
    LE_SET_SCAN_ENABLE = 0x000c,
    LE_CREATE_CONN = 0x000d,
    LE_READ_WHITE_LIST_SIZE = 0x000f,
    LE_READ_SUPPORTED_STATES = 0x001c,
)

le_set_event_mask_cp = Struct("le_set_event_mask_cp",
    Array(8, ULInt8("mask")),
)

le_set_event_mask_rp = Struct("le_set_event_mask_rp",
    ULInt8("status"),
)

le_read_buffer_size_rp = Struct("le_read_buffer_size_rp",
    ULInt8("status"),
    ULInt16("pkt_len"),
    ULInt8("max_pkt"),
)

le_read_local_supported_features_rp = Struct("le_read_local_supported_features_rp",
    ULInt8("status"),
    Array(8, ULInt8("features")),
)

le_read_advertising_channel_tx_power_rp = Struct("le_read_advertising_channel_tx_power_rp",
    ULInt8("status"),
    SLInt8("level"),
)

le_set_advertising_data_cp = Struct("le_set_advertising_data_cp",
    ULInt8("length"),
    Array(31, ULInt8("data")),
)

le_set_advertising_data_rp = Struct("le_set_advertising_data_rp",
    ULInt8("status"),
)

le_set_scan_rsp_data_cp = Struct("le_set_scan_rsp_data_cp",
    ULInt8("length"),
    Array(31, ULInt8("data")),
)

le_set_scan_rsp_data_rp = Struct("le_set_scan_rsp_data_rp",
    ULInt8("status"),
)

le_set_scan_parameters_cp = Struct("le_set_scan_parameters_cp",
    ULInt8("type"),
    ULInt16("interval"),
    ULInt16("window"),
    ULInt8("own_bdaddr_type"),
    ULInt8("filter"),
)

le_set_scan_parameters_rp = Struct("le_set_scan_parameters_rp",
    ULInt8("status"),
)

le_set_scan_enable_cp = Struct("le_set_scan_enable_cp",
    ULInt8("enable"),
    ULInt8("filter_dup"),
)

le_set_scan_enable_rp = Struct("le_set_scan_enable_rp",
    ULInt8("status"),
)

le_create_conn_cp = Struct("le_create_conn_cp",
    ULInt16("scan_interval"),
    ULInt16("scan_window"),
    ULInt8("filter_policy"),
    ULInt8("peer_addr_type"),
    BdAddr("peer_addr"),
    ULInt8("own_addr_type"),
    ULInt16("min_interval"),
    ULInt16("max_interval"),
    ULInt16("latency"),
    ULInt16("supv_timeout"),
    ULInt16("min_length"),
    ULInt16("max_length"),
)

le_read_white_list_size_rp = Struct("le_read_white_list_size_rp",
    ULInt8("status"),
    ULInt8("size"),
)

le_read_supported_states_rp = Struct("le_read_supported_states_rp",
    ULInt8("status"),
    Array(8, ULInt8("states")),
)

# Commands

Opcode = TunnelAdapter(
    SwapAdapter(Bytes("opcode", 2)),
    EmbeddedBitStruct(
        Enum(BitField("ogf", 6),
            LINK_CTL = 0x01,
            LINK_POLICY = 0x02,
            HOST_CTL = 0x03,
            INFO_PARAM = 0x04,
            STATUS_PARAM = 0x05,
            LE_CTL = 0x08,
        ),
        Switch("ocf", lambda ctx: ctx.ogf,
            {
                "LINK_CTL": link_ctl_commands,
                "LINK_POLICY": link_policy_commands,
                "HOST_CTL": host_ctl_commands,
                "INFO_PARAM": info_param_commands,
                "LE_CTL": le_ctl_commands,
            }
        ),
    )
)

command = Struct("command",
    Opcode,
    TunnelAdapter(PascalString("params", ULInt8("plen")),
        Switch("params", lambda ctx: ctx.opcode.ocf,
            {
                # Link Control (OGF 0x01)
                "INQUIRY": inquiry_cp,
                "INQUIRY_CANCEL": Pass,
                "CREATE_CONN": create_conn_cp,
                "DISCONNECT": disconnect_cp,
                "LINK_KEY_REQUEST_NEG_REPLY": link_key_request_neg_reply_cp,
                "AUTH_REQUESTED": auth_requested_cp,
                "SET_CONN_ENCRYPT": set_conn_encrypt_cp,
                "REMOTE_NAME_REQ": remote_name_req_cp,
                "REMOTE_NAME_REQ_CANCEL": remote_name_req_cancel_cp,
                "READ_REMOTE_FEATURES": read_remote_features_cp,
                "READ_REMOTE_EXT_FEATURES": read_remote_ext_features_cp,
                "READ_REMOTE_VERSION": read_remote_version_cp,
                # Link Policy (OGF 0x02)
                "WRITE_DEFAULT_LINK_POLICY": write_default_link_policy_cp,
                # Controller & Baseband (OGF 0x03)
                "SET_EVENT_MASK": set_event_mask_cp,
                "RESET": Pass,
                "SET_EVENT_FLT": set_event_flt_cp,
                "READ_STORED_LINK_KEY": read_stored_link_key_cp,
                "DELETE_STORED_LINK_KEY": delete_stored_link_key_cp,
                "CHANGE_LOCAL_NAME": change_local_name_cp,
                "READ_LOCAL_NAME": Pass,
                "WRITE_CONN_ACCEPT_TIMEOUT": write_conn_accept_timeout_cp,
                "WRITE_PAGE_TIMEOUT": write_page_timeout_cp,
                "READ_SCAN_ENABLE": Pass,
                "WRITE_SCAN_ENABLE": write_scan_enable_cp,
                "READ_PAGE_ACTIVITY": Pass,
                "READ_CLASS_OF_DEV": Pass,
                "WRITE_CLASS_OF_DEV": write_class_of_dev_cp,
                "READ_VOICE_SETTING": Pass,
                "READ_NUM_SUPPORTED_IAC": Pass,
                "READ_CURRENT_IAC_LAP": Pass,
                "WRITE_INQUIRY_MODE": write_inquiry_mode_cp,
                "READ_PAGE_SCAN_TYPE": Pass,
                "WRITE_EXT_INQUIRY_RESPONSE": write_ext_inquiry_response_cp,
                "READ_SIMPLE_PAIRING_MODE": Pass,
                "WRITE_SIMPLE_PAIRING_MODE": write_simple_pairing_mode_cp,
                "READ_INQ_RESPONSE_TX_POWER_LEVEL": Pass,
                "WRITE_LE_HOST_SUPPORTED": write_le_host_supported_cp,
                # Informational Parameters (OGF 0x04)
                "READ_LOCAL_VERSION": Pass,
                "READ_LOCAL_COMMANDS": Pass,
                "READ_LOCAL_FEATURES": Pass,
                "READ_LOCAL_EXT_FEATURES": read_local_ext_features_cp,
                "READ_BUFFER_SIZE": Pass,
                "READ_BD_ADDR": Pass,
                # LE Controller (OGF 0x08)
                "LE_SET_EVENT_MASK": le_set_event_mask_cp,
                "LE_READ_BUFFER_SIZE": Pass,
                "LE_READ_LOCAL_SUPPORTED_FEATURES": Pass,
                "LE_READ_ADVERTISING_CHANNEL_TX_POWER": Pass,
                "LE_SET_ADVERTISING_DATA": le_set_advertising_data_cp,
                "LE_SET_SCAN_RSP_DATA": le_set_scan_rsp_data_cp,
                "LE_SET_SCAN_PARAMETERS": le_set_scan_parameters_cp,
                "LE_SET_SCAN_ENABLE": le_set_scan_enable_cp,
                "LE_CREATE_CONN": le_create_conn_cp,
                "LE_READ_WHITE_LIST_SIZE": Pass,
                "LE_READ_SUPPORTED_STATES": Pass,
            }
        ),
    ),
)

# Events

evt_inquiry_complete = Struct("evt_inquiry_complete",
    ULInt8("status"),
)

# FIXME: allow multiple responses
evt_inquiry_result = Struct("evt_inquiry_result",
    ULInt8("num_rsp"),
    BdAddr("bdaddr"),
    ULInt8("pscan_rep_mode"),
    ULInt8("reserved1"),
    ULInt8("reserved2"),
    Array(3, ULInt8("dev_class")),
    ULInt16("clock_offset"),
)

evt_conn_complete = Struct("evt_conn_complete",
    ULInt8("status"),
    ULInt16("handle"),
    BdAddr("bdaddr"),
    ULInt8("link_type"),
    ULInt8("encr_mode"),
)

evt_disconn_complete = Struct("evt_disconn_complete",
    ULInt8("status"),
    ULInt16("handle"),
    ULInt8("reason"),
)

evt_auth_complete = Struct("evt_auth_complete",
    ULInt8("status"),
    ULInt16("handle"),
)

evt_remote_name_req_complete = Struct("evt_remote_name_req_complete",
    ULInt8("status"),
    BdAddr("bdaddr"),
    String("name", HCI_MAX_NAME_LENGTH, padchar="\x00"),
)

evt_encrypt_change = Struct("evt_encrypt_change",
    ULInt8("status"),
    ULInt16("handle"),
    ULInt8("encrypt"),
)

evt_read_remote_features_complete = Struct("evt_read_remote_features_complete",
    ULInt8("status"),
    ULInt16("handle"),
    Array(8, ULInt8("features")),
)

evt_read_remote_version_complete = Struct("evt_read_remote_version_complete",
    ULInt8("status"),
    ULInt16("handle"),
    ULInt8("lmp_ver"),
    ULInt16("manufacturer"),
    ULInt16("lmp_subver"),
)

evt_cmd_complete = Struct("evt_cmd_complete",
    ULInt8("ncmd"),
    Opcode,
    FixedSwitch("rparams", lambda ctx: ctx.opcode.ocf,
        {
            # Link Control (OGF 0x01)
            "INQUIRY_CANCEL": inquiry_cancel_rp,
            "LINK_KEY_REQUEST_NEG_REPLY": link_key_request_neg_reply_rp,
            "REMOTE_NAME_REQ_CANCEL": remote_name_req_cancel_rp,
            # Link Policy (OGF 0x02)
            "WRITE_DEFAULT_LINK_POLICY": write_default_link_policy_rp,
            # Controller & Baseband (OGF 0x03)
            "SET_EVENT_MASK": set_event_mask_rp,
            "RESET": reset_rp,
            "SET_EVENT_FLT": set_event_flt_rp,
            "READ_STORED_LINK_KEY": read_stored_link_key_rp,
            "DELETE_STORED_LINK_KEY": delete_stored_link_key_rp,
            "CHANGE_LOCAL_NAME": change_local_name_rp,
            "READ_LOCAL_NAME": read_local_name_rp,
            "WRITE_CONN_ACCEPT_TIMEOUT": write_conn_accept_timeout_rp,
            "WRITE_PAGE_TIMEOUT": write_page_timeout_rp,
            "READ_SCAN_ENABLE": read_scan_enable_rp,
            "WRITE_SCAN_ENABLE": write_scan_enable_rp,
            "READ_PAGE_ACTIVITY": read_page_activity_rp,
            "READ_CLASS_OF_DEV": read_class_of_dev_rp,
            "WRITE_CLASS_OF_DEV": write_class_of_dev_rp,
            "READ_VOICE_SETTING": read_voice_setting_rp,
            "READ_NUM_SUPPORTED_IAC": read_num_supported_iac_rp,
            "READ_CURRENT_IAC_LAP": read_current_iac_lap_rp,
            "WRITE_INQUIRY_MODE": write_inquiry_mode_rp,
            "READ_PAGE_SCAN_TYPE": read_page_scan_type_rp,
            "WRITE_EXT_INQUIRY_RESPONSE": write_ext_inquiry_response_rp,
            "READ_SIMPLE_PAIRING_MODE": read_simple_pairing_mode_rp,
            "WRITE_SIMPLE_PAIRING_MODE": write_simple_pairing_mode_rp,
            "READ_INQ_RESPONSE_TX_POWER_LEVEL": read_inq_response_tx_power_level_rp,
            "WRITE_LE_HOST_SUPPORTED": write_le_host_supported_rp,
            # Informational Parameters (OGF 0x04)
            "READ_LOCAL_VERSION": read_local_version_rp,
            "READ_LOCAL_COMMANDS": read_local_commands_rp,
            "READ_LOCAL_FEATURES": read_local_features_rp,
            "READ_LOCAL_EXT_FEATURES": read_local_ext_features_rp,
            "READ_BUFFER_SIZE": read_buffer_size_rp,
            "READ_BD_ADDR": read_bd_addr_rp,
            # LE Controller (OGF 0x08)
            "LE_SET_EVENT_MASK": le_set_event_mask_rp,
            "LE_READ_BUFFER_SIZE": le_read_buffer_size_rp,
            "LE_READ_LOCAL_SUPPORTED_FEATURES": le_read_local_supported_features_rp,
            "LE_READ_ADVERTISING_CHANNEL_TX_POWER": le_read_advertising_channel_tx_power_rp,
            "LE_SET_ADVERTISING_DATA": le_set_advertising_data_rp,
            "LE_SET_SCAN_RSP_DATA": le_set_scan_rsp_data_rp,
            "LE_SET_SCAN_PARAMETERS": le_set_scan_parameters_rp,
            "LE_SET_SCAN_ENABLE": le_set_scan_enable_rp,
            "LE_READ_WHITE_LIST_SIZE": le_read_white_list_size_rp,
            "LE_READ_SUPPORTED_STATES": le_read_supported_states_rp,
        }
    ),
)

evt_cmd_status = Struct("evt_cmd_status",
    ULInt8("status"),
    ULInt8("ncmd"),
    Opcode,
)

evt_num_comp_pkts = Struct("evt_num_comp_pkts",
    ULInt8("num_handles"),
    ULInt16("handle"),
    ULInt16("count"),
)

evt_link_key_request = Struct("evt_link_key_request",
    BdAddr("bdaddr"),
)

evt_read_remote_ext_features_complete = Struct("evt_read_remote_ext_features_complete",
    ULInt8("status"),
    ULInt16("handle"),
    ULInt8("page_num"),
    ULInt8("max_page_num"),
    Array(8, ULInt8("features")),
)

evt_extended_inquiry_result = Struct("evt_extended_inquiry_result",
    ULInt8("num_rsp"),
    BdAddr("bdaddr"),
    ULInt8("pscan_rep_mode"),
    ULInt8("reserved"),
    Array(3, ULInt8("dev_class")),
    ULInt16("clock_offset"),
    SLInt8("rssi"),
    Array(HCI_MAX_EIR_LENGTH, ULInt8("data")),
)

evt_le_conn_complete = Struct("evt_le_conn_complete",
    ULInt8("status"),
    ULInt16("handle"),
    ULInt8("role"),
    ULInt8("peer_addr_type"),
    BdAddr("peer_addr"),
    ULInt16("interval"),
    ULInt16("latency"),
    ULInt16("supv_timeout"),
    ULInt8("clock_accuracy"),
)

evt_le_adv_report = Struct("evt_le_adv_report",
    ULInt8("num_reports"),
    # FIXME: implement support for multiple reports
    Enum(ULInt8("event_type"),
        ADV_IND = 0x00,
    ),
    Enum(ULInt8("addr_type"),
        ADDR_LE_DEV_PUBLIC = 0x00,
    ),
    BdAddr("addr"),
    PascalString("data"),
    SLInt8("rssi"),
)

evt_le_meta_event = Struct("evt_le_meta_event",
    Enum(ULInt8("subevent"),
        LE_CONN_COMPLETE = 0x01,
        LE_ADVERTISING_REPORT = 0x02,
    ),
    Switch("rparams", lambda ctx: ctx.subevent,
        {
            "LE_CONN_COMPLETE": evt_le_conn_complete,
            "LE_ADVERTISING_REPORT": evt_le_adv_report,
        }
    ),
)

event = Struct("event",
    Enum(ULInt8("evt"),
        INQUIRY_COMPLETE = 0x01,
        INQUIRY_RESULT = 0x02,
        CONN_COMPLETE = 0x03,
        DISCONN_COMPLETE = 0x05,
        AUTH_COMPLETE = 0x06,
        REMOTE_NAME_REQ_COMPLETE = 0x07,
        ENCRYPT_CHANGE = 0x08,
        READ_REMOTE_FEATURES_COMPLETE = 0x0b,
        READ_REMOTE_VERSION_COMPLETE = 0x0c,
        CMD_COMPLETE = 0x0e,
        CMD_STATUS = 0x0f,
        NUM_COMP_PKTS = 0x13,
        LINK_KEY_REQUEST = 0x17,
        READ_REMOTE_EXT_FEATURES_COMPLETE = 0x23,
        EXTENDED_INQUIRY_RESULT = 0x2f,
        LE_META_EVENT = 0x3e,
    ),
    TunnelAdapter(PascalString("params", ULInt8("plen")),
        Switch("params", lambda ctx: ctx.evt,
            {
                "INQUIRY_COMPLETE": evt_inquiry_complete,
                "INQUIRY_RESULT": evt_inquiry_result,
                "CONN_COMPLETE": evt_conn_complete,
                "DISCONN_COMPLETE": evt_disconn_complete,
                "AUTH_COMPLETE": evt_auth_complete,
                "REMOTE_NAME_REQ_COMPLETE": evt_remote_name_req_complete,
                "ENCRYPT_CHANGE": evt_encrypt_change,
                "READ_REMOTE_FEATURES_COMPLETE": evt_read_remote_features_complete,
                "READ_REMOTE_VERSION_COMPLETE": evt_read_remote_version_complete,
                "CMD_COMPLETE": evt_cmd_complete,
                "CMD_STATUS": evt_cmd_status,
                "NUM_COMP_PKTS": evt_num_comp_pkts,
                "LINK_KEY_REQUEST": evt_link_key_request,
                "READ_REMOTE_EXT_FEATURES_COMPLETE": evt_read_remote_ext_features_complete,
                "EXTENDED_INQUIRY_RESULT": evt_extended_inquiry_result,
                "LE_META_EVENT": evt_le_meta_event,
            }
        ),
    ),
)
