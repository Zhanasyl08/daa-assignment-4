# Assignment 4 — Python analysis

## Environment and reproduction

Language: Python. Actual local runs used CPython 3.12.10, 64-bit AMD64,
Windows 10 build 19045, Intel Core i7-1065G7 @ 1.30 GHz, 8,361,132,032 bytes
physical RAM (approximately 7.79 GiB). Measurements were taken on a shared
interactive laptop, without CPU pinning; scheduling noise is expected.
Python arbitrary-precision integers preserve all required costs and counts.
No external dependencies or algorithm libraries are required.

From the repository root, with Python 3.12+ on PATH:

```sh
python tools/run.py --setup
python tools/run.py --check
python tools/run.py --input examples/lcs.jsonl
python tests/student/test_algorithms.py
python tests/student/benchmark.py
```

The actual local command prefix was `../python312/python.exe`, an isolated
official Python 3.12.10 embedded runtime outside the repository. Its `_pth`
included this repository's `tools` and `Python/source` directories, so the
unchanged template dispatcher and launcher could import their sibling modules.
An ordinary Python installation does not need that embedded-runtime adjustment.
There is no separate compilation stage for this implementation. The supplied
JSONL transport is unchanged: one result per request, with all algorithm state
created inside the request function.

## Algorithms and correctness

### LCS

`dp[i][j]` is the maximum common-subsequence length of prefixes `a[:i]` and
`b[:j]`. Row and column zero are zero. Equal final characters extend the optimum
diagonal by one; otherwise the optimum is the larger of deleting the final
character from either prefix. A common subsequence cannot use two unequal final
characters as one match, so those two alternatives cover every optimum.
Rows and columns increase, making the previous row and previous column ready.

Backtracking starts at the full prefixes. Equal characters are appended and
both indices decrease; on mismatch the larger predecessor is followed. On a tie
the upper predecessor is chosen. Each step preserves an optimal remaining
subproblem, and reversing the collected characters restores their original
order. Empty prefixes terminate immediately. Time and auxiliary storage are
O((n+1)(m+1)); reconstruction costs O(n+m), with O(min(n,m)+1) output.
The `ab`/`ba` test accepts a length-one optimum; exhaustive subsequences check
that the witness is valid rather than requiring one arbitrary tie resolution.

### Ordered adjacent merging

`dp[l][r]` is the minimum cost to collapse the closed original interval `[l,r]`.
A singleton costs zero. In any final merge there is a split `k` separating
`[l,k]` and `[k+1,r]`; therefore
`dp[l][r] = min_k(dp[l][k]+dp[k+1][r]) + prefix[r+1]-prefix[l]`.
Increasing interval width makes both children available. Every valid final
merge has one such split, and combining optimal children gives a valid plan,
proving optimality by induction on width. The first minimizing split wins ties.

An explicit stack performs postorder reconstruction: both children are output
before `[l,k,r]`. Thus the two current blocks exist and are adjacent at each step.
There are n-1 operations. Zero or one block returns no operations and cost zero.
Time is O(n^3), auxiliary memory O(n^2), output O(n); n=0 takes O(1).
The `[1,100,1]` test distinguishes adjacent merging (203) from illegal arbitrary
merging. A separate oracle enumerates chronological adjacent choices, and a
simulation checks each returned operation and recomputes its cost.

### Maximum-weight independent set on a tree

Root at zero. An iterative parent-before-child traversal builds `order` and
`parent`, avoiding recursion at n=100000. `take[u]` includes u and therefore
adds only `skip[child]`; `skip[u]` adds `max(take[child],skip[child])`.
The arrays start at the vertex weights and zero, respectively. Reversing the
traversal lets each child contribute its completed pair to its parent.
Conditional on selecting or excluding u, different child subtrees have no
remaining connecting edges, so their optima add independently. These two states
exhaust the possibilities and establish correctness by subtree induction.

Reconstruction traverses parents first. A selected parent forces exclusion;
otherwise u is selected exactly when `take[u] > skip[u]`. Ties are excluded.
The choices attain the corresponding DP state and never select both ends of
an edge. The empty set remains possible for all-negative weights. An empty
tree returns zero and an empty list. Time, auxiliary storage and worst-case
output size are O(n+1). Small subset enumeration validates optimality; the
100000-vertex chain tests stack safety and a total weight of 50,000,000,000,000.

### Naive search

For every start from zero through n-m, j counts the prefix already verified
equal to the text window. A mismatch rejects the window; j=m proves a match.
Every possible start is visited once in increasing order, so overlaps are
retained. If m=0 the comparison loop is empty and all n+1 boundaries are added;
if m>n the outer range is empty. Time O(n*m+n+1), auxiliary memory O(1), and
output O(z+1). The empty pattern in `ab` must return `[0,1,2]`, including the
final boundary. No built-in substring search is used in this algorithm.

### KMP

`pi[i]` is the longest proper prefix of the pattern that is also a suffix of
`pattern[:i+1]`. Starting from `pi[i-1]`, a mismatch shortens the candidate to
`pi[j-1]`. Those borders contain every possible shorter candidate; a matching
character extends the candidate by one. Prefix lengths are computed left to
right. During search, j is the longest pattern prefix matching a suffix of the
text processed so far. The same border fallback preserves that invariant.
At j=m a full match ends at i; report i-m+1 and fall back to `pi[m-1]` so
overlapping matches remain possible. Empty patterns are handled before indexing.

Each successful extension increases j by at most one, while fallback strictly
decreases it, giving amortized O(n+m+z+1) time. Auxiliary memory O(m+1), output
O(z+1). The `abababa`/`aba` test expects `[0,2,4]`. A slicing oracle, confined
to tests, checks random inputs independently of the three implementations.

### Exact Rabin–Karp

Use ASCII codes, base 31 and modulus 101. The leftmost character has power m-1.
Pattern and initial window hashes are accumulated left to right. With
`high=31^(m-1) mod 101`, update by
`((window-ord(outgoing)*high)*31+ord(incoming)) % 101`.
Python's positive-modulus remainder is nonnegative. Algebraically this removes
the outgoing term and shifts the remaining polynomial before appending the new
character, preserving the window-hash invariant. Unequal hashes cannot represent
equal strings; equal hashes are only candidates and are verified character by
character. Consequently collisions cannot introduce false matches.

Empty patterns return n+1 boundaries; m>n returns an empty result before a
window is formed. For 1<=m<=n the bound is O(n+m+c*m), where c is the number of
equal-hash windows; the general bound is O(n*m+n+m+1). Auxiliary memory is O(1)
besides integer arithmetic under the published limits, and output is O(z+1).
This is not deterministic linear-time search. `ab` and `dj` both hash to 75;
searching `abdj` for `ab` must return only zero.

### Suffix array and Kasai LCP

Initially ranks are ASCII codes. At doubling width w, sort suffix starts by
`(rank[i], rank[i+w])`, using -1 beyond the end. The ranks describe the first w
characters; a pair therefore orders the first 2w characters, with the missing
second part smaller than any actual character. Equal pairs receive the same
new rank, others consecutive increasing ranks. Induction on doubling rounds
shows ranks describe ever longer prefixes. Stop when all ranks are distinct
or w reaches n: the ordering is then the complete suffix order. Only indices
and rank pairs are sorted, never materialized suffix strings. Python's
comparison-based `list.sort` gives O(n log^2(n+1)) worst-case time, O(n+1)
auxiliary storage. The output omits any sentinel and the empty suffix.

Kasai uses inverse suffix ranks. For each text start i, compare against the
previous suffix in sorted order, starting at the carried height h. Removing
the first character from a common prefix leaves at least h-1 characters;
the predecessor ordering ensures this is a lower bound for the next comparison.
Decrease h by one after processing, or reset it at the smallest suffix.
The number of increments is linear, so Kasai costs O(n) time and O(n) storage.
`lcp[0]=0`; lcp[j] compares sa[j-1] and sa[j].

Suffixes sharing a prefix form a contiguous lexicographic interval. Thus any
repeated substring is a prefix of some adjacent suffix pair; the maximum
adjacent LCP is a longest repeat. The first maximum encountered during Kasai
is returned, with overlap allowed. Empty input returns empty arrays/string;
one character returns `[0]`, `[0]`, and an empty repeat. Output is O(n+1).
Small direct suffix sorting tests order and LCP independently; `a` repeated
50000 times requires descending sa, lcp 0..49999, and repeat length 49999.

### Aho–Corasick

Each trie state represents a dictionary prefix. Duplicate patterns share the
same terminal state but retain a separate entry in `terminals`, preserving
column order. Transition rows are compact `array('i')` arrays of 95 entries,
indexed by ASCII code minus 32. Breadth-first construction sets each failure
link to the longest proper suffix that is a trie prefix. Missing transitions
use the already completed failure state's transition. Root missing edges loop
to root, and depth-one failure links are root. Breadth-first order guarantees
that the shorter fallback state's transitions are ready.

The scan state is the longest dictionary-prefix suffix of the processed text.
Increment its visit count at each position. Reverse breadth-first propagation
adds each count to its failure parent. Every terminal on the failure chain is
a pattern ending at that position, so its propagated count includes all and
only its occurrences, including overlaps and suffix patterns. No inherited
output lists or individual match records are copied. State and visits reset
for every text. Terminal lookup duplicates counts into original dictionary
positions. Empty texts produce zero rows; an empty dictionary yields an empty
row per text; no texts yields an empty outer list.

Let L be total dictionary length including duplicates, p its size, S trie
states including root, q texts, and T total text length. Construction takes
O(L+95S+p) time and O(95S+p) auxiliary storage; scans plus propagation take
O(T+q(S+p)). Output takes O(q(p+1)+1). Empty collections are handled directly.
Tests include duplicate `he`, suffix `she`, repeated independent texts, dense
matches with 10000 duplicate patterns, and a 100000-character single pattern.

## Own tests and actual results

The test suite passed all eight test methods in 12.796 seconds on the environment
above. It contains hundreds of deterministic randomized inputs, independent
small oracles, witness simulation, full-limit cases and a mixed JSONL subprocess.
See `tests/student/test-results.txt` for the actual run. The official launcher
passed setup, all 44 public cases, and two complete public batches in one process.
These are verification results, not a claim about an unseen grading score.

`fixtures.json` contains exact inputs and expected results;
`fixture-results.json` records the actual outputs from the JSONL subprocess.
For general nonunique optima the larger oracle suite checks optimality and
validity instead of requiring the fixture's particular tie-breaking choice.

|Command|Fixture/input|Expected|Actual|Defect detected|
|---|---|---|---|---|
|lcs|`ab`, `ba`|length 1, valid common character|`1, a`|invalid reconstruction/ties|
|merge|`[1,100,1]`|203, valid adjacent plan|203; `[1,1,2]`, `[0,0,2]`|nonadjacent greedy merges|
|tree|chain, weights -1,-2,-3|0, empty|0, empty|forcing a negative selection|
|naive|`ab`, empty pattern|0,1,2|0,1,2|missing final boundary|
|kmp|`abababa`, `aba`|0,2,4|0,2,4|losing overlaps|
|rk|`abdj`, `ab`|0|0|accepting a hash collision|
|suffix|`banana`|sa 5,3,1,0,4,2; lcp 0,1,3,0,0,2; ana|exact match|sentinel, LCP indexing, overlaps|
|aho|he,she,he; sheshe,empty,sheshe|2,2,2 / 0,0,0 / 2,2,2|exact match|suffix counts, duplicates, stale state|

Full-limit checks assert known results, not merely successful termination:
1000x1000 LCS; 200 equal billion-size blocks (cost 1544 billion, checked plan);
100000-vertex chain; maximum naive/KMP/RK inputs with overlaps;
50000 identical suffix characters; dense 100-text/10000-pattern Aho output;
and 100001 trie states. For equal 200-leaf merging, an optimal alphabetic tree
has 56 leaves at depth 7 and 144 at depth 8, giving external path length 1544.
Small merge tests instead enumerate every chronological adjacent choice.

## Reproducible search comparison

`tests/student/benchmark.py` generates all inputs and writes raw measurements
to `benchmark-results.json`. For n=500,1500,3000, m=n//5. Random cases use
`random.Random(404000+n).choices('abcd', k=n)` and take a guaranteed-occurring
pattern from `text[n//3:n//3+m]`. Repetitive cases use `a` repeated n and m
times. Both dimensions satisfy all three algorithms' domains. Every method
first matches an independent slicing oracle, and every measured result is
checked again outside the timing interval.

The same `perf_counter_ns` boundary encloses one function call, including
preprocessing and returned-output allocation, for each method. Imports, JSON,
input generation, validation and compilation are excluded. One untimed warm-up
call follows the correctness call. CPython 3.12 has no JIT here. Three measured
runs and their median are reported in milliseconds below; there is no timing
threshold test. Scheduling and laptop power management make the raw runs noisy.

|Case|n|m|Seed|Method|Run 1 ms|Run 2 ms|Run 3 ms|Median ms|Verified|
|---|---:|---:|---:|---|---:|---:|---:|---:|---|
|random|500|100|404500|naive|0.0952|0.0930|0.0828|0.0930|yes|
|random|500|100|404500|kmp|0.0689|0.0679|0.0663|0.0679|yes|
|random|500|100|404500|rk|0.2122|0.2293|0.2680|0.2293|yes|
|random|1500|300|405500|naive|0.3933|0.3346|0.3448|0.3448|yes|
|random|1500|300|405500|kmp|0.4499|0.4019|0.4445|0.4445|yes|
|random|1500|300|405500|rk|0.7739|0.8751|2.5650|0.8751|yes|
|random|3000|600|407000|naive|0.8433|1.1716|0.9066|0.9066|yes|
|random|3000|600|407000|kmp|0.9077|0.9417|1.2947|0.9417|yes|
|random|3000|600|407000|rk|1.6556|1.6656|1.1636|1.6556|yes|
|repetitive|500|100|404500|naive|6.4870|7.1861|5.8688|6.4870|yes|
|repetitive|500|100|404500|kmp|0.1066|0.1058|0.1158|0.1066|yes|
|repetitive|500|100|404500|rk|8.1434|8.1462|5.5483|8.1434|yes|
|repetitive|1500|300|405500|naive|60.1835|55.1652|63.4466|60.1835|yes|
|repetitive|1500|300|405500|kmp|0.7225|1.4439|1.2046|1.2046|yes|
|repetitive|1500|300|405500|rk|121.6259|101.3978|111.7868|111.7868|yes|
|repetitive|3000|600|407000|naive|459.4445|362.3341|331.5217|362.3341|yes|
|repetitive|3000|600|407000|kmp|1.7980|1.8754|4.4006|1.8754|yes|
|repetitive|3000|600|407000|rk|255.4997|303.7138|378.1782|303.7138|yes|

Random inputs usually reject naive windows after few comparisons, so KMP's
stronger worst-case guarantee does not imply it is always faster on these
small random instances. In these measurements the largest random case had
naive and KMP medians close to each other, while RK paid for modular updates.
On repetitive inputs every window is a real match: naive and exact RK verify
many m-character windows, whereas KMP reuses borders. At n=3000 the measured
medians were approximately 362.334 ms (naive), 1.875 ms (KMP), and 303.714 ms
(RK). These observations are consistent with, but do not prove, the bounds.
RK's modulus 101 is a deliberate collision laboratory; production hashes may
use much larger moduli or multiple fingerprints. That can reduce accidental
candidates but does not eliminate exact verification costs on genuine dense
matches. The `ab`/`dj` test separately checks collision correctness.

## Sources and AI assistance

- Official starter, contracts, rubric, testing guide and supplied public checks:
  https://github.com/RZhaniya/daa-assignment-4-archive (template revision
  `4686cc60334aa189c2ac168e10a82d882b32858c`). The JSONL dispatcher and public
  validation tools are supplied course code and remain unchanged.
- Course lesson/practice reference: https://rzhaniya.github.io/daa-assignment-4-archive/.
- OpenAI Codex assisted substantially: it implemented the eight Python functions,
  wrote independent test oracles and stress tests, ran the commands and benchmarks,
  and drafted this explanation. The verification evidence above records actual
  tool-executed runs. It does not claim that the student personally performed
  those runs or independently authored the generated code. The student should
  review, reproduce and understand the solution before submission and defence.
- No assessed defence questions were accessed or answered. No algorithm library
  or built-in substring-search function replaces a required implementation;
  slicing and direct suffix sorting are used only in independent small test oracles.
