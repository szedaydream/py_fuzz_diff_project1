.PHONY: fuzz analyze clean

fuzz:
	python fuzzer.py corpus/

analyze:
	python analyzer.py

clean:
	rm -rf corpus/ __pycache__ .pytest_cache
	rm -f differences.log fingerprints.txt
	rm -rf reports minimized_cases
