# N = number of chips (200 for a smoke run), SIZE = patch side after block averaging.
N ?= 1500
SIZE ?= 64
PY = .venv/bin/python

.PHONY: data features train evaluate export test all publish

data:
	N=$(N) SIZE=$(SIZE) $(PY) -m biomass.load

features:
	$(PY) -m biomass.features
	$(PY) -m biomass.split

train:
	$(PY) -m biomass.models

evaluate:
	MPLBACKEND=Agg $(PY) -m biomass.evaluate

export:
	MPLBACKEND=Agg $(PY) -m biomass.export

test:
	$(PY) -m pytest -q tests

all: data features train evaluate export

# Publish the static build (including web/public/data) to GitHub Pages from a gh-pages branch.
publish:
	cd web && npm run build && touch dist/.nojekyll
	cd web/dist && git init -q && git add -A && git commit -qm "Deploy" \
	  && git push -qf $$(git -C ../.. remote get-url origin) HEAD:gh-pages && rm -rf .git
