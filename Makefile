.PHONY: ready test package-check
ready: test

test:
	python3 -m unittest discover -s tests -v

package-check:
	PCDD_WHEEL_TEST=1 python3 -m unittest tests.test_packaging -v
