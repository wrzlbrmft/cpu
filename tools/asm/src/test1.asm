        nop

foo:    mov a,0x10  ; ok
        nop 0x10h

.end ---------------------------

; here comes the error
:       nop
        push a,

foo:    ; foo again?

bar:    pop :

.bar
        bar
