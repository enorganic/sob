.PHONY:
	install
	clean
	requirements
.DEFAULT_GOAL := install

install:
	python3.6 -m venv venv &&\
	venv/bin/pip3 install -e '.[test,dev]'

clean:
	venv/bin/daves-dev-tools clean

requirements:
	venv/bin/python3 scripts/update_setup_requirements.py

readme:
	venv/bin/python3 scripts/update_readme.py


