local helper = noctalia.pluginDir() .. "/wallpaper.py"
local busy = false
local pending = false
local lastError = nil
local sync
local reportError
local colorRoles = {
    mPrimary = "primary", mOnPrimary = "on_primary",
    mSecondary = "secondary", mOnSecondary = "on_secondary",
    mTertiary = "tertiary", mOnTertiary = "on_tertiary",
    mError = "error", mOnError = "on_error",
    mSurface = "surface", mOnSurface = "on_surface",
    mSurfaceVariant = "surface_container", mOnSurfaceVariant = "on_surface_variant",
    mOutline = "outline_variant", mShadow = "shadow",
    mHover = "hover", mOnHover = "on_hover",
}

local function syncColors()
    local colors = {}
    for key, role in pairs(colorRoles) do
        local value = noctalia.getColor(role)
        if not value then
            reportError("Noctalia color unavailable: " .. role)
            return
        end
        colors[key] = value
    end
    local payload = noctalia.json.encode(colors)
    if not payload then
        reportError("Could not encode Noctalia colors")
        return
    end
    local accepted = noctalia.runAsync({ "python3", helper, "colors", payload }, function(result)
        if result.exitCode ~= 0 then
            local message = (result.stderr or ""):gsub("%s+$", "")
            reportError(message ~= "" and message or "Color sync failed")
        end
    end, 60000)
    if not accepted then reportError("Could not start color sync") end
end

reportError = function(message)
    if message ~= lastError then
        noctalia.log("SDDM wallpaper sync: " .. message)
        noctalia.notifyError("SDDM Wallpaper", message)
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
        syncColors()
    elseif event == "colors" then
        syncColors()
    end
end

function onOutputsChanged()
    sync()
end

sync()
syncColors()
