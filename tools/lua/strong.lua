-- QA cheat: party (5 records of 0x14 bytes at 0x02035358: HP, maxHP, ATK, SPD, DEF as u16) gets ATK 250 and
-- full HP every frame, so battles end in a turn or two during story tours.
local base = 0x02035358
local function w16(a, v)
  emu.write(a, v & 0xFF, emu.memType.gbaMemory)
  emu.write(a + 1, (v >> 8) & 0xFF, emu.memType.gbaMemory)
end
local function r16(a)
  return emu.read(a, emu.memType.gbaMemory) | (emu.read(a + 1, emu.memType.gbaMemory) << 8)
end
L.on_frame(function()
  for k = 0, 4 do
    local a = base + 0x14 * k
    local maxhp = r16(a + 2)
    if maxhp > 0 and maxhp < 1000 then
      w16(a, maxhp)
      w16(a + 4, 250)
    end
  end
end)
