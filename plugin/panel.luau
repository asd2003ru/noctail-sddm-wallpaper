local helper = noctalia.pluginDir() .. "/wallpaper.py"
local status = { mode = "sync", connector = "", installed = false, image = "" }
local errorMessage = ""
local busy = false

local function commandError(result, fallback)
    if result.timedOut then
        return "Image update timed out after 60 seconds"
    end
    local detail = (result.stderr or ""):gsub("^%s+", ""):gsub("%s+$", "")
    if detail ~= "" then
        return detail
    end
    return fallback .. " (exit code " .. tostring(result.exitCode or "unknown") .. ")"
end

local function showError(message)
    errorMessage = message and message ~= "" and message or "Unknown SDDM wallpaper error"
    noctalia.notifyError("SDDM Wallpaper", errorMessage)
    update()
end

local function refresh()
    local accepted = noctalia.runAsync({ "python3", helper, "status" }, function(result)
        if result.exitCode == 0 then
            local ok, decoded = pcall(noctalia.json.decode, result.stdout)
            if ok and type(decoded) == "table" then
                status = decoded
            end
        else
            showError(commandError(result, "Could not read status"))
            return
        end
        update()
    end)
    if not accepted then
        showError("Could not start status helper")
    end
end

local function run(args, after)
    if busy then return end
    busy = true
    errorMessage = ""
    update()
    local command = { "python3", helper }
    for _, arg in ipairs(args) do table.insert(command, arg) end
    local accepted = noctalia.runAsync(command, function(result)
        busy = false
        if result.exitCode ~= 0 then
            showError(commandError(result, "Image update failed"))
            return
        end
        refresh()
        if after then after() end
    end, 60000)
    if not accepted then
        busy = false
        showError("Could not start image helper")
    end
end

function chooseImage()
    if busy then return end
    local accepted = noctalia.runAsync({ "zenity", "--file-selection", "--title=Choose SDDM wallpaper", "--file-filter=Images | *.png *.jpg *.jpeg *.webp *.bmp *.avif", "--file-filter=All files | *" }, function(result)
        if result.exitCode == 0 then
            local path = (result.stdout or ""):gsub("\r?\n$", "")
            if path ~= "" then run({ "manual", path }) end
        elseif result.exitCode ~= 1 then
            showError(commandError(result, "File chooser failed"))
        end
    end, 60000)
    if not accepted then
        showError("Could not open file chooser")
    end
end

function enableSync()
    local connector = status.connector ~= "" and status.connector or noctalia.focusedOutputName()
    local source = connector and noctalia.wallpaperPath(connector) or nil
    if not source or source == "" then
        showError("No wallpaper available for the selected output")
        return
    end
    run({ "mode", "sync", connector, source })
end

function selectOutput(name)
    local source = noctalia.wallpaperPath(name)
    if not source or source == "" then
        showError("No wallpaper available for " .. name)
        return
    end
    run({ "connector", name, source })
end

function onOpen()
    refresh()
end

function update()
    local connector = status.connector ~= "" and status.connector or noctalia.focusedOutputName()
    local current = connector and noctalia.wallpaperPath(connector) or nil
    local currentName = current and string.match(current, "[^/]+$") or "unavailable"
    local copiedName = status.image ~= "" and string.match(status.image, "[^/]+$") or "none"
    local children = {
        ui.label({ text = "SDDM wallpaper", fontSize = 20, fontWeight = "bold" }),
        ui.label({ text = status.installed and "Integration installed" or "Run scripts/install.sh to enable SDDM updates", color = status.installed and "on_surface" or "error" }),
        ui.row({ gap = 8 }, {
            ui.button({ text = "Sync with Noctalia", variant = status.mode == "sync" and "primary" or "default", enabled = not busy and status.installed, onClick = enableSync }),
            ui.button({ text = "Choose image…", variant = status.mode == "manual" and "primary" or "default", enabled = not busy and status.installed, onClick = chooseImage }),
        }),
        ui.label({ text = "Source monitor: " .. (status.connector ~= "" and status.connector or "current focused monitor") }),
        ui.label({ text = "Noctalia: " .. currentName, maxLines = 1 }),
        ui.label({ text = "SDDM: " .. copiedName, maxLines = 1 }),
    }

    if errorMessage ~= "" then
        table.insert(children, ui.label({ text = errorMessage, color = "error", maxLines = 3 }))
    end

    local outputs = {}
    for _, output in ipairs(noctalia.outputs()) do
        local name = output.name
        table.insert(outputs, ui.button({ text = name, selected = status.connector == name, enabled = not busy and status.installed, onClick = function() selectOutput(name) end }))
    end
    table.insert(children, ui.row({ gap = 8 }, outputs))
    if errorMessage == "" and status.image and status.image ~= "" then
        table.insert(children, ui.image({ path = status.image, width = 350, height = 120, fit = "cover", radius = 8 }))
    end
    if busy then table.insert(children, ui.label({ text = "Updating…" })) end
    panel.render(ui.column({ gap = 12, padding = 16 }, children))
end

refresh()
