-- Enter the built-in debug menu (mode_debug, struct 0x085D4CF8: MAIN/OBJECT/SOUND/MAP/BATTLE/EVENT/EVENT TEST/
-- FLAG/FONT) by writing the game's next-mode variables at frame DEBUG_AT (default 1300 = title screen).
local at = DEBUG_AT or 1300
local function w32(a, v)
  for i = 0, 3 do emu.write(a + i, (v >> (8 * i)) & 0xFF, emu.memType.gbaMemory) end
end
L.on_frame(function(n)
  if n == at then
    w32(0x03007494, 0x085D4CF8)
    w32(0x03007498, 1)
    L.log("debug menu requested at frame " .. n)
  end
end)
