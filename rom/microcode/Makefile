.PHONY: microcode clean

microcode:
	../../tools/rom/src/rom microcode.csv 2:1,3:1,4:1,5:4,6:8 7:control_signals.txt microcode_0-7.raw 0-7
	../../tools/rom/src/rom microcode.csv 2:1,3:1,4:1,5:4,6:8 7:control_signals.txt microcode_8-15.raw 8-15
	../../tools/rom/src/rom microcode.csv 2:1,3:1,4:1,5:4,6:8 7:control_signals.txt microcode_16-23.raw 16-23

clean:
	rm -vf microcode_0-7.raw
	rm -vf microcode_8-15.raw
	rm -vf microcode_16-23.raw
