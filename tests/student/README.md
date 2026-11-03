# Additional tests and measurements

Run from the repository root with Python 3.12+:

    python tests/student/test_algorithms.py
    python tests/student/benchmark.py

The unittest suite checks independent small-instance oracles, reconstruction,
boundary cases, the full published input limits, and repeated JSONL requests.
fixtures.json and fixture-results.json record explicit protocol examples.
test-results.txt records the actual test run.

The benchmark uses deterministic random and repetitive inputs, checks outputs
against an independent oracle, warms up each function, and records three runs.
Results are saved to benchmark-results.json; the method, environment and
interpretation are documented in ANALYSIS.md.
