#! /bin/bash

pip install codespell pre-commit detect-secrets
pip install -r requirements.txt

pre-commit install --install-hooks
pre-commit install --install-hooks --hook-type commit-msg

npm install -g commitizen
npm install -g cz-conventional-changelog
npm install -g markdown-link-check
npm install -g markdownlint-cli2
