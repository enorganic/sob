SHELL := bash
PYTHON_VERSION := 3.8

install:
	{ python$(PYTHON_VERSION) -m venv venv || py -$(PYTHON_VERSION) -m venv venv ; } && \
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	pip install --upgrade pip wheel && \
	pip install\
	 -r requirements.txt\
	 -e . && \
	{ mypy --install-types --non-interactive || echo "" ; } && \
	echo "Installation Successful!"

ci-install:
	{ python3 -m venv venv || py -3 -m venv venv ; } && \
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	{ python3 -m pip install --upgrade pip || echo "" ; } && \
	python3 -m pip install\
	 -r requirements.txt\
	 -e . && \
	echo "Installation Successful!"

editable:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	daves-dev-tools install-editable --upgrade-strategy eager && \
	make requirements

clean:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	daves-dev-tools uninstall-all\
	 -e .\
     -e pyproject.toml\
     -e tox.ini\
     -e requirements.txt && \
	daves-dev-tools clean

distribute:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	daves-dev-tools distribute --skip-existing

upgrade:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	daves-dev-tools requirements freeze\
	 -nv '*' . pyproject.toml tox.ini daves-dev-tools \
	 > .requirements.txt && \
	pip install --upgrade --upgrade-strategy eager\
	 -r .requirements.txt && \
	rm .requirements.txt && \
	make requirements

requirements:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	daves-dev-tools requirements update\
	 -i more-itertools -aen all\
	 setup.cfg pyproject.toml tox.ini && \
	daves-dev-tools requirements freeze\
	 -nv setuptools -nv filelock -nv platformdirs\
	 . pyproject.toml tox.ini daves-dev-tools\
	 > requirements.txt

test:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && tox -r -p

# Apply formatting requirements and perform checks
format:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	black . && isort . && flake8 && mypy

reinstall:
	{ rm -R venv || echo "" ; } && \
	{ python$(PYTHON_VERSION) -m venv venv || py -$(PYTHON_VERSION) -m venv venv ; } && \
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	pip install --upgrade pip && \
	pip install isort flake8 mypy black tox pytest daves-dev-tools -e . && \
	{ mypy --install-types --non-interactive || echo "" ; } && \
	make requirements && \
	echo "Installation complete"
