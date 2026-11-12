local helper = noctalia.pluginDir() .. "/wallpaper.py"
local busy = false
local pending = false
local lastError = nil
local sync

local function reportError(message)
    if message ~= lastError then
        noctalia.log("SDDM wallpaper sync: " .. message)
        if string.find(message, "PNG is not supported", 1, true) then
            noctalia.notifyError("SDDM Wallpaper", message)
        end
        lastError = message
    end
end

local function finish()
    busy = false
    if pending then
        pending = false
        sync()
    end
end

sync = function()
    if busy then
        pending = true
        return
    end
    busy = true
    local accepted = noctalia.runAsync({ "python3", helper, "status" }, function(statusResult)
        if statusResult.exitCode ~= 0 then
            reportError(statusResult.stderr or "could not read state")
            finish()
            return
        end
        local state, decodeError = noctalia.json.decode(statusResult.stdout)
        if not state then
            reportError(decodeError or "invalid state")
            finish()
            return
        end
        if state.mode == "manual" then
            lastError = nil
            finish()
            return
        end
        local connector = state.connector ~= "" and state.connector or noctalia.focusedOutputName()
        local source = connector and noctalia.wallpaperPath(connector) or nil
        if not source or source == "" then
            reportError("no wallpaper available for output " .. (connector or "unknown"))
            finish()
            return
        end
        local copyAccepted = noctalia.runAsync({ "python3", helper, "sync-source", connector, source }, function(result)
            if result.exitCode ~= 0 then
                local message = (result.stderr or ""):gsub("^%s+", ""):gsub("%s+$", "")
                if message == "" then
                    message = result.timedOut and "image update timed out" or ("image helper failed with exit code " .. tostring(result.exitCode or "unknown"))
                end
                reportError(message)
            else
                lastError = nil
            end
            finish()
        end, 60000)
        if not copyAccepted then
            reportError("could not start image helper")
            finish()
        end
    end)
    if not accepted then
        busy = false
        reportError("could not read state")
    end
end

function onIpc(event, _payload)
    if event == "sync" then
        sync()
    end
end

function onOutputsChanged()
    sync()
end

sync()
