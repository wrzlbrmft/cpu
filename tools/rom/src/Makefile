.PHONY: clean

clean:
	rm -vf rom
	rm -rvf __pycache__

rom:
	$(eval TEMP_DIR := $(shell mktemp -d))
	cp -v rom.py $(TEMP_DIR)/__main__.py
	cp -v ../../asm/src/data.py i18n.py $(TEMP_DIR)

	$(eval TEMP_FILE := $(shell mktemp))
	zip -rj9X - $(TEMP_DIR) > $(TEMP_FILE)

	echo '#!/usr/bin/env python3' > rom
	cat $(TEMP_FILE) >> rom
	chmod +x rom

	rm -v $(TEMP_FILE)
	rm -rv $(TEMP_DIR)
