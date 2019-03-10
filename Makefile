.PHONY: all tools os bios microcode clean

all: tools os bios microcode

tools:
	$(MAKE) -C tools/asm/src
	$(MAKE) -C tools/bin2/src
	$(MAKE) -C tools/rom/src

os: tools
	$(MAKE) -C os/src

bios: tools
	$(MAKE) -C rom/bios/src

microcode: tools
	$(MAKE) -C rom/microcode

clean:
	$(MAKE) -C tools/asm/src clean
	$(MAKE) -C tools/bin2/src clean
	$(MAKE) -C tools/rom/src clean

	$(MAKE) -C os/src clean

	$(MAKE) -C rom/bios/src clean

	$(MAKE) -C rom/microcode clean

	rm -rf tools/asm/example/*.obj
	rm -rf tools/asm/example/*.cpu
	rm -rf tools/asm/example/*.raw
	rm -rf tools/asm/src/*.obj
	rm -rf tools/asm/src/*.cpu
	rm -rf tools/asm/src/*.raw

	rm -rf tools/bin2/src/*.raw

	rm -rf tools/rom/examples/*.raw
	rm -rf tools/rom/src/*.raw
