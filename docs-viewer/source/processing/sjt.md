---
doc_id: sjt
title: SJT
added_date: "2026-07-14 13:12"
last_updated: "2026-07-14 13:12"
parent_id: composites-engine
---
# SJT



```
How can the sequence of permutations be sorted so that a minimum of numbers change position in the sequence with each successive permutation?

```


You’re looking for a **minimal-change ordering of permutations**—often called a **permutation Gray code**—where each step changes as little as possible from the previous one.

**Best-known solution: Steinhaus–Johnson–Trotter (SJT)**

SJT generates all permutations using **one adjacent swap** at each step. That means:
	•	Exactly **two elements move** each step.
	•	And they move **by one position** (adjacent transposition) — the smallest possible change.

**How SJT works (conceptual)**
	1.	Start with 1 2 3 … n, and give every number a direction (initially **left**).
	2.	A number is **mobile** if its arrow points to a smaller neighbor.
	3.	At each step:
	•	Find the **largest mobile** number.
	•	**Swap** it with the neighbor it points to (one adjacent swap).
	•	**Reverse the direction** of all numbers **larger** than the one you just moved.
	4.	Repeat until no number is mobile → you’ve listed all n! permutations.

**Example (n = 4, first few in SJT order)**

1234
2134  (swap 1←2)
2314  (swap 3←1)
2341  (swap 4←1)
3241  (swap 3→4)
3421  (swap 4→2)
...

Each line differs from the previous by a **single adjacent swap**.

**Why this is “minimum change”**
	•	Any two distinct permutations must differ in at least **one swap**.
	•	SJT ensures exactly **one** swap per step, and it’s **adjacent**, so positions change by the minimal distance possible.

**Alternative note: Heap’s algorithm**

Heap’s algorithm also does **one swap per permutation**, but the swap isn’t guaranteed to be adjacent. SJT is stricter (and usually what people mean by “minimum change”).



```
Explain the pseudo code. How was it implemented when creating the Excel file?

```

Here’s a clear walkthrough of the **SJT (Steinhaus–Johnson–Trotter)** pseudocode and exactly how I implemented it to build your Excel.

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

**How I implemented it (line-by-line mapping)**

Below is the structure I used in Python to create the SJT order that fed into the Excel file.

**1) Function to generate SJT permutations**


```
def sjt(n):
    perm = list(range(1, n + 1))           # perm = [1, 2, ..., n]
    dir_map = {i: -1 for i in range(1, n + 1)}  # -1 = left, +1 = right (all left at start)
    result = [perm.copy()]                  # store the initial permutation

```


	•	Matches pseudocode “represent permutation and directions.”


```
    def largest_mobile_index():
        idx = -1
        val = -1
        for i, x in enumerate(perm):
            d = dir_map[x]
            j = i + d                       
```


```
*# neighbor index in x's direction*
```


```

            if 0 <= j < n and perm[j] < x: 
```


```
*# check mobility (inside + neighbor smaller)*
```


```

                if x > val:                 
```


```
*# keep the largest mobile*
```


```

                    val = x
                    idx = i
        return idx

```


	•	Implements “find the **largest mobile** element”:
		•	Checks mobility (bounds + neighbor smaller than x).
		•	Tracks the largest x (not the leftmost/rightmost; strictly the **largest value**).


```
    while True:
        i = largest_mobile_index()
        if i == -1:
            break                          
```


```
*# no mobile → done (all n! generated)*
```


```

        x = perm[i]
        d = dir_map[x]
        j = i + d
        perm[i], perm[j] = perm[j], perm[i]  
```


```
*# adjacent swap (minimal change)*
```


```


```


	•	Implements the **single adjacent swap**.


```
        for y in range(x + 1, n + 1):
            dir_map[y] *= -1               
```


```
*# reverse direction of all elements > x*
```


```

        result.append(perm.copy())
    return result

```


	•	Implements the “reverse directions for all elements larger than x” step.
	•	Records each permutation to result.

That’s the entire SJT engine.

⸻

**2) Building the Excel workbook (3! to 6!)**


```
wb = openpyxl.Workbook()
for n in range(3, 7):
    seqs = sjt(n)                          
```


```
*# generate SJT order for this n*
```


```

    if n == 3:
        ws = wb.active
        ws.title = f"{n}!"
    else:
        ws = wb.create_sheet(title=f"{n}!")

    
```


```
*# Header: show count and structure*
```


```

    ws.append([f"{n}! = {len(seqs)} sequences (SJT order: adjacent swap Gray code)"])
    ws.append([])

    
```


```
*# Column headers: Index, Pos1..Posn*
```


```

    header = ["Index"] + [f"Pos{i+1}" for i in range(n)]
    ws.append(header)

    
```


```
*# Write each permutation as one row in SJT order*
```


```

    for idx, seq in enumerate(seqs, start=1):
        ws.append([idx] + seq)

```


	•	For each n in 3..6:
		•	Calls sjt(n) (the algorithm above).
		•	Creates/renames the sheet to “n!”.
		•	Writes a readable header with the count (e.g., 6! = 720).
		•	Writes an Index column for reference.
		•	Splits each permutation into Pos1, Pos2, ... columns.
		•	The **order in the sheet is SJT order**, so each row differs from the previous by one adjacent swap.


```
excel_path = "/mnt/data/Permutations_3to6_SJT_indexed.xlsx"
wb.save(excel_path)

```


	•	Saves the workbook you downloaded.

⸻

**Why this guarantees “minimal change”**
	•	Each step performs **exactly one swap**, and that swap is **adjacent**.
	•	Therefore, only two neighboring elements move, and everything else stays fixed—this is as small a change as possible between permutations.
	•	This is why SJT is known as a **permutation Gray code**.

⸻

**Notes for your workflow**
	•	If you later want **lexicographic order** instead, you would use the “next permutation” algorithm (std::next_permutation style), but that does **not** guarantee adjacent swaps.
	•	If you want to scale to **7! (5040)** or **8! (40320)** in the same format, this SJT generator handles it; just be mindful of file size/performance.



```
What strategies can be employed to select a sub set of permutations for n=7 and above?

```


Great question  <span style="font-family: .AppleColorEmojiUI;">
     👌
 </span> — for **n = 7 and above** the number of permutations becomes enormous:
	•	7! = **5,040**
	•	8! = **40,320**
	•	9! = **362,880**
	•	10! = **3,628,800**
…and so on.

Clearly, it’s not feasible to use all of them (e.g., at 25 fps, 9! frames would last **over 4 hours**, and 10! would run for **40+ hours**).
So you need strategies to **select a subset** of permutations that still capture the structure or variety you want.

⸻

 <span style="font-family: .AppleColorEmojiUI;">
     🔹
 </span> **Strategies for Selecting a Subset of Permutations**

**1. Stride / Skip Selection**
	•	Choose every *kth* permutation in a fixed order (e.g., lexicographic or SJT).
	•	Example: stride = 10 → take permutations 1, 11, 21, …
	•	Pros: evenly spaced through the sequence, predictable.
	•	Cons: may miss local patterns if order has structure.

⸻

**2. Random Sampling**
	•	Randomly pick m permutations out of the full set.
	•	Options:
	•	**Uniform random** (every permutation equally likely).
	•	**Seeded random** (reproducible, using a fixed random seed).
	•	Pros: easy, scalable, can capture variety.
	•	Cons: no guarantee of coverage or smooth transitions between frames.

⸻

**3. Gray-Code / Minimal-Change Walk**
	•	Instead of taking arbitrary subsets, follow a **Gray code order** (like SJT) but stop after m permutations.
	•	Ensures **smooth transitions** (only adjacent swaps between successive selections).
	•	Pros: minimal-change, visually coherent.
	•	Cons: sequence length still grows factorially; you must choose where to stop or skip.

⸻

**4. Factorial Number System / Ranking & Unranking**
	•	Each permutation has a unique **index** in factorial number system representation.
	•	You can directly jump to permutation k without generating all prior ones.
	•	Strategy: select permutations corresponding to indices spaced evenly across [0, n! – 1].
	•	Pros: efficient, good coverage.
	•	Cons: requires implementing ranking/unranking.

⸻

**5. Combinatorial Substructures**
	•	Instead of sampling the full n!, restrict to subsets with special properties:
	•	**Derangements** (no element in its original position).
	•	**Cyclic shifts** of a base permutation.
	•	**Symmetry groups** (select one from each equivalence class under symmetry).
	•	Pros: can capture interesting mathematical properties.
	•	Cons: reduces variety, but may be exactly what you want.

⸻

**6. Hybrid Approaches**
	•	Combine structured selection + randomness:
	•	Use stride sampling for coverage.
	•	Then shuffle selections randomly to avoid regularity.
	•	Or cluster permutations (by Hamming distance or inversion count) and sample evenly from each cluster.

⸻

 <span style="font-family: .AppleColorEmojiUI;">
     🔹
 </span> **Practical Example for n = 7 (5,040 permutations)**

Suppose you only want ~500 frames (~20 seconds at 25fps):
	•	Use **stride = 10** → take every 10th permutation in lexicographic order.
	•	Or **random sample 500** with a fixed seed (reproducible).
	•	Or take **first 500 SJT-order permutations** for a smooth, adjacent-swap progression.

⸻

 <span style="font-family: .AppleColorEmojiUI;">
     ✅
 </span> **Summary**
	•	If you want **coverage** → stride or factorial indexing.
	•	If you want **variety** → random or hybrid sampling.
	•	If you want **smoothness** → Gray-code (SJT) truncation.
	•	If you want **mathematical elegance** → special subsets (derangements, cyclic groups).




```
Add duration columns. Include notes column to explain strategy 

```

Added duration columns + notes ✅
	•	 <span style="font-family: .AppleColorEmojiUI;">
     📊
 </span> **Updated workbook (with durations & notes):**
[Download permutation_subsets_n7_n8_with_durations.xlsx](sandbox:/mnt/data/permutation_subsets_n7_n8_with_durations.xlsx?_chatgptios_conversationID=68b1ad0d-91d4-8333-a1e8-222d9d38b552&_chatgptios_messageID=0326a33f-e65c-43f0-8d2b-9e8ea31e4e85)

What changed:
	•	**Summary** now includes **Count (frames)**, **Duration @25fps (minutes)**, and a **Notes** column describing each strategy.
	•	Every detailed sheet starts with a **Duration @25fps** line (e.g., “500 frames ≈ 0.333 minutes”), plus a **Notes** column in the table header reiterating the strategy:
	•	**SJT_first_500** — “Adjacent-swap Gray code; smooth motion.”
	•	**Lexi_stride_10** — “Every 10th permutation in lexicographic order.”
	•	**Lexi_random_500** — “Uniform random sample; reproducible via seed.”
	•	**Lexi_spaced_500** — “Evenly spaced indices from full range.”
	•	**Derangements_7** — “No fixed points.”
	•	**HammingBalanced_500** — “Greedy farthest-point in Hamming space.”
	•	**Derangements_8** — “No fixed points.”

Want any alternate frame rates (e.g., **24 fps** or **30 fps**) added as extra columns?


```
Yes, including 24, 30, 60. What is the visual difference between these frame rates? Download explanation 

```

Great — let’s handle both parts:

⸻

 <span style="font-family: .AppleColorEmojiUI;">
     🔹
 </span> **Visual Differences Between Frame Rates**
	•	**24 fps (film standard)**
	•	Classic cinema look (slight motion blur & stutter).
	•	Human brain interprets this as “cinematic” because it’s been the standard for decades.
	•	Best for storytelling and drama; motion feels a little less smooth.
	•	**25 fps (PAL/European video standard)**
	•	Similar to 24 fps, slightly smoother.
	•	Standard for broadcast in many countries.
	•	Often interchangeable with 24 fps for artistic purposes.
	•	**30 fps (NTSC/US video standard)**
	•	Noticeably smoother than 24/25 fps.
	•	Feels more “realistic” and closer to live television.
	•	Good for news, sports, or YouTube content where clarity matters.
	•	**60 fps (high frame rate)**
	•	Extremely smooth and fluid.
	•	Excellent for sports, gaming, or fast-moving visuals.
	•	Can feel “too real” or “soap opera effect” in narrative film (some viewers dislike it).
	•	Doubles temporal resolution compared to 30 fps, so fast motion is very clear.

👉 In practice:
	•	**24 fps** = cinematic, artistic.
	•	**25 fps** = broadcast European video.
	•	**30 fps** = realistic, crisp, “live TV.”
	•	**60 fps** = ultra-smooth, immersive, hyper-realistic.

⸻

 <span style="font-family: .AppleColorEmojiUI;">
     🔹
 </span> **Next Step for Excel**

I’ll regenerate the workbook to include **extra duration columns** for 24, 25, 30, and 60 fps (so you can compare directly). Each sheet and the Summary will show durations at all four frame rates.

⸻

All set ✅
	•	 <span style="font-family: .AppleColorEmojiUI;">
     📊
 </span> **New Excel (with 24/25/30/60 fps durations):**
[Download permutation_subsets_fps_24_25_30_60.xlsx](sandbox:/mnt/data/permutation_subsets_fps_24_25_30_60.xlsx?_chatgptios_conversationID=68b1ad0d-91d4-8333-a1e8-222d9d38b552&_chatgptios_messageID=ab631fc3-cd44-4f8b-800e-b5892e95b31d)
What’s inside:
	•	**Summary** with frame counts and **durations at 24/25/30/60 fps** + notes for each strategy.
	•	Strategy tabs (each includes a “Durations — …” line and a **Notes** column):
	•	**SJT_first_500** (minimal-change adjacent swaps)
	•	**Lexi_stride_10** (every 10th in lexicographic order)
	•	**Lexi_random_500** (seed=42)
	•	**Lexi_spaced_500** (evenly spaced indices)
	•	**Derangements_7** (all !7 = 1,854)
	•	**HammingBalanced_500** (greedy farthest-point in Hamming distance)
	•	**Derangements_8** (all !8 = 14,833)
	•	 <span style="font-family: .AppleColorEmojiUI;">
     📄
 </span> **HTML explanation (visual differences + formulas + link):**
[Download frame_rate_and_subsets_explainer.html](sandbox:/mnt/data/frame_rate_and_subsets_explainer.html?_chatgptios_conversationID=68b1ad0d-91d4-8333-a1e8-222d9d38b552&_chatgptios_messageID=ab631fc3-cd44-4f8b-800e-b5892e95b31d)



```
To summarise, for n=9, what is the best strategy to use in order to produce a 1 minuite video 

```


Here’s the short, practical answer for **n = 9** (there are 9! = 362{,}880 permutations):

**Best strategy: SJT (minimal-change) truncation**

Use the **Steinhaus–Johnson–Trotter (SJT)** order and take only the first **N** permutations you need for a **60-second** video. SJT changes each frame by a **single adjacent swap**, so motion is smooth and easy on the eyes.

**How many frames do you need?**
	•	**24 fps:** N = **1,440**
	•	**25 fps:** N = **1,500**
	•	**30 fps:** N = **1,800**
	•	**60 fps:** N = **3,600**

**Why SJT truncation?**
	•	**Smoothness:** consecutive frames differ by one adjacent swap → minimal visual “jump.”
	•	**Simplicity:** just generate SJT and stop at N frames.
	•	**Performance:** generating the first few thousand out of 362,880 is trivial.

**Optional refinements (nice-to-have)**
	•	**Looping:** the last SJT frame won’t naturally match the first; use a quick **crossfade** (e.g., 6–12 frames) to loop seamlessly.
	•	**Variety bias (if you want more diversity):** instead of pure truncation, you *can* pick evenly spaced indices across the full SJT run and then **locally smooth** by sorting neighbors by Hamming distance—but this trades away the perfect adjacent-swap property. For most videos, pure SJT truncation looks better.

⸻

**Quick recommendation (pick one)**
	•	**Cinematic feel:** 24 or 25 fps → take **1,440** or **1,500** SJT frames (smooth, slightly filmic cadence).
	•	**General web video:** 30 fps → take **1,800** SJT frames (crisper motion).
	•	**Ultra-smooth (sports/gaming vibe):** 60 fps → take **3,600** SJT frames.

If you want, I can produce a 9! workbook/tab with the first N SJT permutations for your chosen frame rate and include a tiny HTML “how to render” note (export as PNG sequence → assemble at the selected fps).


```
Yes, create excel and include all options and explanations in html

```

All set ✅
	•	 <span style="font-family: .AppleColorEmojiUI;">
     📊
 </span> **Excel (n=9, 1-minute SJT subsets for all fps):**
[Download n9_SJT_1min_all_fps.xlsx](sandbox:/mnt/data/n9_SJT_1min_all_fps.xlsx?_chatgptios_conversationID=68b1ad0d-91d4-8333-a1e8-222d9d38b552&_chatgptios_messageID=fbc044ed-546b-4d6b-b91c-a4332705fccb)
Sheets included:
	•	**Summary** (frames + durations at 24/25/30/60 fps, with notes)
	•	**SJT_24fps_1440** — first 1,440 SJT permutations
	•	**SJT_25fps_1500** — first 1,500 SJT permutations
	•	**SJT_30fps_1800** — first 1,800 SJT permutations
	•	**SJT_60fps_3600** — first 3,600 SJT permutations
Each SJT sheet includes Properties, Frames, a “Durations — 24/25/30/60 fps” line, a looping tip, and rows with Index, SJT Index, Sequence, Pos1..Pos9, and Notes.
	•	 <span style="font-family: .AppleColorEmojiUI;">
     📄
 </span> **HTML explanation (options + how-to):**
[Download n9_SJT_1min_all_fps_explainer.html](sandbox:/mnt/data/n9_SJT_1min_all_fps_explainer.html?_chatgptios_conversationID=68b1ad0d-91d4-8333-a1e8-222d9d38b552&_chatgptios_messageID=fbc044ed-546b-4d6b-b91c-a4332705fccb)
