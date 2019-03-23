.base 0x0000    ; bios entry point

.proc   main

; --------- static interrupt jump table ---------
; the INT microcode jumps into the static interrupt jump table

; --- bios interrupts ---

; int 0x00 is fixed and does not jump into the dynamic interrupt jump table
; it is the bios entry point at 0x0000 when the cpu is powered on
_int00: jmp int00
        nop

; all other interrupts use the dynamic interrupt jump table

; dynamic_interrupt_jump_table = 0x0800  # start address of ram
; for i in range(1, 64):
;     print("_int{}: jmp 0x{}\n        nop\n".format(
;         hex(i)[2:].zfill(2),
;         hex(dynamic_interrupt_jump_table + (4 * i))[2:].zfill(4)
;     ))

_int01: jmp 0x0804
        nop

_int02: jmp 0x0808
        nop

_int03: jmp 0x080c
        nop

_int04: jmp 0x0810
        nop

_int05: jmp 0x0814
        nop

_int06: jmp 0x0818
        nop

_int07: jmp 0x081c
        nop

_int08: jmp 0x0820
        nop

_int09: jmp 0x0824
        nop

_int0a: jmp 0x0828
        nop

_int0b: jmp 0x082c
        nop

_int0c: jmp 0x0830
        nop

_int0d: jmp 0x0834
        nop

_int0e: jmp 0x0838
        nop

_int0f: jmp 0x083c
        nop

_int10: jmp 0x0840
        nop

_int11: jmp 0x0844
        nop

_int12: jmp 0x0848
        nop

_int13: jmp 0x084c
        nop

_int14: jmp 0x0850
        nop

_int15: jmp 0x0854
        nop

_int16: jmp 0x0858
        nop

_int17: jmp 0x085c
        nop

_int18: jmp 0x0860
        nop

_int19: jmp 0x0864
        nop

_int1a: jmp 0x0868
        nop

_int1b: jmp 0x086c
        nop

_int1c: jmp 0x0870
        nop

_int1d: jmp 0x0874
        nop

_int1e: jmp 0x0878
        nop

_int1f: jmp 0x087c
        nop

; --- os interrupts ---

_int20: jmp 0x0880
        nop

_int21: jmp 0x0884
        nop

_int22: jmp 0x0888
        nop

_int23: jmp 0x088c
        nop

_int24: jmp 0x0890
        nop

_int25: jmp 0x0894
        nop

_int26: jmp 0x0898
        nop

_int27: jmp 0x089c
        nop

_int28: jmp 0x08a0
        nop

_int29: jmp 0x08a4
        nop

_int2a: jmp 0x08a8
        nop

_int2b: jmp 0x08ac
        nop

_int2c: jmp 0x08b0
        nop

_int2d: jmp 0x08b4
        nop

_int2e: jmp 0x08b8
        nop

_int2f: jmp 0x08bc
        nop

_int30: jmp 0x08c0
        nop

_int31: jmp 0x08c4
        nop

_int32: jmp 0x08c8
        nop

_int33: jmp 0x08cc
        nop

_int34: jmp 0x08d0
        nop

_int35: jmp 0x08d4
        nop

_int36: jmp 0x08d8
        nop

_int37: jmp 0x08dc
        nop

_int38: jmp 0x08e0
        nop

_int39: jmp 0x08e4
        nop

_int3a: jmp 0x08e8
        nop

_int3b: jmp 0x08ec
        nop

_int3c: jmp 0x08f0
        nop

_int3d: jmp 0x08f4
        nop

_int3e: jmp 0x08f8
        nop

_int3f: jmp 0x08fc
        nop

; -----------------------------------------------

; --------- bios interrupt address table at 0x0100 ---------

bios_int_addr_tbl:
        dw int00, int01, int02, int03, int04, int05, int06, int07
        dw int08, int09, int0a, int0b, int0c, int0d, int0e, int0f
        dw int10, int11, int12, int13, int14, int15, int16, int17
        dw int18, int19, int1a, int1b, int1c, int1d, int1e, int1f

; ----------------------------------------------------------

.endproc

; --------- bios interrupt routines ---------

.proc   int00
        ; power on
        mov sp, 0xffff  ; initialize stack pointer

        ; copy bios interrupt address table
        mov b, 0x1f     ; number of interrupt addresses to copy
        mov c, 0x01     ; first destination interrupt in dynamic interrupt jump table
        mov hl, bios_int_addr_tbl
        mov a, l        ; l += 2 (skip interrupt 0x00)
        add 0x02
        mov l, a
        call int01      ; direct interrupt call (dynamic interrupt jump table not ready)

        ; TODO: load os

        jmp 0x0900      ; jump into os
.endproc

.proc   int01
        ; copy interrupt address table
        ;   b = number of interrupt addresses to copy
        ;   c = first destination interrupt in dynamic interrupt jump table
        ;   hl = address of interrupt address table
        mov a, c        ; c *= 4
        add a
        add a
        mov c, a        ; write to 0x0800+c onwards
        mov a, b        ; use the a register as counter
        mov b, l        ; read from h+b onwards

i0:     push a          ; push counter

        mov d, m        ; read low-order byte of interrupt address
        mov a, l        ; b = l + 1
        add 0x01
        mov b, a

        push h
        mov h, 0x08
        mov l, c        ; 0x0800+c
        mov a, 0x77     ; opcode for 'jmp addr' instruction
        mov m, a
        mov a, l        ; l += 1
        add 0x01
        mov l, a
        mov m, d        ; write low-order byte of interrupt address
        mov a, l        ; c = l + 1
        add 0x01
        mov c, a
        pop h

        mov l, b        ; h+b
        mov d, m        ; read high-order byte of interrupt address
        mov a, l        ; b = l + 1
        add 0x01
        mov b, a

        push h
        mov h, 0x08
        mov l, c        ; 0x0800+c
        mov m, d        ; write high-order byte of interrupt address
        mov a, l        ; c = l + 2
        add 0x02
        mov c, a
        pop h

        pop a           ; pop counter
        sub 0x01
        rz              ; done

        mov l, b        ; h+l

        jmp i0          ; next interrupt address
.endproc

.proc   int02
        ret
.endproc

.proc   int03
        ret
.endproc

.proc   int04
        ret
.endproc

.proc   int05
        ret
.endproc

.proc   int06
        ret
.endproc

.proc   int07
        ret
.endproc

.proc   int08
        ret
.endproc

.proc   int09
        ret
.endproc

.proc   int0a
        ret
.endproc

.proc   int0b
        ret
.endproc

.proc   int0c
        ret
.endproc

.proc   int0d
        ret
.endproc

.proc   int0e
        ret
.endproc

.proc   int0f
        ret
.endproc

.proc   int10
        ret
.endproc

.proc   int11
        ret
.endproc

.proc   int12
        ret
.endproc

.proc   int13
        ret
.endproc

.proc   int14
        ret
.endproc

.proc   int15
        ret
.endproc

.proc   int16
        ret
.endproc

.proc   int17
        ret
.endproc

.proc   int18
        ret
.endproc

.proc   int19
        ret
.endproc

.proc   int1a
        ret
.endproc

.proc   int1b
        ret
.endproc

.proc   int1c
        ret
.endproc

.proc   int1d
        ret
.endproc

.proc   int1e
        ret
.endproc

.proc   int1f
        ret
.endproc

; -------------------------------------------

.end
