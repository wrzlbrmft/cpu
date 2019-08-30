.base   0x0000  ; bios entry point

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
        dw int00
bios_int_addr_tbl_int01:
        dw        int01, int02, int03, int04, int05, int06, int07
        dw int08, int09, int0a, int0b, int0c, int0d, int0e, int0f
        dw int10, int11, int12, int13, int14, int15, int16, int17
        dw int18, int19, int1a, int1b, int1c, int1d, int1e, int1f

; ----------------------------------------------------------

.endproc

; --------- bios interrupt routines ---------

.proc   int00
        ; power on
        mov sp, 0xffff  ; initialize stack pointer

        ; copy bios interrupt address table to dynamic interrupt jump table
        mov a, 0x01     ; first destination interrupt in dynamic interrupt jump table (skip interrupt 0x00)
        mov b, 0x1f     ; number of interrupt addresses to copy
        mov hl, bios_int_addr_tbl_int01 ; address of source interrupt address table (start at interrupt 0x01)
        pushf           ; manually push flags for direct interrupt call
        call int01      ; direct interrupt call (to not use dynamic interrupt jump table; not ready)

        ; TODO: load os

        jmp 0x0900      ; jump into os
.endproc

.proc   int01
        ; copy interrupt address table to dynamic interrupt jump table
        ;   a = first destination interrupt in dynamic interrupt jump table
        ;   b = number of interrupt addresses to copy
        ;   hl = address of source interrupt address table
        push a
        push b
        push c
        push d
        pushhl

        ; calculate destination address in dynamic interrupt jump table
        add a           ; a *= 4
        add a

@0:     mov c, m        ; read low-order byte
        inchl
        mov d, m        ; read high-order byte
        inchl

        pushhl          ; save source address

        mov h, 0x08     ; write to 0x0800+a
        mov l, a
        mov a, 0x77     ; opcode for 'jmp addr' instruction
        mov m, a
        inc l
        mov m, c        ; write low-order byte
        inc l
        mov m, d        ; write high-order byte

        dec b
        jz @1           ; done

        mov a, l        ; skip 4th byte
        add 0x02

        pophl           ; restore source address

        jmp @0          ; next interrupt address

@1:     pophl           ; restore source address

        pophl
        pop d
        pop c
        pop b
        pop a

        iret
.endproc

.proc   int02
        ; get/set interrupt address in dynamic interrupt jump table
        ; b = 0x01: get interrupt address
        ;   a = interrupt number
        ;   return:
        ;       hl = interrupt address
        ; b = 0x02: set interrupt address
        ;   a = interrupt number
        ;   hl = interrupt address
        push b

        dec b
        jz @1
        dec b
        jz @2

        pop b

        iret

; get interrupt address
@1:     pop b
        push a
        push c
        push d

        ; calculate destination address in dynamic interrupt jump table
        add a           ; a *= 4
        add a
        inc a           ; skip 1st byte (opcode for 'jmp addr' instruction)

        mov h, 0x08     ; read from 0x0800+a
        mov l, a

        mov c, m        ; read low-order byte
        inchl
        mov d, m        ; read high-order byte

        mov h, d        ; set high-order byte
        mov l, c        ; set low-order byte

        pop d
        pop c
        pop a

        iret

; set interrupt address
@2:     pop b
        push a
        push c
        push d
        pushhl

        ; calculate destination address in dynamic interrupt jump table
        add a           ; a *= 4
        add a
        inc a           ; skip 1st byte (opcode for 'jmp addr' instruction)

        mov c, l        ; set low-order byte
        mov d, h        ; set high-order byte

        mov h, 0x08     ; write to 0x0800+a
        mov l, a
        mov m, c        ; write low-order byte
        inc l
        mov m, d        ; write high-order byte

        pophl
        pop d
        pop c
        pop a

        iret
.endproc

.proc   int03
        iret
.endproc

.proc   int04
        iret
.endproc

.proc   int05
        iret
.endproc

.proc   int06
        iret
.endproc

.proc   int07
        iret
.endproc

.proc   int08
        iret
.endproc

.proc   int09
        iret
.endproc

.proc   int0a
        iret
.endproc

.proc   int0b
        iret
.endproc

.proc   int0c
        iret
.endproc

.proc   int0d
        iret
.endproc

.proc   int0e
        iret
.endproc

.proc   int0f
        iret
.endproc

.proc   int10
        iret
.endproc

.proc   int11
        iret
.endproc

.proc   int12
        iret
.endproc

.proc   int13
        iret
.endproc

.proc   int14
        iret
.endproc

.proc   int15
        iret
.endproc

.proc   int16
        iret
.endproc

.proc   int17
        iret
.endproc

.proc   int18
        iret
.endproc

.proc   int19
        iret
.endproc

.proc   int1a
        iret
.endproc

.proc   int1b
        iret
.endproc

.proc   int1c
        iret
.endproc

.proc   int1d
        iret
.endproc

.proc   int1e
        iret
.endproc

.proc   int1f
        iret
.endproc

; -------------------------------------------

.end
