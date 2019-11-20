#!/usr/bin/env sh
if [ -z "${VIRTUAL_ENV}" ]; then
    source venv/bin/activate
fi
export PATH=${PWD}/bin:${PATH}
