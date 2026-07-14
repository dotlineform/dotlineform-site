---
doc_id: sjt-explanation
title: "Minimal‑Change Permutations (SJT) — Explanation & Implementation"
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# Minimal‑Change Permutations (Steinhaus–Johnson–Trotter)

### Prompt & Timestamp

> Timestamp: Sunday, 31 August 2025 at 05:25 PM Prompt: Create an HTML explanation of the Steinhaus–Johnson–Trotter (SJT) minimal‑change permutation order, and show how it was implemented to generate the Excel file.

Download the Excel listing (3!–6!, SJT order, indexed):

Permutations_3to6_SJT_indexed.xlsx

**TL;DR:** The SJT algorithm lists permutations so that each successive permutation differs from the previous by a single *adjacent* swap — a permutation Gray code. This achieves the “minimum‑change” property.

## 1) Pseudocode (Concept)

```
# SJT for numbers 1..n
perm = [1..n]
dir = {k: LEFT for k in 1..n}   # each element has an arrow; initially LEFT
output perm

while True:
    i = largest_mobile_index(perm, dir)  # index of the largest mobile element
    if i == NONE: break                  # no mobile ⇒ done (all n! generated)
    x = perm[i]
    swap perm[i] with perm[i + dir[x]]   # one adjacent swap (minimal change)
    for y in (x+1..n): dir[y] = reverse(dir[y])  # flip directions of all > x
    output perm
```

## 2) Python Implementation Used for the Excel

A compact implementation matching the pseudocode was used to generate the permutations in SJT order:

```
def sjt(n):
    perm = list(range(1, n + 1))
    dir_map = {i: -1 for i in range(1, n + 1)}  # -1 = left, +1 = right
    result = [perm.copy()]

    def largest_mobile_index():
        idx = -1
        val = -1
        for i, x in enumerate(perm):
            d = dir_map[x]
            j = i + d
            if 0 <= j < n and perm[j] < x:     # mobile if within bounds & neighbor smaller
                if x > val:                    # keep the largest mobile value
                    val = x
                    idx = i
        return idx

    while True:
        i = largest_mobile_index()
        if i == -1:
            break
        x = perm[i]
        d = dir_map[x]
        j = i + d
        perm[i], perm[j] = perm[j], perm[i]  # adjacent swap
        for y in range(x + 1, n + 1):        # reverse directions of all elements > x
            dir_map[y] *= -1
        result.append(perm.copy())
    return result
```

### Mapping Steps

- **perm & dir:** `perm = [1..n]`, `dir_map` holds arrows (−1 left, +1 right).
- **Mobile element:** `x` is mobile if its arrow points to a smaller neighbor inside bounds.
- **Largest mobile:** choose the greatest-valued mobile element.
- **Adjacent swap:** swap `perm[i]` with `perm[i + dir[x]]`.
- **Flip directions:** for all `y > x`, multiply direction by −1.
- **Record:** append a copy of the permutation to the output list.

## 3) Example — n = 3

| Step | Permutation | Change from previous |
| --- | --- | --- |
| 1 | 123 | — |
| 2 | 132 | swap positions 2↔3 (2↔3) |
| 3 | 312 | swap positions 1↔2 (1↔3) |
| 4 | 321 | swap positions 2↔3 (1↔2) |
| 5 | 231 | swap positions 1↔2 (3↔2) |
| 6 | 213 | swap positions 2↔3 (3↔1) |

Each step differs by swapping two *adjacent* elements only (the minimum possible change).

## 4) Writing to Excel

1. For each `n` in 3..6, compute `seqs = sjt(n)`.
2. Create a sheet titled `“n!”`.
3. Write a header line like `“n! = len(seqs) sequences (SJT order: adjacent swap Gray code)”`.
4. Add columns `Index, Pos1, Pos2, …`, then write each permutation row.

Download the Excel (generated above):

Permutations_3to6_SJT_indexed.xlsx

## References

| Source | Description | URL |
| --- | --- | --- |
| Steinhaus–Johnson–Trotter algorithm (Wikipedia) | Overview and properties of the minimal‑change permutation order. | [https://en.wikipedia.org/wiki/Steinhaus%E2%80%93Johnson%E2%80%93Trotter_algorithm](https://en.wikipedia.org/wiki/Steinhaus%E2%80%93Johnson%E2%80%93Trotter_algorithm) |
| Permutation (MathWorld) | Background on permutations and factorial counts. | [https://mathworld.wolfram.com/Permutation.html](https://mathworld.wolfram.com/Permutation.html) |
| Ruskey, *Combinatorial Generation* | Chapters on permutation Gray codes and minimal‑change generation. | [https://page.math.tu-berlin.de/~felsner/SemWS17-18/Ruskey-Comb-Gen.pdf](https://page.math.tu-berlin.de/~felsner/SemWS17-18/Ruskey-Comb-Gen.pdf) |
| Cut‑the‑Knot: Johnson–Trotter | Intuitive explanation and relation to Gray codes. | [https://www.cut-the-knot.org/Curriculum/Combinatorics/JohnsonTrotter.shtml](https://www.cut-the-knot.org/Curriculum/Combinatorics/JohnsonTrotter.shtml) |

### APA‑style citations

Steinhaus–Johnson–Trotter algorithm. (n.d.). In *Wikipedia*. Retrieved August 31, 2025, from <https://en.wikipedia.org/wiki/Steinhaus%E2%80%93Johnson%E2%80%93Trotter_algorithm> Weisstein, E. W. (2003). Permutation. In *MathWorld—A Wolfram Web Resource*. Retrieved August 31, 2025, from <https://mathworld.wolfram.com/Permutation.html> Ruskey, F. (2003). *Combinatorial Generation*. Retrieved August 31, 2025, from <https://page.math.tu-berlin.de/~felsner/SemWS17-18/Ruskey-Comb-Gen.pdf> Bogomolny, A. (n.d.). Johnson–Trotter Algorithm: Listing All Permutations. *Cut‑the‑Knot*. Retrieved August 31, 2025, from <https://www.cut-the-knot.org/Curriculum/Combinatorics/JohnsonTrotter.shtml>
