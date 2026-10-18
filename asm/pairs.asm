; English pair glyphs (docs/re/font.md). A text cell whose first byte is < 0x80 is two ASCII letters drawn as one
; 16x16 OBJ glyph pre-rendered by tools/build.py; the layout routines advance by the pair's pixel width instead
; of the fixed 12 px. Assembled onto the built ROM by tools/build.py.
;   PAIR_TAB  u16[96*128]: glyph number for cell (a, b) at (a-0x20)*128 + b; 0 = missing (glyph 0 = '?')
;   PAIR_GFX  128 bytes per glyph (tiles TL, TR, BL, BR)
;   WIDTHS    u8[128]: advance per ASCII byte

.gba
.open BUILD_ROM, 0x08000000
.thumb

WRAP_EXTRA equ 20

; ---- glyph lookup 0800A86C(code, u16 *idx, u8 *page): ASCII first byte -> page 3, idx = code
.org 0x0800A86C
  ldr r3,=lookup_hook|1
  bx r3
  .pool

; ---- glyph upload 0800A780(page, idx) -> OBJ handle: page 3 -> our pair glyph
.org 0x0800A780
  ldr r3,=upload_hook|1
  bx r3
  .pool

; ---- dialogue layout 0800E990: per-cell advance (was sl += 0xC00)
.org 0x0800EA80
  ldr r0,=dlg_advance|1
  bx r0
  .pool
  nop

; ---- dialogue auto-wrap limit: every cell gets the (width+1)*12 px limit that 81xx punctuation had, plus
;      WRAP_EXTRA px (main box: 16 cells + 20 = 212 px). Our build line-breaks itself; this is the safety net.
.org 0x0800EA26
  b 0x0800EA32
.org 0x0800EA34
  ldr r0,=wrap_limit|1
  bx r0
  .pool

; ---- main dialogue box text origin x: 30 -> 14 px (0x0802879C movs r0,#0xF0 / lsls r0,#5)
.org 0x0802879C
  mov r0,#0x70

; ---- menu layout 0800E4FC: entry advance byte (was 12)
.org 0x0800E5A4
  ldr r1,[pc,#0]               ; E5A8
  bx r1
  .word menu_advance|1
newline_tail:                  ; E5AC: the newline cell ("nn", empty entry) skips the glyph: r4 += 8 / r7++
  add r4,#8
  add r7,#1
  nop                          ; falls into the loop head at E5B2
.org 0x0800E54C
  b newline_tail               ; was b 0x0800E5AA, which now lands in the hook above

; ---- choice rows (task_adv_menuTabList, class 0x085D9A58): the glyph entry buffer at +0x44 holds 8 cells and
;      overflows into the fields after it. Move it to +0x98 (past the original object) with room for CHOICE_CELLS,
;      and centre the row on the text's pixel width instead of 12 px per cell.
CHOICE_CELLS equ 16
.org 0x085D9A6C
  .word 0x98 + CHOICE_CELLS * 8  ; object size
.org 0x0802993A
  add r4,#0x84                 ; init: entry buffer +0x14 +0x84 = +0x98 (was +0x30)
  add r0,r4,#0
  mov r1,#CHOICE_CELLS         ; entries cleared (was 8)
.org 0x08029BE2
  add r2,#0x98                 ; draw (was +0x44)
.org 0x08029C28
  add r2,#0x98                 ; draw (was +0x44)
.org 0x08029C8E
  add r4,#0x98                 ; free (was +0x44)
.org 0x08029BBE                ; draw, side 0 (replaced 08029BBE-BCF: r1 = (4 - cells)*6 + 16)
  mov r2,#40
  ldr r3,=0x08029BD0|1
  ldr r1,=choice_x|1
  bx r1
  .pool
.org 0x08029C04                ; draw, side 1 (replaced 08029C04-C15: r1 = (8 - cells)*6 + 16)
  mov r2,#64
  ldr r3,=0x08029C16|1
  ldr r1,=choice_x|1
  bx r1
  .pool

; ---- list menus (generic list 0801162C, e.g. map View/Menu/Save/Enter): item {entries, u16 count, ..}; the draw
;      centred each item on x+40 at 12 px per cell (08011572-0801157F: r0 = (4 - count)*6 + 16)
.org 0x08011572
  ldr r1,=menu_x|1
  bx r1
  .pool

.org CODE_AT
menu_x:                        ; r5 = item -> back at 08011580 with r0 = 40 - width/2 (r1-r4 reloaded there)
  ldr r2,[r5]                  ; entries {OBJ handle, u8 advance}
  ldrh r3,[r5,#4]              ; count
  mov r0,#0
@@next:
  cmp r3,#0
  beq @@done
  ldrb r1,[r2,#4]
  add r0,r0,r1
  add r2,#8
  sub r3,#1
  b @@next
@@done:
  lsr r0,r0,#1
  mov r1,#40
  sub r0,r1,r0
  ldr r1,=0x08011580|1
  bx r1

choice_x:                      ; r0 = row x (kept), r2 = centre, r3 = return, r5 = object -> r1 = centre - width/2
  push {r0,r2,r3,r4,r6}        ; r2/r3 are reloaded after the return points
  add r4,r5,#0                 ; width = sum of the entries' advances (the string pointer at +0x94 is shared
  add r4,#0x41                 ; by all rows, so it only holds the last row's text by draw time)
  ldrb r1,[r4]                 ; entry count
  add r4,#0x98 - 0x41 + 4      ; first entry's advance byte
  mov r6,#0
@@next:
  cmp r1,#0
  beq @@done
  ldrb r0,[r4]
  add r6,r6,r0
  add r4,#8
  sub r1,#1
  b @@next
@@done:
  lsr r6,r6,#1
  ldr r2,[sp,#4]
  sub r1,r2,r6
  pop {r0,r2,r3,r4,r6}
  bx r3

lookup_hook:
  push {r4,r5,r6,lr}           ; replaced: push / adds r3,r1,#0 / lsls r0,#16 / lsrs r4,r0,#16
  add r3,r1,#0
  lsl r0,r0,#16
  lsr r4,r0,#16
  lsr r0,r4,#8
  cmp r0,#0x80
  bcs @@sjis
  strh r4,[r3]
  mov r0,#3
  strb r0,[r2]
  pop {r4,r5,r6}
  pop {r0}
  bx r0
@@sjis:
  ldr r0,=0x0800A874|1
  bx r0

upload_hook:
  push {lr}                    ; replaced: push {lr} / lsls r0,#24 / lsrs r0,#24 / adds r3,r0,#0
  lsl r0,r0,#24
  lsr r0,r0,#24
  cmp r0,#3
  beq @@pair
  add r3,r0,#0
  ldr r2,=0x0800A788|1         ; r2 is reloaded there (lsrs r2,r1,#16)
  bx r2
@@pair:
  lsl r1,r1,#16
  lsr r1,r1,#16
  lsr r2,r1,#8                 ; a
  sub r2,#0x20
  lsl r2,r2,#7
  lsl r3,r1,#24
  lsr r3,r3,#24                ; b
  add r2,r2,r3
  lsl r2,r2,#1
  ldr r3,=PAIR_TAB
  ldrh r2,[r3,r2]
  lsl r2,r2,#7
  ldr r0,=PAIR_GFX
  add r0,r0,r2
  mov r1,#0x80
  ldr r3,=0x080025C0|1         ; OBJ tile cache: (src, size) -> handle
  bl call_r3
  pop {r1}
  bx r1

; r0 = advance of the cell at r1 (two bytes)
cell_width:
  ldrb r0,[r1]
  cmp r0,#0x80
  bcs @@sjis
  ldr r2,=WIDTHS
  ldrb r0,[r2,r0]
  ldrb r1,[r1,#1]
  ldrb r1,[r2,r1]
  add r0,r0,r1
  bx lr
@@sjis:
  mov r0,#12
  bx lr

dlg_advance:                   ; replaced 0800EA80-EA91: sb = (sb+1)&0xFF / sl += 0xC00 / r5 += 2
  mov r0,r9                    ; sb
  add r0,#1
  lsl r0,r0,#24
  lsr r0,r0,#24
  mov r9,r0
  add r1,r5,#0
  bl cell_width
  lsl r0,r0,#8
  add r10,r0                   ; sl
  add r5,#2
  ldr r0,=0x0800EA92|1         ; loop head reloads r0
  bx r0

wrap_limit:                    ; replaced 0800EA34-EA3B: r0 = r1*12 px (8.8) / r7 = r2
  lsl r0,r1,#1
  add r0,r0,r1
  lsl r0,r0,#10
  mov r3,#WRAP_EXTRA
  lsl r3,r3,#8
  add r0,r0,r3
  add r7,r2,#0
  ldr r3,=0x0800EA3C|1         ; r3 is not live here
  bx r3

menu_advance:                  ; replaced 0800E5A4-E5B1: str r0,[r4] / strb 12,[r4,#4] / r4 += 8 / r7++
  str r0,[r4]
  mov r1,sp                    ; the cell's two bytes were copied to [sp] (r6 = sp)
  bl cell_width
  strb r0,[r4,#4]
  add r4,#8
  add r0,r7,#1
  lsl r0,r0,#24
  lsr r7,r0,#24
  ldr r1,=0x0800E5B2|1         ; loop head reloads r1
  bx r1

call_r3:
  bx r3

  .pool
.close
