main:   mov sp, 0xffff  ; initialize stack pointer
        mov a, 0

up:     nop     ; print(a)
        call inc
        cmp 0b1111
        jnz up

down:   nop     ; print(a)
        call dec
        jnz down

        jmp up

inc:    add 1
        ret

dec:    sub 1
        ret

.end
