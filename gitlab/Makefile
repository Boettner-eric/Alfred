WORKFLOWS := $(HOME)/Library/Application Support/Alfred/Alfred.alfredpreferences/workflows
VENV      := .venv
PY        := $(VENV)/bin/python3

# If any step fails, remove $(PY) so a half-built venv isn't treated as current.
.DELETE_ON_ERROR:

# Rebuilt whenever requirements.txt changes. The touch is required because pip
# does not bump the interpreter's mtime, so make would otherwise reinstall on
# every invocation once requirements.txt is the newer file.
$(PY): requirements.txt
	rm -rf $(VENV)
	python3 -m venv $(VENV)
	$(PY) -m pip install --quiet --upgrade pip
	$(PY) -m pip install --quiet --requirement requirements.txt
	@touch $(PY)

venv: $(PY)

install: $(PY)
	ln -sfn "$(PWD)" "$(WORKFLOWS)/user.workflow.gitlab"

clean:
	rm -rf $(VENV)

.PHONY: venv install clean
