"""Reproducible function-only comparison; verify with a slicing oracle first."""
import json
import platform
import random
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Python/source'))
import algorithms as a

rows = []
for case in ('random', 'repetitive'):
    for n in (500, 1500, 3000):
        m = n // 5
        seed = 404000 + n
        rng = random.Random(seed)
        text = ''.join(rng.choices('abcd', k=n)) if case == 'random' else 'a' * n
        pattern = text[n // 3:n // 3 + m] if case == 'random' else 'a' * m
        request = {'text': text, 'pattern': pattern}
        expected = [i for i in range(n - m + 1) if text[i:i + m] == pattern]
        for function in (a.naive, a.kmp, a.rk):
            assert function(request)['positions'] == expected
            function(request)  # one untimed warm-up; no JIT in this CPython build
            runs = []
            for _ in range(3):
                start = time.perf_counter_ns()
                result = function(request)
                elapsed = time.perf_counter_ns() - start
                assert result['positions'] == expected
                runs.append(elapsed / 1000000)
            rows.append({'case': case, 'n': n, 'm': m, 'seed': seed,
                         'algorithm': function.__name__, 'runs_ms': runs,
                         'median_ms': statistics.median(runs), 'matches': len(expected), 'verified': True})
report = {'runtime': sys.version, 'platform': platform.platform(),
          'scope': 'one function call, preprocessing and output allocation included; JSON, oracle, imports excluded',
          'warmup': 'one untimed call per algorithm/input after correctness check', 'rows': rows}
path = ROOT / 'tests/student/benchmark-results.json'
path.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
