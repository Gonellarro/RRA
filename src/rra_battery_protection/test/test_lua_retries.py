"""Exercise the actual Lua retry loop with a mock ArduPilot environment.

Install lupa to run this optional test on a host without an ArduPilot SITL.
"""
import unittest
from pathlib import Path

try:
    from lupa import LuaRuntime
except ImportError:
    LuaRuntime = None


@unittest.skipUnless(LuaRuntime, "lupa is needed to run Lua on this host")
class LuaRetryTests(unittest.TestCase):
    def make_runtime(self, cut_enabled=0):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.globals().test_cut_enabled = cut_enabled
        lua.execute(r'''
now = 0
params = {SERVO12_FUNCTION=-1, RELAY1_FUNCTION=1, RELAY1_PIN=61,
          RELAY1_DEFAULT=0, RELAY1_INVERTED=0}
param = {}
function param:add_table(...) return true end
function param:add_param(key, idx, name, value)
  params['RBP_'..name] = name == 'CUT_EN' and test_cut_enabled or value
  return true
end
function param:get(name) return params[name] end
local ticks = {}
ticks.__index = ticks
function ticks:toint() return self.value end
ticks.__mod = function(a,b) return setmetatable({value=a.value % b},ticks) end
function millis() return setmetatable({value=now},ticks) end
battery = {}
voltage = 7.1
healthy = true
function battery:num_instances() return 1 end
function battery:healthy(idx) return healthy end
function battery:voltage(idx) return voltage end
relay = {on_count=0, off_count=0}
function relay:enabled(instance) return true end
function relay:on(instance) self.on_count=self.on_count+1 end
function relay:off(instance) self.off_count=self.off_count+1 end
gcs = {}
function gcs:send_text(...) end
logger = {}
function logger:write(...) end
local msgs = { HEARTBEAT=0, COMMAND_LONG=76, COMMAND_ACK=77 }
package.preload['MAVLink/mavlink_msgs'] = function()
  return {get_msgid=function(name) return msgs[name] end,
          decode=function(raw,map) return raw end,
          encode=function(name,payload) return msgs[name], payload end}
end
mavlink = {sent=0, max_confirmation=0, queue={}}
function mavlink:init(...) end
function mavlink:register_rx_msgid(...) end
function mavlink:block_command(...) end
function mavlink:receive_chan()
  if #self.queue > 0 then return table.remove(self.queue,1), 1 end
  return nil
end
function mavlink:send_chan(chan,id,payload)
  if id == 76 then
    assert(payload.confirmation >= 0 and payload.confirmation <= 255)
    self.sent = self.sent + 1
    self.max_confirmation = math.max(self.max_confirmation,payload.confirmation)
    self.nonce = payload.param1
  end
  return true
end
table.insert(mavlink.queue,{msgid=0,sysid=1,compid=191})
''')
        script = Path(__file__).resolve().parents[1] / "ardupilot" / "rra_battery_protection.lua"
        update, _ = lua.execute(script.read_text(encoding="utf-8"))
        return lua, update

    def test_retries_beyond_uint8_limit_and_accepts_late_ack(self):
        lua, update = self.make_runtime()
        for tick in range(330):
            lua.globals().now = (tick + 1) * 5000
            update, _ = update()
        mavlink = lua.globals().mavlink
        self.assertGreater(mavlink.sent, 255)
        self.assertEqual(mavlink.max_confirmation, 255)
        lua.execute("table.insert(mavlink.queue,{msgid=77,sysid=1,compid=191,command=31000,result=0})")
        before = mavlink.sent
        for tick in range(5):
            lua.globals().now += 5000
            update, _ = update()
        self.assertEqual(mavlink.sent, before)

    def test_disabled_output_remains_off_after_timeout(self):
        lua, update = self.make_runtime()
        for tick in range(20):
            lua.globals().now = (tick + 1) * 5000
            update, _ = update()
        self.assertEqual(lua.globals().relay.on_count, 0)

    def test_enabled_timeout_pulses_once_even_if_sensor_fails(self):
        lua, update = self.make_runtime(cut_enabled=1)
        for tick in range(3):
            lua.globals().now = (tick + 1) * 5000
            update, _ = update()
        lua.globals().healthy = False
        for tick in range(3, 12):
            lua.globals().now = (tick + 1) * 5000
            update, _ = update()
        self.assertEqual(lua.globals().relay.on_count, 1)
        self.assertEqual(lua.globals().relay.off_count, 1)

    def test_dry_run_ready_blocks_cut_even_after_timeout(self):
        lua, update = self.make_runtime(cut_enabled=1)
        for tick in range(3):
            lua.globals().now = (tick + 1) * 5000
            update, _ = update()
        lua.execute("table.insert(mavlink.queue,{msgid=76,sysid=1,compid=191,command=31001,target_system=1,target_component=1,param1=mavlink.nonce,param2=0})")
        for tick in range(3, 15):
            lua.globals().now = (tick + 1) * 5000
            update, _ = update()
        self.assertEqual(lua.globals().relay.on_count, 0)

    def test_real_ready_waits_for_grace_then_pulses(self):
        lua, update = self.make_runtime(cut_enabled=1)
        for tick in range(3):
            lua.globals().now = (tick + 1) * 5000
            update, _ = update()
        lua.execute("table.insert(mavlink.queue,{msgid=76,sysid=1,compid=191,command=31001,target_system=1,target_component=1,param1=mavlink.nonce,param2=1})")
        lua.globals().now = 16000
        update, _ = update()
        self.assertEqual(lua.globals().relay.on_count, 0)
        lua.globals().now = 20999
        update, _ = update()
        self.assertEqual(lua.globals().relay.on_count, 0)
        lua.globals().now = 21000
        update, _ = update()
        self.assertEqual(lua.globals().relay.on_count, 1)

    def test_incorrect_relay_mapping_blocks_output(self):
        lua, update = self.make_runtime(cut_enabled=1)
        lua.globals().params['RELAY1_PIN'] = 60
        for tick in range(20):
            lua.globals().now = (tick + 1) * 5000
            update, _ = update()
        self.assertEqual(lua.globals().relay.on_count, 0)

    def test_changing_enable_during_runtime_requires_restart(self):
        lua, update = self.make_runtime(cut_enabled=0)
        lua.globals().params['RBP_CUT_EN'] = 1
        for tick in range(20):
            lua.globals().now = (tick + 1) * 5000
            update, _ = update()
        self.assertEqual(lua.globals().relay.on_count, 0)


if __name__ == "__main__":
    unittest.main()
