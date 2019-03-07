;.base   0x0800

main:   jmp boot
        nop

; --------- dynamic interrupt jump table ---------

; --- bios interrupts ---

_int01: ret
        nop
        nop
        nop

_int02: ret
        nop
        nop
        nop

_int03: ret
        nop
        nop
        nop

_int04: ret
        nop
        nop
        nop

_int05: ret
        nop
        nop
        nop

_int06: ret
        nop
        nop
        nop

_int07: ret
        nop
        nop
        nop

_int08: ret
        nop
        nop
        nop

_int09: ret
        nop
        nop
        nop

_int0a: ret
        nop
        nop
        nop

_int0b: ret
        nop
        nop
        nop

_int0c: ret
        nop
        nop
        nop

_int0d: ret
        nop
        nop
        nop

_int0e: ret
        nop
        nop
        nop

_int0f: ret
        nop
        nop
        nop

_int10: ret
        nop
        nop
        nop

_int11: ret
        nop
        nop
        nop

_int12: ret
        nop
        nop
        nop

_int13: ret
        nop
        nop
        nop

_int14: ret
        nop
        nop
        nop

_int15: ret
        nop
        nop
        nop

_int16: ret
        nop
        nop
        nop

_int17: ret
        nop
        nop
        nop

_int18: ret
        nop
        nop
        nop

_int19: ret
        nop
        nop
        nop

_int1a: ret
        nop
        nop
        nop

_int1b: ret
        nop
        nop
        nop

_int1c: ret
        nop
        nop
        nop

_int1d: ret
        nop
        nop
        nop

_int1e: ret
        nop
        nop
        nop

_int1f: ret
        nop
        nop
        nop

; --- os interrupts ---

_int20: jmp int20
        nop

_int21: jmp int21
        nop

_int22: jmp int22
        nop

_int23: jmp int23
        nop

_int24: jmp int24
        nop

_int25: jmp int25
        nop

_int26: jmp int26
        nop

_int27: jmp int27
        nop

_int28: jmp int28
        nop

_int29: jmp int29
        nop

_int2a: jmp int2a
        nop

_int2b: jmp int2b
        nop

_int2c: jmp int2c
        nop

_int2d: jmp int2d
        nop

_int2e: jmp int2e
        nop

_int2f: jmp int2f
        nop

_int30: jmp int30
        nop

_int31: jmp int31
        nop

_int32: jmp int32
        nop

_int33: jmp int33
        nop

_int34: jmp int34
        nop

_int35: jmp int35
        nop

_int36: jmp int36
        nop

_int37: jmp int37
        nop

_int38: jmp int38
        nop

_int39: jmp int39
        nop

_int3a: jmp int3a
        nop

_int3b: jmp int3b
        nop

_int3c: jmp int3c
        nop

_int3d: jmp int3d
        nop

_int3e: jmp int3e
        nop

_int3f: jmp int3f
        nop

; ------------------------------------------------

; --------- os interrupt routines ---------

int20:  ret

int21:  ret

int22:  ret

int23:  ret

int24:  ret

int25:  ret

int26:  ret

int27:  ret

int28:  ret

int29:  ret

int2a:  ret

int2b:  ret

int2c:  ret

int2d:  ret

int2e:  ret

int2f:  ret

int30:  ret

int31:  ret

int32:  ret

int33:  ret

int34:  ret

int35:  ret

int36:  ret

int37:  ret

int38:  ret

int39:  ret

int3a:  ret

int3b:  ret

int3c:  ret

int3d:  ret

int3e:  ret

int3f:  ret

; -----------------------------------------

; --------- boot code ---------

; copy bios interrupt addresses from static to dynamic interrupt jump table
boot:   mov b, 0x02     ; start with interrupt 0x01
        mov c, 0x04

i0:     mov h, 0x08
        mov l, c
        mov m, 0x77     ; opcode for 'jmp addr'

        mov a, c        ; c += 1
        add 0x01
        mov c, a

        call cpb        ; copy low-order byte of interrupt address

        mov a, b        ; b += 1
        add 0x01
        mov b, a
        mov a, c        ; c += 1
        add 0x01
        mov c, a

        call cpb        ; copy high-order byte of interrupt address

        cmp 0x7e        ; reached high-order byte of address of interrupt 0x1f
        jz  ok

        mov a, b        ; b += 1
        add 0x01
        mov b, a
        mov a, c        ; c += 2 (skip nop)
        add 0x02
        mov c, a

        jmp i0x

cpb:    mov h, 0x01     ; read byte from 0x0100+b
        mov l, b
        mov d, m
        mov h, 0x08     ; write byte to 0x0800+c
        mov l, c
        mov m, d
        ret

i0x:    hlt             ; done copying interrupt addresses

; -----------------------------

.end
