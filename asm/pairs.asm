; English pair glyphs (docs/re/font.md). A text cell whose first byte is < 0x80 is two ASCII letters drawn as one
; 16x16 OBJ glyph pre-rendered by tools/build.py; the layout routines advance by the pair's pixel width instead
; of the fixed 12 px. Assembled onto the built ROM by tools/build.py.
;   PAIR_TAB  u16[96*128]: glyph number for cell (a, b) at (a-0x20)*128 + b; 0 = missing (glyph 0 = '?')
;   PAIR_GFX  128 bytes per glyph (tiles TL, TR, BL, BR)
;   WIDTHS    u8[128]: advance per ASCII byte

.gba
.open BUILD_ROM, 0x08000000
.thumb

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

; ---- dialogue auto-wrap limit: every cell gets the (width+1)*12 px limit that 81xx punctuation had
;      (dialogue: 15 -> 16 cells = 192 px). Our build line-breaks itself; this is only the safety net.
.org 0x0800EA26
  b 0x0800EA32

; ---- menu layout 0800E4FC: entry advance byte (was 12)
.org 0x0800E5A4
  ldr r1,=menu_advance|1
  bx r1
  nop
  nop
  .pool

.org CODE_AT
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
