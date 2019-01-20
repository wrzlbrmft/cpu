main:   mov a,0

up:     nop     ; print
        add 1
        cmp 100
        jnz up

down:   nop     ; print
        sub 1
        jnz down

        jmp up

.end
