.PHONY: clean

clean:
	rm -vf asm
	rm -vf link

asm:
	$(eval TEMP_DIR := $(shell mktemp -d))
	cp -v asm.py $(TEMP_DIR)/__main__.py
	cp -v endianness.py fileutils.py i18n.py obj_file.py symbol_table.py symbols.py $(TEMP_DIR)

	$(eval TEMP_FILE := $(shell mktemp))
	zip -rj9 $(TEMP_FILE).zip $(TEMP_DIR)

	echo '#!/usr/bin/env python' > asm
	cat $(TEMP_FILE).zip >> asm
	chmod +x asm

	rm -v $(TEMP_FILE).zip
	rm -rv $(TEMP_DIR)

link:
	$(eval TEMP_DIR := $(shell mktemp -d))
	cp -v link.py $(TEMP_DIR)/__main__.py
	cp -v cpu_file.py endianness.py fileutils.py i18n.py obj_file.py symbol_table.py symbols.py $(TEMP_DIR)

	$(eval TEMP_FILE := $(shell mktemp))
	zip -rj9 $(TEMP_FILE).zip $(TEMP_DIR)

	echo '#!/usr/bin/env python' > link
	cat $(TEMP_FILE).zip >> link
	chmod +x link

	rm -v $(TEMP_FILE).zip
	rm -rv $(TEMP_DIR)
