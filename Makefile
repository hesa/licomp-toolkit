# SPDX-FileCopyrightText: 2024 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

clean:
	find . -name "*~" | xargs rm -f
	rm -fr licomp_toolkit.egg-info
	rm -fr build
	rm -fr dist sdist
	rm -fr licomp_toolkit/__pycache__
	rm -fr tests/python/__pycache__
	rm -fr .pytest_cache

.PHONY: build
build:
	rm -fr build && python3 setup.py sdist

lint:
	PYTHONPATH=. python3.11 -m flake8 licomp_toolkit

check_version:
	@echo -n "Checking api versions: "
	@MY_VERSION=`grep api_version licomp_toolkit/config.py | cut -d = -f 2 | sed -e "s,[ ']*,,g"` ; LICOMP_VERSION=`grep "licomp " requirements.txt | cut -d = -f 3 | sed -e "s,[ ']*,,g" -e "s,[ ']*,,g" -e "s,\(^[0-9].[0-9]\)[\.0-9\*]*,\1,g"` ; if [ "$$MY_VERSION" != "$$LICOMP_VERSION" ] ; then echo "FAIL" ; echo "API versions differ \"$$MY_VERSION\" \"$$LICOMP_VERSION\"" ; exit 1 ; else echo OK ; fi

unit-test:
	PYTHONPATH=. python3 -m pytest tests/python

unit-test-local:
	PYTHONPATH=.:../licomp:../licomp-reclicense:../licomp-osadl:../licomp-proprietary:../licomp-hermione:../licomp-dwheeler:../licomp-gnuguide python3 -m pytest

unit-test-local-verbose:
	PYTHONPATH=.:../licomp:../licomp-reclicense:../licomp-osadl:../licomp-proprietary:../licomp-hermione:../licomp-dwheeler:../licomp-gnuguide python3 -m pytest  --log-cli-level=10 tests

cli-test:
	tests/shell/test-cli.sh
	tests/shell/test_returns.sh

cli-test-local:
	tests/shell/test-cli.sh --local
	tests/shell/test_returns.sh --local

test: unit-test cli-test

test-local: unit-test-local cli-test-local

install:
	pip install .

reuse:
	reuse lint

check: clean reuse lint test check_version build
	@echo
	@echo
	@echo "All tests passed :)"
	@echo
	@echo

check-local: clean reuse lint test-local check_version build
	@echo
	@echo
	@echo "All (local) tests passed :)"
	@echo
	@echo

