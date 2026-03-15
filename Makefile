.PHONY: fuzz analyze clean

fuzz:
	python fuzzer_numpy_vs_math.py corpus/

analyze:
	python analyzer_numpy_vs_math.py

clean:
	rm -rf corpus/ __pycache__ .pytest_cache
	rm -f differences.log fingerprints.txt
	rm -rf reports minimized_cases
