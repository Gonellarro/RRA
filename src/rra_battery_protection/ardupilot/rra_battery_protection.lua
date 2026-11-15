-- RRA electronics battery monitor and Companion orderly-shutdown request.
-- It has NO relay/GPIO/power-cut code. Do not install until the parameter-table
-- key and MAVLink scripting modules have been checked on the exact FCU build.
local TABLE_KEY = 111 -- verify this is unused by every script on the FCU
local PARAM_PREFIX = "RBP_"
assert(param:add_table(TABLE_KEY, PARAM_PREFIX, 12), "RBP parameter table unavailable/conflict")
assert(param:add_param(TABLE_KEY, 1, "WARN_V", 7.4), "RBP WARN_V init failed")
assert(param:add_param(TABLE_KEY, 2, "SHUT_V", 7.3), "RBP SHUT_V init failed")
assert(param:add_param(TABLE_KEY, 3, "URGENT_V", 7.2), "RBP URGENT_V init failed")
assert(param:add_param(TABLE_KEY, 4, "EMERG_V", 7.0), "RBP EMERG_V init failed")
assert(param:add_param(TABLE_KEY, 5, "WARN_S", 10), "RBP WARN_S init failed")
assert(param:add_param(TABLE_KEY, 6, "SHUT_S", 10), "RBP SHUT_S init failed")
assert(param:add_param(TABLE_KEY, 7, "URGENT_S", 5), "RBP URGENT_S init failed")
assert(param:add_param(TABLE_KEY, 8, "EMERG_S", 1), "RBP EMERG_S init failed")
assert(param:add_param(TABLE_KEY, 9, "HYST_V", 0.1), "RBP HYST_V init failed")
assert(param:add_param(TABLE_KEY, 10, "BATT_IDX", 0), "RBP BATT_IDX init failed")
assert(param:add_param(TABLE_KEY, 11, "DEBUG", 0), "RBP DEBUG init failed")
assert(param:add_param(TABLE_KEY, 12, "EMERGEN", 0), "RBP EMERGEN init failed")

local function P(name) return param:get(PARAM_PREFIX .. name) end

local mavlink_msgs = require("MAVLink/mavlink_msgs")
local HEARTBEAT_ID = mavlink_msgs.get_msgid("HEARTBEAT")
local COMMAND_LONG_ID = mavlink_msgs.get_msgid("COMMAND_LONG")
local COMMAND_ACK_ID = mavlink_msgs.get_msgid("COMMAND_ACK")
local rx_map = {
    [HEARTBEAT_ID] = "HEARTBEAT",
    [COMMAND_LONG_ID] = "COMMAND_LONG",
    [COMMAND_ACK_ID] = "COMMAND_ACK",
}
local MAV_CMD_WAYPOINT_USER_1 = 31000 -- shutdown request to component 191
local MAV_CMD_WAYPOINT_USER_2 = 31001 -- Companion PREPARED_TO_POWER_OFF
local MAV_RESULT_ACCEPTED = 0

mavlink:init(20, 3)
mavlink:register_rx_msgid(HEARTBEAT_ID)
mavlink:register_rx_msgid(COMMAND_LONG_ID)
mavlink:register_rx_msgid(COMMAND_ACK_ID)
-- Prevent ArduPilot's regular handler from returning UNSUPPORTED for our
-- application-level READY command. It is still ACKed by this Lua script.
mavlink:block_command(MAV_CMD_WAYPOINT_USER_2)

local ring, short = {}, {}
local ring_n, short_n, position = 20, 5, 0
local ema, last_ms, bad_since = nil, nil, nil
local timers, recovery = {}, {}
local warning_sent, shutdown_sent, sensor_fault_sent = false, false, false
local companion_chan, request_nonce = nil, nil
local request_ack, prepared_ack = false, false
local request_attempts, last_request_ms = 0, 0
local no_ack_reported = false
local missing_companion_reported = false
local prepared_at_ms = nil
local state = "NORMAL"

local function med5()
    local a = {}
    for i=1,#short do a[i]=short[i] end
    table.sort(a)
    return a[math.floor((#a+1)/2)]
end

local function elapsed(now, since, seconds)
    return since ~= nil and (now - since) >= seconds * 1000
end

local function threshold_confirmed(key, value, threshold, duration, now)
    if value <= threshold then
        if timers[key] == nil then timers[key] = now end
    else
        -- Confirmation requires continuous time below the threshold.
        timers[key] = nil
    end
    return elapsed(now, timers[key], duration)
end

local function send_ack(chan, command, target_sysid, target_compid)
    local ack = {
        command = command, result = MAV_RESULT_ACCEPTED,
        progress = 100, result_param2 = 0,
        target_system = 0, target_component = target_compid,
    }
    local id, payload = mavlink_msgs.encode("COMMAND_ACK", ack)
    return mavlink:send_chan(chan, id, payload)
end

local function send_shutdown_request(now, filtered_v, instant_v)
    if shutdown_sent then return end
    if companion_chan == nil then
        state = "COMPANION_LINK_MISSING"
        if not missing_companion_reported then
            gcs:send_text(3, "RRA: baja bateria, sin heartbeat Companion; no se envio apagado")
            missing_companion_reported = true
        end
        return
    end
    missing_companion_reported = false
    request_nonce = (millis() % 16777216):toint()
    if request_nonce == 0 then request_nonce = 1 end
    local request = {
        param1 = request_nonce,
        param2 = filtered_v,
        param3 = instant_v,
        param4 = 1, -- protocol version
        param5 = 0, param6 = 0, param7 = 0,
        command = MAV_CMD_WAYPOINT_USER_1,
        target_system = 1, target_component = 191, confirmation = 0,
    }
    local id, payload = mavlink_msgs.encode("COMMAND_LONG", request)
    local sent = mavlink:send_chan(companion_chan, id, payload)
    if sent then
        shutdown_sent = true
        request_attempts = 1
        last_request_ms = now
        state = "SHUTDOWN_REQUESTED"
        gcs:send_text(4, string.format("RRA: solicitando apagado Companion; %.2fV", filtered_v))
        logger:write("RBP", "Vinst,Vfilt,nonce", "fff", "---", "---", instant_v, filtered_v, request_nonce)
    else
        gcs:send_text(3, "RRA: fallo de envio MAVLink para apagado Companion")
    end
end

local function process_mavlink(now)
    -- Drain a bounded number per scheduler tick; never wait on the UART.
    for _=1,10 do
        local raw, chan = mavlink:receive_chan()
        if raw == nil then break end
        local decoded = mavlink_msgs.decode(raw, rx_map)
        if decoded == nil then
            -- Not a message registered by this script, or unsupported frame.
        elseif decoded.msgid == HEARTBEAT_ID and decoded.sysid == 1 and decoded.compid == 191 then
            companion_chan = chan
        elseif decoded.msgid == COMMAND_ACK_ID and decoded.sysid == 1 and decoded.compid == 191 then
            if shutdown_sent and not request_ack and decoded.command == MAV_CMD_WAYPOINT_USER_1 and decoded.result == MAV_RESULT_ACCEPTED then
                request_ack = true
                gcs:send_text(6, "RRA: Companion recibio la solicitud de apagado")
            end
        elseif decoded.msgid == COMMAND_LONG_ID and decoded.command == MAV_CMD_WAYPOINT_USER_2
                and decoded.sysid == 1 and decoded.compid == 191
                and decoded.target_system == 1 and decoded.target_component == 1
                and request_nonce ~= nil and math.floor(decoded.param1 + 0.5) == request_nonce then
            prepared_ack = true
            prepared_at_ms = now
            send_ack(chan, decoded.command, decoded.sysid, decoded.compid)
            gcs:send_text(6, "RRA: Companion listo; no hay corte fisico instalado")
        end
    end
end

local function update()
    local now = millis():toint()
    process_mavlink(now)
    local dt = last_ms and math.max(1, now-last_ms) or 500
    last_ms = now
    local batt_idx = math.floor(P("BATT_IDX"))
    local voltage = nil
    if battery:num_instances() > batt_idx and battery:healthy(batt_idx) then
        voltage = battery:voltage(batt_idx)
    end
    if voltage == nil or voltage ~= voltage or voltage < 5.0 or voltage > 9.0 then
        timers, recovery = {}, {}
        if bad_since == nil then bad_since = now end
        if elapsed(now, bad_since, 3) and not sensor_fault_sent then
            state = "SENSOR_FAULT"
            sensor_fault_sent = true
            gcs:send_text(3, "RRA: fallo persistente monitor bateria; sin orden de apagado")
        end
        return update, 500
    end
    bad_since, sensor_fault_sent = nil, false

    position = (position % ring_n) + 1
    ring[position] = voltage
    short[#short+1] = voltage
    if #short > short_n then table.remove(short, 1) end
    local med = med5()
    local alpha = 1 - math.exp(-dt / 2000)
    ema = ema and (alpha * med + (1-alpha) * ema) or med
    if P("DEBUG") > 0 then
        logger:write("RBP", "Vinst,Vfilt,N", "ffi", "---", "---", voltage, ema, #ring)
    end

    if not warning_sent and threshold_confirmed("warn", ema, P("WARN_V"), P("WARN_S"), now) then
        warning_sent, state = true, "LOW_VOLTAGE_WARNING"
        gcs:send_text(4, "RRA: BAT ELECTRONICA BAJA - 7.4V")
    elseif warning_sent then
        if ema > P("WARN_V") + P("HYST_V") then
            recovery.warn = recovery.warn or now
            if elapsed(now, recovery.warn, 3) then
                warning_sent, recovery.warn = false, nil
                if not shutdown_sent then state = "NORMAL" end
                gcs:send_text(6, "RRA: tension recuperada; aviso retirado")
            end
        else
            recovery.warn = nil
        end
    end

    if not shutdown_sent and threshold_confirmed("shutdown", ema, P("SHUT_V"), P("SHUT_S"), now) then
        send_shutdown_request(now, ema, voltage)
    end
    -- Fast critical path: if 7.2 V persists for 5 s, request Pi shutdown
    -- immediately even when the 7.3 V/10 s timer has not completed.
    if not shutdown_sent and threshold_confirmed("urgent", ema, P("URGENT_V"), P("URGENT_S"), now) then
        send_shutdown_request(now, ema, voltage)
    end
    if not shutdown_sent and P("EMERGEN") > 0
            and threshold_confirmed("emergency", voltage, P("EMERG_V"), P("EMERG_S"), now) then
        send_shutdown_request(now, ema, voltage)
    end
    if shutdown_sent then
        state = "SHUTDOWN_REQUESTED"
        local retry_interval = request_attempts < 5 and 1000 or 5000
        if not request_ack and request_attempts >= 5 and not no_ack_reported then
            gcs:send_text(3, "RRA: Companion sin ACK; sigue reintentando")
            no_ack_reported = true
        end
        if not request_ack and now-last_request_ms >= retry_interval then
            local retry = {
                param1=request_nonce, param2=ema, param3=voltage, param4=1,
                param5=0, param6=0, param7=0,
                command=MAV_CMD_WAYPOINT_USER_1,
                target_system=1, target_component=191, confirmation=request_attempts,
            }
            local id, payload = mavlink_msgs.encode("COMMAND_LONG", retry)
            last_request_ms = now
            if companion_chan ~= nil and mavlink:send_chan(companion_chan, id, payload) then
                request_attempts = request_attempts + 1
            end
        end
        -- The READY handshake is retained for later Pololu integration. With
        -- no Pololu fitted, this script never switches a GPIO or cuts power.
        if prepared_ack and prepared_at_ms ~= nil and elapsed(now, prepared_at_ms, 5) then
            state = "COMPANION_PREPARED_NO_CUTOFF"
        end
    elseif ema <= P("SHUT_V") then
        state = "SHUTDOWN_PENDING"
    end
    return update, 500
end

gcs:send_text(6, "RRA: monitor bateria Lua iniciado; sin corte")
return update()
