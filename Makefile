
SOURCES=latexbot.py

qa: $(SOURCES)
	flake8 $(SOURCES)
	pylint $(SOURCES)
