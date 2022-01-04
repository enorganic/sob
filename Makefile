# python 3.6 is used, for the time being, in order to ensure compatibility
install:
	(python3.6 -m venv venv || python3 -m venv venv) && \
	venv/bin/pip3 install --upgrade pip && \
	venv/bin/pip3 install\
	 -r requirements.txt\
	 -e . && \
	venv/bin/mypy --install-types --non-interactive

clean:
	venv/bin/daves-dev-tools uninstall-all\
	 -e .\
     -e pyproject.toml\
     -e tox.ini\
     -e requirements.txt && \
	venv/bin/daves-dev-tools clean

requirements:
	venv/bin/daves-dev-tools requirements update\
	 -v\
	 setup.cfg\
	 pyproject.toml\
	 tox.ini && \
	venv/bin/daves-dev-tools requirements freeze\
	 . pyproject.toml tox.ini requirements.txt\
	 >> .requirements.txt && \
	rm requirements.txt && \
	mv .requirements.txt requirements.txt

distribute:
	venv/bin/daves-dev-tools distribute --skip-existing

test:
	venv/bin/tox -p all

upgrade:
	venv/bin/daves-dev-tools requirements freeze\
	 -nv '*' . pyproject.toml tox.ini requirements.txt\
	 > .unversioned_requirements.txt && \
	venv/bin/pip3 install --upgrade --upgrade-strategy eager\
	 -r .unversioned_requirements.txt -e . && \
	rm .unversioned_requirements.txt && \
	make requirements
