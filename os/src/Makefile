.PHONY: os clean

os:
	../../tools/asm/src/asm os.asm
	../../tools/asm/src/link os.obj
	../../tools/bin2/src/bin2raw os.cpu 0x0900

clean:
	rm -vf os.obj
	rm -vf os.cpu
	rm -vf os.raw
