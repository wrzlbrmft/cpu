main:   mov b,0
        mov c,1

loop:   nop     ; print(b)
        mov a,b
        add c
        mov b,c
        mov c,a
        jnc loop

        jmp main

.end
