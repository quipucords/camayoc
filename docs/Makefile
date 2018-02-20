# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    = -W
SPHINXBUILD   = python -msphinx
SPHINXPROJ    = Camayoc
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean-api-docs:
	@rm -rf api/*

gen-api-docs: clean-api-docs
	@sphinx-apidoc -efMT -o api ../camayoc
	@sphinx-apidoc -efMT -o api ../tests
	@../scripts/gen_api_docs.sh

html: gen-api-docs
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

serve: html
	sphinx-serve

.PHONY: clean-api-docs gen-api-docs help html Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
