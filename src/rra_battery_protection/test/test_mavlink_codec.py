import struct
import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from rra_battery_protection.mavlink_codec import (
    CMD_SHUTDOWN_REQUEST,
    COMMAND_LONG_ID,
    FRAMING_OK,
    decode_command_long,
    has_expected_endpoints,
    make_command_ack,
    pack_command_ack_payload,
    pack_command_long_payload,
    payload_from_ros,
    shutdown_values_valid,
    x25_checksum,
)


def as_ros_message(payload, msgid=COMMAND_LONG_ID, framing=FRAMING_OK):
    padded = payload + bytes((-len(payload)) % 8)
    return SimpleNamespace(
        framing_status=framing,
        msgid=msgid,
        len=len(payload),
        payload64=[int.from_bytes(padded[i:i + 8], "little")
                   for i in range(0, len(padded), 8)],
        sysid=1,
        compid=1,
    )


class MavlinkCodecTests(unittest.TestCase):
    def test_command_long_round_trip(self):
        payload = pack_command_long_payload(
            command=CMD_SHUTDOWN_REQUEST,
            target_system=1,
            target_component=191,
            params=(12345.0, 7.25, 7.18, 1.0, 0.0, 0.0, 0.0),
        )
        decoded = decode_command_long(as_ros_message(payload))
        self.assertEqual(len(payload), 33)
        self.assertEqual(decoded.command, CMD_SHUTDOWN_REQUEST)
        self.assertEqual((decoded.target_system, decoded.target_component), (1, 191))
        self.assertEqual(decoded.params[:2], (12345.0, 7.25))
        self.assertAlmostEqual(decoded.params[2], 7.18, places=5)
        self.assertEqual(decoded.params[3], 1.0)
        self.assertTrue(has_expected_endpoints(
            decoded, fcu_system=1, fcu_component=1,
            companion_system=1, companion_component=191))
        self.assertTrue(shutdown_values_valid(decoded))
        self.assertFalse(has_expected_endpoints(
            decoded, fcu_system=1, fcu_component=1,
            companion_system=1, companion_component=190))

    def test_shutdown_values_reject_invalid_voltage_and_fractional_nonce(self):
        for nonce, filtered_v, instant_v in ((0.0, 7.4, 7.4), (2.5, 7.4, 7.4),
                                             (4.0, 0.0, 7.4), (4.0, 7.4, 9.1)):
            payload = pack_command_long_payload(
                command=CMD_SHUTDOWN_REQUEST, target_system=1, target_component=191,
                params=(nonce, filtered_v, instant_v, 1.0, 0.0, 0.0, 0.0))
            self.assertFalse(shutdown_values_valid(decode_command_long(as_ros_message(payload))))

    def test_rejects_wrong_frame_or_short_payload(self):
        payload = pack_command_long_payload(command=CMD_SHUTDOWN_REQUEST,
                                            target_system=1, target_component=191,
                                            params=(1.0,) * 7)
        self.assertIsNone(decode_command_long(as_ros_message(payload, framing=2)))
        self.assertIsNone(decode_command_long(as_ros_message(payload[:8])))

    def test_x25_is_stable_and_uses_crc_extra(self):
        raw = bytes.fromhex("21 00 00 01 01 4c 00 00 00") + bytes(33)
        self.assertEqual(x25_checksum(raw, 152), 9982)
        self.assertNotEqual(x25_checksum(raw, 152), x25_checksum(raw, 143))

    def test_ack_frame_is_a_v2_raw_mavros_message(self):
        class FakeMavlink:
            def __init__(self):
                self.header = SimpleNamespace(stamp=None)

        msg_pkg = types.ModuleType("mavros_msgs.msg")
        msg_pkg.Mavlink = FakeMavlink
        parent = types.ModuleType("mavros_msgs")
        parent.msg = msg_pkg
        node = SimpleNamespace(get_clock=lambda: SimpleNamespace(
            now=lambda: SimpleNamespace(to_msg=lambda: "stamp")))
        with patch.dict(sys.modules, {"mavros_msgs": parent, "mavros_msgs.msg": msg_pkg}):
            msg = make_command_ack(node, seq=7, command=31000, result=0,
                                   target_system=1, target_component=1)
        expected_payload = pack_command_ack_payload(command=31000, result=0,
                                                     target_system=1, target_component=1)
        self.assertEqual(msg.magic, 0xFD)
        self.assertEqual(msg.msgid, 77)
        self.assertEqual(msg.len, 10)
        self.assertEqual(msg.sysid, 1)
        self.assertEqual(msg.compid, 191)
        self.assertEqual(payload_from_ros(msg), expected_payload)
        crc_input = bytes((10, 0, 0, 7, 1, 191, 77, 0, 0)) + expected_payload
        self.assertEqual(msg.checksum, x25_checksum(crc_input, 143))


if __name__ == "__main__":
    unittest.main()
