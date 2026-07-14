---
doc_id: sjt-code
title: SJT Code
added_date: "2026-07-14 13:12"
last_updated: "2026-07-14 13:12"
parent_id: composites-engine
---
# SJT Code


## **Here’s a clear walkthrough of the SJT (Steinhaus–Johnson–Trotter) pseudocode and exactly how I implemented it to build your Excel.**
## 
**What the pseudocode says (conceptually)**
	1.	**Represent a permutation and directions**
	•	Keep the current permutation as a list: perm = [1, 2, ..., n].
	•	Give each element a “direction”: left = −1, right = +1. Initially, all point left.
	2.	**Mobile element**
	•	An element x is *mobile* if:
	•	its arrow points inside the array (not off the edge), and
	•	the neighbor in that direction is **smaller** than x.
	3.	**Find the largest mobile element**
	•	Among all mobile elements, choose the *largest value* x.
	4.	**Make one adjacent swap**
	•	Swap x with the neighbor it points to (so exactly one **adjacent** swap per step).
	•	This is the “minimal change” guarantee.
	5.	**Reverse directions of all elements larger than x**
	•	After the swap, for every element y with value > x, flip its arrow.
	6.	**Repeat**
	•	Output the new permutation.
	•	Stop when no element is mobile (you’ve generated all n! permutations).

⸻
## 
**How I implemented it (line-by-line mapping)**
## 
## **Below is the structure I used in Python to create the SJT order that fed into the Excel file.**
## 
**1) Function to generate SJT permutations**

def sjt(n):
    perm = list(range(1, n + 1))           *# perm = [1, 2, ..., n]*
    dir_map = {i: -1 for i in range(1, n + 1)}  *# -1 = left, +1 = right (all left at start)*
    result = [perm.copy()]                  *# store the initial permutation*

	•	Matches pseudocode “represent permutation and directions.”

    def largest_mobile_index():
        idx = -1
        val = -1
        for i, x in enumerate(perm):
            d = dir_map[x]
            j = i + d                       *# neighbor index in x's direction*
            if 0 <= j < n and perm[j] < x: *# check mobility (inside + neighbor smaller)*
                if x > val:                 *# keep the largest mobile*
                    val = x
                    idx = i
        return idx

	•	Implements “find the **largest mobile** element”:
	•	Checks mobility (bounds + neighbor smaller than x).
	•	Tracks the largest x (not the leftmost/rightmost; strictly the **largest value**).

    while True:
        i = largest_mobile_index()
        if i == -1:
            break                          *# no mobile → done (all n! generated)*
        x = perm[i]
        d = dir_map[x]
        j = i + d
        perm[i], perm[j] = perm[j], perm[i]  *# adjacent swap (minimal change)*

	•	Implements the **single adjacent swap**.

        for y in range(x + 1, n + 1):
            dir_map[y] *= -1               *# reverse direction of all elements > x*
        result.append(perm.copy())
    return result

	•	Implements the “reverse directions for all elements larger than x” step.
	•	Records each permutation to result.

That’s the entire SJT engine.

⸻
## 
**2) Building the Excel workbook (3! to 6!)**

wb = openpyxl.Workbook()
for n in range(3, 7):
    seqs = sjt(n)                          *# generate SJT order for this n*
    if n == 3:
        ws = wb.active
        ws.title = f"{n}!"
    else:
        ws = wb.create_sheet(title=f"{n}!")

    *# Header: show count and structure*
    ws.append([f"{n}! = {len(seqs)} sequences (SJT order: adjacent swap Gray code)"])
    ws.append([])

    *# Column headers: Index, Pos1..Posn*
    header = ["Index"] + [f"Pos{i+1}" for i in range(n)]
    ws.append(header)

    *# Write each permutation as one row in SJT order*
    for idx, seq in enumerate(seqs, start=1):
        ws.append([idx] + seq)

	•	For each n in 3..6:
	•	Calls sjt(n) (the algorithm above).
	•	Creates/renames the sheet to “n!”.
	•	Writes a readable header with the count (e.g., 6! = 720).
	•	Writes an Index column for reference.
	•	Splits each permutation into Pos1, Pos2, ... columns.
	•	The **order in the sheet is SJT order**, so each row differs from the previous by one adjacent swap.

excel_path = "/mnt/data/Permutations_3to6_SJT_indexed.xlsx"
wb.save(excel_path)

	•	Saves the workbook you downloaded.

⸻
## 
**Why this guarantees “minimal change”**
	•	Each step performs **exactly one swap**, and that swap is **adjacent**.
	•	Therefore, only two neighboring elements move, and everything else stays fixed—this is as small a change as possible between permutations.
	•	This is why SJT is known as a **permutation Gray code**.

⸻
## 
**Notes for your workflow**
	•	If you later want **lexicographic order** instead, you would use the “next permutation” algorithm (std::next_permutation style), but that does **not** guarantee adjacent swaps.
	•	If you want to scale to **7! (5040)** or **8! (40320)** in the same format, this SJT generator handles it; just be mindful of file size/performance.

If you want, I can regenerate the workbook including **7!** and add a small “Properties” row on each tab (e.g., “Adjacent swap per step: Yes / Gray code: Yes / Generator: SJT”).
