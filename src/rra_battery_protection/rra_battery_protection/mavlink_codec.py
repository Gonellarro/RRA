"""Small MAVLink v2 codec for the two fixed battery-shutdown messages.

Uses only the MAVROS raw-message fields; does not open another UART or UDP
connection. The CRC extras are from the official common.xml dialect.
"""
from __future__ import annotations

import struct
import math
from dataclasses import dataclass

FRAMING_OK = 1
MAVLINK_V2 = 0xFD
COMMAND_LONG_ID = 76
COMMAND_ACK_ID = 77
CRC_EXTRA = {COMMAND_LONG_ID: 152, COMMAND_ACK_ID: 143}
CMD_SHUTDOWN_REQUEST = 31000  # MAV_CMD_WAYPOINT_USER_1
CMD_COMPANION_PREPARED = 31001  # MAV_CMD_WAYPOINT_USER_2
MAV_RESULT_ACCEPTED = 0
MAV_RESULT_DENIED = 2


@dataclass(frozen=True)
class CommandLong:
    sysid: int
    compid: int
    target_system: int
    target_component: int
    command: int
    params: tuple[float, ...]


def has_expected_endpoints(cmd: CommandLong, *, fcu_system: int,
                           fcu_component: int, companion_system: int,
                           companion_component: int) -> bool:
    return (cmd.command == CMD_SHUTDOWN_REQUEST
            and cmd.sysid == fcu_system and cmd.compid == fcu_component
            and cmd.target_system == companion_system
            and cmd.target_component == companion_component)


def shutdown_values_valid(cmd: CommandLong) -> bool:
    nonce, filtered_v, instant_v = cmd.params[:3]
    return (math.isfinite(nonce) and 1 <= nonce <= 16_777_215
            and abs(nonce - round(nonce)) <= 0.01
            and math.isfinite(filtered_v) and math.isfinite(instant_v)
            and 5.0 <= filtered_v <= 9.0 and 5.0 <= instant_v <= 9.0)


def _crc_accumulate(byte: int, crc: int) -> int:
    tmp = byte ^ (crc & 0xFF)
    tmp = (tmp ^ (tmp << 4)) & 0xFF
    return ((crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)) & 0xFFFF


def x25_checksum(data: bytes, crc_extra: int) -> int:
    crc = 0xFFFF
    for byte in data:
        crc = _crc_accumulate(byte, crc)
    return _crc_accumulate(crc_extra, crc)


def payload_from_ros(msg) -> bytes:
    """Decode the payload64 array in mavros_msgs/Mavlink."""
    raw = b"".join(int(word).to_bytes(8, "little", signed=False) for word in msg.payload64)
    return raw[: int(msg.len)]


def decode_command_long(msg) -> CommandLong | None:
    if int(msg.framing_status) != FRAMING_OK or int(msg.msgid) != COMMAND_LONG_ID:
        return None
    payload = payload_from_ros(msg)
    if len(payload) < 33:
        return None
    fields = struct.unpack_from("<7fHBBB", payload)
    return CommandLong(int(msg.sysid), int(msg.compid), fields[8], fields[9],
                       fields[7], tuple(fields[:7]))


def _ros_frame(node, msgid: int, payload: bytes, crc_extra: int, seq: int,
               sysid: int = 1, compid: int = 191):
    """Create a mavros_msgs/Mavlink v2 frame for publication on mavlink_sink."""
    from mavros_msgs.msg import Mavlink

    msg = Mavlink()
    msg.header.stamp = node.get_clock().now().to_msg()
    msg.framing_status = FRAMING_OK
    msg.magic = MAVLINK_V2
    msg.len = len(payload)
    msg.incompat_flags = 0
    msg.compat_flags = 0
    msg.seq = seq & 0xFF
    msg.sysid = sysid
    msg.compid = compid
    msg.msgid = msgid
    hdr_payload = bytes((msg.len, 0, 0, msg.seq, msg.sysid, msg.compid)) + msgid.to_bytes(3, "little") + payload
    msg.checksum = x25_checksum(hdr_payload, crc_extra)
    padded = payload + bytes((-len(payload)) % 8)
    msg.payload64 = [int.from_bytes(padded[i:i + 8], "little") for i in range(0, len(padded), 8)]
    msg.signature = []
    return msg


def pack_command_long_payload(*, command: int, target_system: int,
                              target_component: int, params: tuple[float, ...]) -> bytes:
    if len(params) != 7:
        raise ValueError("COMMAND_LONG requires seven parameters")
    return struct.pack("<7fHBBB", *params, command, target_system,
                       target_component, 0)


def pack_command_ack_payload(*, command: int, result: int,
                             target_system: int, target_component: int) -> bytes:
    return struct.pack("<HBBiBB", command, result, 100, 0,
                       target_system, target_component)


def make_command_long(node, *, seq: int, command: int, target_system: int,
                      target_component: int, params: tuple[float, ...],
                      source_system: int = 1, source_component: int = 191):
    payload = pack_command_long_payload(command=command,
                                        target_system=target_system,
                                        target_component=target_component,
                                        params=params)
    return _ros_frame(node, COMMAND_LONG_ID, payload, CRC_EXTRA[COMMAND_LONG_ID],
                      seq, source_system, source_component)


def make_command_ack(node, *, seq: int, command: int, result: int,
                     target_system: int, target_component: int,
                     source_system: int = 1, source_component: int = 191):
    # MAVLink 2 extension fields: progress, result_param2, target sys/comp.
    payload = pack_command_ack_payload(command=command, result=result,
                                       target_system=target_system,
                                       target_component=target_component)
    return _ros_frame(node, COMMAND_ACK_ID, payload, CRC_EXTRA[COMMAND_ACK_ID],
                      seq, source_system, source_component)

