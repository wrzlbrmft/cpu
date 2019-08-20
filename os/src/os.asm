.base   0x0900  ; os entry point

.proc   main
        jmp boot
        nop

; --------- os interrupt address table at 0x0904 ---------

os_int_addr_tbl:
        dw int20, int21, int22, int23, int24, int25, int26, int27
        dw int28, int29, int2a, int2b, int2c, int2d, int2e, int2f
        dw int30, int31, int32, int33, int34, int35, int36, int37
        dw int38, int39, int3a, int3b, int3c, int3d, int3e, int3f

; --------------------------------------------------------

.endproc

; --------- os interrupt routines ---------

.proc   int20
        iret
.endproc

.proc   int21
        iret
.endproc

.proc   int22
        iret
.endproc

.proc   int23
        iret
.endproc

.proc   int24
        iret
.endproc

.proc   int25
        iret
.endproc

.proc   int26
        iret
.endproc

.proc   int27
        iret
.endproc

.proc   int28
        iret
.endproc

.proc   int29
        iret
.endproc

.proc   int2a
        iret
.endproc

.proc   int2b
        iret
.endproc

.proc   int2c
        iret
.endproc

.proc   int2d
        iret
.endproc

.proc   int2e
        iret
.endproc

.proc   int2f
        iret
.endproc

.proc   int30
        iret
.endproc

.proc   int31
        iret
.endproc

.proc   int32
        iret
.endproc

.proc   int33
        iret
.endproc

.proc   int34
        iret
.endproc

.proc   int35
        iret
.endproc

.proc   int36
        iret
.endproc

.proc   int37
        iret
.endproc

.proc   int38
        iret
.endproc

.proc   int39
        iret
.endproc

.proc   int3a
        iret
.endproc

.proc   int3b
        iret
.endproc

.proc   int3c
        iret
.endproc

.proc   int3d
        iret
.endproc

.proc   int3e
        iret
.endproc

.proc   int3f
        iret
.endproc

; -----------------------------------------

; --------- boot routine ---------

.proc   boot
        ; copy os interrupt address table
        mov b, 0x20     ; number of interrupt addresses to copy
        mov c, 0x20     ; first destination interrupt in dynamic interrupt jump table
        mov hl, os_int_addr_tbl
        int 0x01

        hlt
.endproc

; --------------------------------

.end
