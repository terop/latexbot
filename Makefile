
SOURCES=latexbot.py

qa: $(SOURCES)
	flake8 $(SOURCES)
	pylint $(SOURCES)

build:
	docker build -t latexbot .
