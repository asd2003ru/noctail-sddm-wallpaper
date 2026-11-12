local panelId = "noctail/sddm-wallpaper:wallpaper"

function onQuery(text)
    local query = string.lower(text)
    local names = { "sddm", "wallpaper", "login", "background", "обои", "Обои", "экран входа", "Экран входа" }
    local matches = query == ""
    for _, name in ipairs(names) do
        if string.find(name, query, 1, true) or string.find(query, name, 1, true) then
            matches = true
            break
        end
    end

    if matches then
        launcher.setResults(text, {
            { id = "open", title = "SDDM Wallpaper", subtitle = "Open wallpaper settings for the login screen", glyph = "photo" },
        })
    else
        launcher.setResults(text, {})
    end
end

function onActivate(id)
    if id == "open" then
        noctalia.togglePanel(panelId)
    end
end
