.PHONY: bios clean

bios:
	../../../tools/asm/src/asm bios.asm
	../../../tools/asm/src/link bios.obj
	../../../tools/bin2/src/bin2raw bios.cpu 0x0000

clean:
	rm -vf bios.obj
	rm -vf bios.cpu
	rm -vf bios.raw
