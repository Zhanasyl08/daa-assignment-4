"""Independent algorithms for the supplied Assignment 4 JSONL dispatcher."""
from array import array
from collections import deque


def lcs(request):
    a, b = request['a'], request['b']
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    result = []
    i, j = n, m
    while i and j:
        if a[i - 1] == b[j - 1]:
            result.append(a[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return {'length': dp[n][m], 'sequence': ''.join(reversed(result))}


def merge(request):
    sizes = request['sizes']
    n = len(sizes)
    if n < 2:
        return {'cost': 0, 'plan': []}
    prefix = [0]
    for size in sizes:
        prefix.append(prefix[-1] + size)
    dp = [[0] * n for _ in range(n)]
    split = [[0] * n for _ in range(n)]
    for width in range(2, n + 1):
        for left in range(n - width + 1):
            right = left + width - 1
            best = None
            for middle in range(left, right):
                candidate = dp[left][middle] + dp[middle + 1][right]
                if best is None or candidate < best:
                    best = candidate
                    split[left][right] = middle
            dp[left][right] = best + prefix[right + 1] - prefix[left]
    plan = []
    stack = [(0, n - 1, False)]
    while stack:
        left, right, ready = stack.pop()
        if left == right:
            continue
        middle = split[left][right]
        if ready:
            plan.append([left, middle, right])
        else:
            stack.extend([(left, right, True), (middle + 1, right, False),
                          (left, middle, False)])
    return {'cost': dp[0][n - 1], 'plan': plan}


def tree(request):
    n, weights = request['n'], request['weights']
    if not n:
        return {'weight': 0, 'selected': []}
    adjacency = [[] for _ in range(n)]
    for u, v in request['edges']:
        adjacency[u].append(v)
        adjacency[v].append(u)
    parent = [-1] * n
    order = [0]
    for u in order:
        for v in adjacency[u]:
            if v != parent[u]:
                parent[v] = u
                order.append(v)
    take, skip = weights.copy(), [0] * n
    for u in reversed(order[1:]):
        p = parent[u]
        take[p] += skip[u]
        skip[p] += max(take[u], skip[u])
    chosen = [False] * n
    selected = []
    for u in order:
        if (parent[u] == -1 or not chosen[parent[u]]) and take[u] > skip[u]:
            chosen[u] = True
            selected.append(u)
    return {'weight': max(take[0], skip[0]), 'selected': selected}


def naive(request):
    text, pattern = request['text'], request['pattern']
    n, m = len(text), len(pattern)
    positions = []
    for start in range(n - m + 1):
        j = 0
        while j < m and text[start + j] == pattern[j]:
            j += 1
        if j == m:
            positions.append(start)
    return {'positions': positions}


def kmp(request):
    text, pattern = request['text'], request['pattern']
    n, m = len(text), len(pattern)
    if not m:
        return {'positions': list(range(n + 1))}
    pi = [0] * m
    for i in range(1, m):
        j = pi[i - 1]
        while j and pattern[i] != pattern[j]:
            j = pi[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
        pi[i] = j
    positions = []
    j = 0
    for i, char in enumerate(text):
        while j and char != pattern[j]:
            j = pi[j - 1]
        if char == pattern[j]:
            j += 1
        if j == m:
            positions.append(i - m + 1)
            j = pi[j - 1]
    return {'positions': positions}


def rk(request):
    text, pattern = request['text'], request['pattern']
    n, m = len(text), len(pattern)
    if not m:
        return {'positions': list(range(n + 1))}
    if m > n:
        return {'positions': []}
    base, modulus = 31, 101
    high = pow(base, m - 1, modulus)
    target = window = 0
    for j in range(m):
        target = (target * base + ord(pattern[j])) % modulus
        window = (window * base + ord(text[j])) % modulus
    positions = []
    for start in range(n - m + 1):
        if window == target:
            j = 0
            while j < m and text[start + j] == pattern[j]:
                j += 1
            if j == m:
                positions.append(start)
        if start + m < n:
            window = ((window - ord(text[start]) * high) * base
                      + ord(text[start + m])) % modulus
    return {'positions': positions}


def suffix(request):
    text = request['text']
    n = len(text)
    if not n:
        return {'sa': [], 'lcp': [], 'repeated': ''}
    sa = list(range(n))
    rank = [ord(char) for char in text]
    width = 1
    while width < n:
        def key(i):
            return rank[i], rank[i + width] if i + width < n else -1
        sa.sort(key=key)
        new_rank = [0] * n
        for j in range(1, n):
            new_rank[sa[j]] = new_rank[sa[j - 1]] + (key(sa[j]) != key(sa[j - 1]))
        rank = new_rank
        if rank[sa[-1]] == n - 1:
            break
        width *= 2
    inverse = [0] * n
    for j, start in enumerate(sa):
        inverse[start] = j
    lcp = [0] * n
    height = best = best_start = 0
    for i in range(n):
        j = inverse[i]
        if j == 0:
            height = 0
            continue
        previous = sa[j - 1]
        while i + height < n and previous + height < n and text[i + height] == text[previous + height]:
            height += 1
        lcp[j] = height
        if height > best:
            best, best_start = height, i
        if height:
            height -= 1
    return {'sa': sa, 'lcp': lcp, 'repeated': text[best_start:best_start + best]}


def aho(request):
    patterns, texts = request['patterns'], request['texts']
    if not patterns:
        return {'counts': [[] for _ in texts]}
    if not texts:
        return {'counts': []}
    # Compact complete transition rows; no copied inherited output lists.
    alphabet = 95
    transitions = [array('i', [-1]) * alphabet]
    failure = [0]
    terminals = []
    for pattern in patterns:
        state = 0
        for char in pattern:
            code = ord(char) - 32
            child = transitions[state][code]
            if child == -1:
                child = len(transitions)
                transitions[state][code] = child
                transitions.append(array('i', [-1]) * alphabet)
                failure.append(0)
            state = child
        terminals.append(state)
    queue = deque()
    for code in range(alphabet):
        child = transitions[0][code]
        if child == -1:
            transitions[0][code] = 0
        else:
            queue.append(child)
    order = []
    while queue:
        state = queue.popleft()
        order.append(state)
        row, fallback = transitions[state], transitions[failure[state]]
        for code in range(alphabet):
            child = row[code]
            if child == -1:
                row[code] = fallback[code]
            else:
                failure[child] = fallback[code]
                queue.append(child)
    counts = []
    for text in texts:
        visits = [0] * len(transitions)
        state = 0
        for char in text:
            state = transitions[state][ord(char) - 32]
            visits[state] += 1
        for state in reversed(order):
            visits[failure[state]] += visits[state]
        counts.append([visits[state] for state in terminals])
    return {'counts': counts}
