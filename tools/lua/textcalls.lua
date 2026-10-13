-- Log who calls the glyph lookups (0800A51C = 0x81xx codes, 0800A86C = others) and the text layout
-- routine 0800E990 (r2 = string). One line per distinct (hook, lr) for lookups; every string for layout.
local seen = {}
local function reg(s, n) return s["cpu.r" .. n] end
local function lookup(name)
  return function()
    local s = emu.getState()
    local key = name .. (reg(s, 14) & ~1)
    if not seen[key] then
      seen[key] = true
      L.log(string.format("f%d %s lr=%08X r0=%04X", L.frame, name, reg(s, 14) & ~1, reg(s, 0) & 0xFFFF))
    end
  end
end
L.on_exec(0x0800A51C, 0x0800A51C, lookup("glyph81"))
L.on_exec(0x0800A86C, 0x0800A86C, lookup("glyph"))
L.on_exec(0x0800E990, 0x0800E990, function()
  local s = emu.getState()
  L.log(string.format("f%d layout lr=%08X str=%08X", L.frame, reg(s, 14) & ~1, reg(s, 2)))
end)
