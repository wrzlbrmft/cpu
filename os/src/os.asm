.base   0x0900  ; os entry point

main:   jmp boot
        nop

; --------- os interrupt address table at 0x0904 ---------

os_int_addr_tbl:
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

boot:   ; copy bios interrupt address table
        mov b, 0x20     ; number of interrupt addresses to copy
        mov c, 0x20     ; first destination interrupt in dynamic interrupt jump table
        mov hl, os_int_addr_tbl
        int 0x01

        hlt

; --------------------------------

.end
