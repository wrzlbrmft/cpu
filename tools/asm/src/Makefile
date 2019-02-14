.PHONY: clean

clean:
	rm -vf asm
	rm -vf link
	rm -rvf __pycache__

asm:
	$(eval TEMP_DIR := $(shell mktemp -d))
	cp -v asm.py $(TEMP_DIR)/__main__.py
	cp -v endianness.py fileutils.py i18n.py obj_file.py symbol_table.py symbols.py $(TEMP_DIR)

	$(eval TEMP_FILE := $(shell mktemp))
	zip -rj9X - $(TEMP_DIR) > $(TEMP_FILE)

	echo '#!/usr/bin/env python' > asm
	cat $(TEMP_FILE) >> asm
	chmod +x asm

	rm -v $(TEMP_FILE)
	rm -rv $(TEMP_DIR)

link:
	$(eval TEMP_DIR := $(shell mktemp -d))
	cp -v link.py $(TEMP_DIR)/__main__.py
	cp -v cpu_file.py endianness.py fileutils.py i18n.py obj_file.py symbol_table.py symbols.py $(TEMP_DIR)

	$(eval TEMP_FILE := $(shell mktemp))
	zip -rj9X - $(TEMP_DIR) > $(TEMP_FILE)

	echo '#!/usr/bin/env python' > link
	cat $(TEMP_FILE) >> link
	chmod +x link

	rm -v $(TEMP_FILE)
	rm -rv $(TEMP_DIR)
