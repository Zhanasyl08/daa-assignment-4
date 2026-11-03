"""Independent exhaustive/random oracles, witnesses, limits and JSONL reset tests."""
import json
import random
import subprocess
import sys
import unittest
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Python' / 'source'))
import algorithms as a


def occurrences(text, pattern):
    # Slicing is deliberately confined to the independent test oracle.
    return [i for i in range(len(text) - len(pattern) + 1)
            if text[i:i + len(pattern)] == pattern]


def subsequence(sequence, text):
    iterator = iter(text)
    return all(any(c == wanted for c in iterator) for wanted in sequence)


def merge_witness(sizes, result):
    blocks = [(i, i, size) for i, size in enumerate(sizes)]
    cost = 0
    for left, middle, right in result['plan']:
        i = next(i for i, b in enumerate(blocks) if b[:2] == (left, middle))
        assert i + 1 < len(blocks) and blocks[i + 1][:2] == (middle + 1, right)
        size = blocks[i][2] + blocks[i + 1][2]
        cost += size
        blocks[i:i + 2] = [(left, right, size)]
    assert len(blocks) == min(1, len(sizes))
    assert len(result['plan']) == max(0, len(sizes) - 1)
    assert cost == result['cost']


class AlgorithmsTest(unittest.TestCase):
    def test_lcs_exhaustive_witness(self):
        rng = random.Random(404)
        pairs = [('', ''), ('', 'abc'), ('abc', ''), ('ab', 'ba'), ('tea_time', 'team')]
        pairs += [(''.join(rng.choices('ab !', k=rng.randrange(9))),
                   ''.join(rng.choices('ab !', k=rng.randrange(9)))) for _ in range(100)]
        for x, y in pairs:
            options = [''.join(x[i] for i in range(len(x)) if mask >> i & 1)
                       for mask in range(1 << len(x))]
            optimum = max(len(s) for s in options if subsequence(s, y))
            result = a.lcs({'a': x, 'b': y})
            self.assertEqual(result['length'], optimum)
            self.assertEqual(len(result['sequence']), optimum)
            self.assertTrue(subsequence(result['sequence'], x) and subsequence(result['sequence'], y))

    def test_merge_all_chronological_choices(self):
        @lru_cache(None)
        def oracle(sizes):
            if len(sizes) < 2:
                return 0
            return min(sizes[i] + sizes[i + 1] + oracle(sizes[:i] +
                       (sizes[i] + sizes[i + 1],) + sizes[i + 2:])
                       for i in range(len(sizes) - 1))
        rng = random.Random(405)
        cases = [[], [0], [0] * 5, [1, 100, 1], [10**9] * 4]
        cases += [[rng.randrange(8) for _ in range(rng.randrange(8))] for _ in range(100)]
        for sizes in cases:
            result = a.merge({'sizes': sizes})
            self.assertEqual(result['cost'], oracle(tuple(sizes)))
            merge_witness(sizes, result)

    def test_tree_subset_oracle(self):
        rng = random.Random(406)
        for n in range(11):
            for _ in range(12):
                edges = [[i, rng.randrange(i)] for i in range(1, n)]
                weights = [rng.randrange(-5, 6) for _ in range(n)]
                best = max(sum(weights[i] for i in range(n) if mask >> i & 1)
                           for mask in range(1 << n)
                           if all(not (mask >> u & 1 and mask >> v & 1) for u, v in edges))
                result = a.tree({'n': n, 'edges': edges, 'weights': weights})
                chosen = set(result['selected'])
                self.assertEqual(len(chosen), len(result['selected']))
                self.assertTrue(all(0 <= i < n for i in chosen))
                self.assertTrue(all(u not in chosen or v not in chosen for u, v in edges))
                self.assertEqual(result['weight'], best)
                self.assertEqual(sum(weights[i] for i in chosen), best)

    def test_search_oracle(self):
        rng = random.Random(407)
        cases = [('', ''), ('', 'a'), ('abc', ''), ('a', 'long'),
                 ('aaaaa', 'aaa'), ('abdj', 'ab'), ('~ ! A a ~', '~'), ('Aa A!', 'A')]
        cases += [(''.join(rng.choices('abc ~!', k=rng.randrange(80))),
                   ''.join(rng.choices('abc ~!', k=rng.randrange(15)))) for _ in range(500)]
        for text, pattern in cases:
            expected = occurrences(text, pattern)
            for function in (a.naive, a.kmp, a.rk):
                self.assertEqual(function({'text': text, 'pattern': pattern})['positions'], expected)

    def test_suffix_direct_oracle(self):
        rng = random.Random(408)
        cases = ['', 'x', 'aaaaaa', 'banana', 'abcXYZ!', 'abXabYcdZcd']
        cases += [''.join(rng.choices('abc ~!', k=rng.randrange(55))) for _ in range(200)]
        for text in cases:
            result = a.suffix({'text': text})
            expected_sa = sorted(range(len(text)), key=lambda i: text[i:])
            expected_lcp = [0] * len(text)
            for j in range(1, len(text)):
                x, y = text[expected_sa[j - 1]:], text[expected_sa[j]:]
                h = 0
                while h < min(len(x), len(y)) and x[h] == y[h]:
                    h += 1
                expected_lcp[j] = h
            self.assertEqual(result['sa'], expected_sa)
            self.assertEqual(result['lcp'], expected_lcp)
            self.assertEqual(len(result['repeated']), max(expected_lcp, default=0))
            if result['repeated']:
                self.assertGreaterEqual(len(occurrences(text, result['repeated'])), 2)

    def test_aho_oracle_and_reset(self):
        rng = random.Random(409)
        cases = [([], ['', 'abc']), (['a'], []), (['he', 'she', 'he'], ['sheshe', '', 'sheshe']),
                 (['a', 'aa', 'aaa'], ['aaaa', 'aaaa', ''])]
        for _ in range(150):
            patterns = [''.join(rng.choices('ab ~', k=rng.randrange(1, 8))) for _ in range(rng.randrange(15))]
            texts = [''.join(rng.choices('ab ~', k=rng.randrange(60))) for _ in range(4)]
            cases.append((patterns, texts))
        for patterns, texts in cases:
            expected = [[len(occurrences(text, pattern)) for pattern in patterns] for text in texts]
            self.assertEqual(a.aho({'patterns': patterns, 'texts': texts})['counts'], expected)

    def test_full_domain_limits(self):
        self.assertEqual(a.lcs({'a': 'a' * 1000, 'b': 'a' * 1000}),
                         {'length': 1000, 'sequence': 'a' * 1000})
        sizes = [10**9] * 200
        result = a.merge({'sizes': sizes})
        # Optimal equal-leaf alphabetic tree: depths 7 and 8, external path length 1544.
        self.assertEqual(result['cost'], 1544 * 10**9)
        merge_witness(sizes, result)
        n = 100000
        result = a.tree({'n': n, 'weights': [10**9] * n,
                         'edges': [[i - 1, i] for i in range(1, n)]})
        self.assertEqual(result['weight'], 50000 * 10**9)
        chosen = set(result['selected'])
        self.assertEqual(len(chosen), 50000)
        self.assertTrue(all(i + 1 not in chosen for i in chosen))
        self.assertEqual(a.naive({'text': 'a' * 3000, 'pattern': 'a' * 1500})['positions'], list(range(1501)))
        self.assertEqual(a.kmp({'text': 'a' * 200000, 'pattern': 'a' * 100000})['positions'], list(range(100001)))
        self.assertEqual(a.rk({'text': 'a' * 10000, 'pattern': 'a' * 2000})['positions'], list(range(8001)))
        result = a.suffix({'text': 'a' * 50000})
        self.assertEqual(result['sa'], list(range(49999, -1, -1)))
        self.assertEqual(result['lcp'], list(range(50000)))
        self.assertEqual(result['repeated'], 'a' * 49999)
        # Maximum dictionary size/length, dense duplicates, 100 independent texts.
        result = a.aho({'patterns': ['a' * 10] * 10000, 'texts': ['a' * 2000] * 100})
        self.assertEqual(result['counts'], [[1991] * 10000 for _ in range(100)])
        # Maximum trie depth and state count, without recursive failure construction.
        result = a.aho({'patterns': ['a' * 100000], 'texts': ['a' * 200000]})
        self.assertEqual(result['counts'], [[100001]])

    def test_fixtures_and_mixed_jsonl(self):
        fixtures = json.loads((ROOT / 'tests/student/fixtures.json').read_text())
        requests = [case['input'] for case in fixtures] * 2
        process = subprocess.run([sys.executable, str(ROOT / 'Python/source/main.py')],
                                 input=''.join(json.dumps(r) + '\n' for r in requests),
                                 capture_output=True, text=True, timeout=20)
        self.assertEqual(process.returncode, 0, process.stderr)
        actual = [json.loads(line) for line in process.stdout.splitlines()]
        expected = [case['expected'] for case in fixtures] * 2
        self.assertEqual(actual, expected)
        report = [dict(case, actual=output) for case, output in zip(fixtures, actual)]
        (ROOT / 'tests/student/fixture-results.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    unittest.main(verbosity=2)
