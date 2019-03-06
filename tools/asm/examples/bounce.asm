main:   mov a, 0

up:     nop     ; print(a)
        add 1
        cmp 0b1111
        jnz up

down:   nop     ; print(a)
        sub 1
        jnz down

        jmp up

.end
