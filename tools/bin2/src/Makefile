.PHONY: clean

bin2raw:
	$(eval TEMP_DIR := $(shell mktemp -d))
	cp -v bin2raw.py $(TEMP_DIR)/__main__.py
	cp -v ../../rom/src/bin_file.py i18n.py ../../rom/src/raw_file.py $(TEMP_DIR)

	$(eval TEMP_FILE := $(shell mktemp))
	zip -rj9X - $(TEMP_DIR) > $(TEMP_FILE)

	echo '#!/usr/bin/env python3' > bin2raw
	cat $(TEMP_FILE) >> bin2raw
	chmod +x bin2raw

	rm -v $(TEMP_FILE)
	rm -rv $(TEMP_DIR)

clean:
	rm -vf bin2raw
	rm -rvf __pycache__
