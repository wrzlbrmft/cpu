.base   0x0900  ; os entry point

main:   jmp boot
        nop

; --------- os interrupt address table at 0x0904 ---------

        dw int20, int21, int22, int23, int24, int25, int26, int27
        dw int28, int29, int2a, int2b, int2c, int2d, int2e, int2f
        dw int30, int31, int32, int33, int34, int35, int36, int37
        dw int38, int39, int3a, int3b, int3c, int3d, int3e, int3f

; --------------------------------------------------------

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

; --------- boot routine ---------

boot:   ; populate dynamic interrupt jump table with os interrupt addresses
        mov b, 0x04     ; copy from h+0x04
        mov c, 0x80     ; to h+0x80

i0:     mov h, 0x08     ; 0x0800+c
        mov l, c
        mov d, 0x77     ; opcode for 'jmp addr' instruction
        mov m, d

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

        cmp 0xfe        ; just copied last os interrupt address (int 0x3f)?
        jz i0x          ; if yes, exit loop

        mov a, b        ; b += 1
        add 0x01
        mov b, a
        mov a, c        ; c += 2 (skip 4th byte)
        add 0x02
        mov c, a

        jmp i0

cpb:    mov h, 0x09     ; copy byte from 0x0900+b
        mov l, b
        mov d, m
        mov h, 0x08     ; to 0x0800+c
        mov l, c
        mov m, d
        ret

i0x:    hlt             ; done copying os interrupt addresses

; --------------------------------

.end
