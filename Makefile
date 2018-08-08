

requirements:
	pip install -r ../configuration/requirements.txt
	mkdir -p vendor/roles
	ansible-galaxy install -p vendor/roles -r requirements.yml