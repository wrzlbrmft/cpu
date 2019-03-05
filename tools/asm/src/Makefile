.PHONY: all clean

all: asm link

asm:
	$(eval TEMP_DIR := $(shell mktemp -d))
	cp -v asm.py $(TEMP_DIR)/__main__.py
	cp -v binutils.py data.py fileutils.py i18n.py obj_file.py relocation_table.py symbol_table.py symbols.py $(TEMP_DIR)

	$(eval TEMP_FILE := $(shell mktemp))
	zip -rj9X - $(TEMP_DIR) > $(TEMP_FILE)

	echo '#!/usr/bin/env python3' > asm
	cat $(TEMP_FILE) >> asm
	chmod +x asm

	rm -v $(TEMP_FILE)
	rm -rv $(TEMP_DIR)

link:
	$(eval TEMP_DIR := $(shell mktemp -d))
	cp -v link.py $(TEMP_DIR)/__main__.py
	cp -v binutils.py cpu_file.py fileutils.py i18n.py obj_file.py relocation_table.py symbol_table.py symbols.py $(TEMP_DIR)

	$(eval TEMP_FILE := $(shell mktemp))
	zip -rj9X - $(TEMP_DIR) > $(TEMP_FILE)

	echo '#!/usr/bin/env python3' > link
	cat $(TEMP_FILE) >> link
	chmod +x link

	rm -v $(TEMP_FILE)
	rm -rv $(TEMP_DIR)

clean:
	rm -vf asm
	rm -vf link
	rm -rvf __pycache__
