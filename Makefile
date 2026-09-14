# N = number of chips (200 for a smoke run), SIZE = patch side after block averaging.
N ?= 1500
SIZE ?= 64
PY = .venv/bin/python

.PHONY: data features train evaluate export test all

data:
	N=$(N) SIZE=$(SIZE) $(PY) -m biomass.load

features:
	$(PY) -m biomass.features
	$(PY) -m biomass.split

train:
	$(PY) -m biomass.models

evaluate:
	$(PY) -m biomass.evaluate

export:
	$(PY) -m biomass.export

test:
	$(PY) -m pytest -q tests

all: data features train evaluate export
