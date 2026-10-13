-- Log every string handed to a text renderer: "f<frame> <kind> lr=<caller> str=<ptr>".
--   dlg  = 0800E990(x, y, str)   per-glyph dialogue layout (7 call sites)
--   menu = 0800E4FC(str, out)    menu label layout
--   dbg  = 08008C0C(.., .., str) debug-screen BG text
-- Map str back to a script id offline (original ROM: id = str - 0x08000000). Repeats of the same
-- (kind, lr, str) are logged once.
local seen = {}
local function hook(addr, kind, reg)
  L.on_exec(addr, addr, function()
    local s = emu.getState()
    local lr, p = s["cpu.r14"] & ~1, s["cpu.r" .. reg]
    local key = kind .. lr .. ":" .. p
    if not seen[key] then
      seen[key] = true
      L.log(string.format("f%d %s lr=%08X str=%08X", L.frame, kind, lr, p))
    end
  end)
end
hook(0x0800E990, "dlg", 2)
hook(0x0800E4FC, "menu", 0)
hook(0x08008C0C, "dbg", 2)
