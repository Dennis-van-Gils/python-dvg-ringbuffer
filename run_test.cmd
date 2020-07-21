@echo off
pytest --cov-report term-missing --cov=src -vv
coverage html
start htmlcov/index.html