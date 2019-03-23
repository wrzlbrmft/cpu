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
        ret
.endproc

.proc   int21
        ret
.endproc

.proc   int22
        ret
.endproc

.proc   int23
        ret
.endproc

.proc   int24
        ret
.endproc

.proc   int25
        ret
.endproc

.proc   int26
        ret
.endproc

.proc   int27
        ret
.endproc

.proc   int28
        ret
.endproc

.proc   int29
        ret
.endproc

.proc   int2a
        ret
.endproc

.proc   int2b
        ret
.endproc

.proc   int2c
        ret
.endproc

.proc   int2d
        ret
.endproc

.proc   int2e
        ret
.endproc

.proc   int2f
        ret
.endproc

.proc   int30
        ret
.endproc

.proc   int31
        ret
.endproc

.proc   int32
        ret
.endproc

.proc   int33
        ret
.endproc

.proc   int34
        ret
.endproc

.proc   int35
        ret
.endproc

.proc   int36
        ret
.endproc

.proc   int37
        ret
.endproc

.proc   int38
        ret
.endproc

.proc   int39
        ret
.endproc

.proc   int3a
        ret
.endproc

.proc   int3b
        ret
.endproc

.proc   int3c
        ret
.endproc

.proc   int3d
        ret
.endproc

.proc   int3e
        ret
.endproc

.proc   int3f
        ret
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
