.base   0x0900

.proc   main
    mov c, 0x00
    mov d, 0x00

    ; save old interrupt
    mov b, 0x01
    mov a, 0x03         ; interrupt 0x03
    int 0x02
    stoa old_int_addr_hi, h
    stoa old_int_addr_lo, l

    ; set new interrupt
    inc b
    mov hl, new_int
    int 0x02

    int 0x03

    ; restore old interrupt
    loda h, old_int_addr_hi
    loda l, old_int_addr_lo
    int 0x02

    int 0x03

    hlt
.endproc

.proc   new_int
    inc d

    pushhl          ; call old interrupt
    loda h, old_int_addr_hi
    loda l, old_int_addr_lo
    pushf
    call m
    pophl

    iret
.endproc

old_int_addr_lo: db 0
old_int_addr_hi: db 0

.end
