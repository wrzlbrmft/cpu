        nop

foo:    mov a,0x10  ; ok

; here comes the error
:       nop
        push a,

foo:    ; foo again?

bar:    pop :

.bar
        bar
