-- Print Mesen GBA state keys once (to learn register names).
L.on_frame(function(n)
  if n == 60 then
    local s, k = emu.getState(), {}
    for key, v in pairs(s) do if key:match("^cpu") then k[#k + 1] = key .. "=" .. tostring(v) end end
    table.sort(k)
    L.log(table.concat(k, "\n"))
  end
end)
