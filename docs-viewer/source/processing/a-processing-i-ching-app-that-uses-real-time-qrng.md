---
doc_id: a-processing-i-ching-app-that-uses-real-time-qrng
title: "A processing I Ching app that uses real time QRNG?"
added_date: "2026-07-14 17:43"
last_updated: "2026-07-14 17:43"
parent_id: i-ching
---
# A processing I Ching app that uses real time QRNG?



Yes! I’ve packaged a **Processing (Java mode) I Ching app** that casts hexagrams using a **real-time Quantum Random Number Generator (QRNG)** from ANU. It reproduces the classic 3-coin probabilities, shows changing lines, and gracefully falls back to a local PRNG if the network is unavailable.

**Download the app (ZIP):** [Processing_IChing_QRNG.zip](sandbox:/mnt/data/Processing_IChing_QRNG.zip?_chatgptios_conversationID=68cfedc3-575c-8329-83fb-b970f9c8f232&_chatgptios_messageID=0ef8ddcd-92a2-41c8-8dec-c9b617bfca15)

What’s inside:
	•	A Processing sketch that fetches **uint8** quantum-random bytes from ANU’s JSON API and maps them to hexagram lines (3 bits → line with the 6/7/8/9 distribution).
	•	A small **data** file with short hexagram names (so you can plug in your preferred translation later).
	•	A **README.html** with setup steps, mapping logic, UI controls (Space = new cast, R = auto-refresh, S = screenshot), and extension ideas.

How the QRNG mapping works (high-level):
	•	Each line uses 3 QRNG bits:
000 → **6** (old yin, changing) • 111 → **9** (old yang, changing) • one-hot → **7** (young yang) • two-hot → **8** (young yin).
This exactly matches the 3-coin probabilities (1/8, 3/8, 3/8, 1/8). The six lines (built bottom→top) yield the primary hexagram; changing lines produce the resulting hexagram.

Citations (for the tech and method):
	•	**ANU Quantum Random Numbers** — JSON API parameters & usage.
	•	**Yijing (I Ching) structure** — 64 hexagrams; line building and coin/yarrow methods.
	•	**Randomness beacons / QRNG context** — background on beacons and quantum randomness.

Want me to add:
	•	A **toggle to Tibetan mo** mode (two 1–6 samples from QRNG → 2–12 table),
	•	A **logging panel** (timestamp, question, hexagram, changing lines), or
	•	A minimal **index.html** landing page that documents your whole I Ching toolkit and links all the downloads?

All set — I upgraded the app and added a project index.

**What’s new**
	•	**Tibetan mo mode:** toggle with **M**. The app draws two independent 1–6 samples from the QRNG (preserving the 2–12 bell curve) and displays the dice and total for manual lookup in your lineage table.
	•	**Logging:** toggle with **L**. Each cast is appended to data/log.csv with timestamp, mode, optional question, hexagram/mo result, changing lines, and whether the source was **QRNG** or PRNG fallback.
	•	**Question prompt:** press **Q** to set a question; it’s stamped into the next log entries.
	•	**Index page:** quick launcher that links all your diagrams, comparisons, timelines, and both app versions.

**Downloads**
	•	**Processing I Ching QRNG — v2 (current):** [Processing_IChing_QRNG_v2.zip](sandbox:/mnt/data/Processing_IChing_QRNG_v2.zip?_chatgptios_conversationID=68cfedc3-575c-8329-83fb-b970f9c8f232&_chatgptios_messageID=1fa08d46-7ff1-4757-8a58-c79cf80be7a5)
	•	**Project index (links to every asset):** [I Ching Toolkit — Index](sandbox:/mnt/data/iching_toolkit_index.html?_chatgptios_conversationID=68cfedc3-575c-8329-83fb-b970f9c8f232&_chatgptios_messageID=1fa08d46-7ff1-4757-8a58-c79cf80be7a5)

(Your original v1 zip is still linked on the index for reference.)

**How to use (quick)**
	•	Open the .pde in Processing (Java mode).
	•	**SPACE** new cast • **R** auto-refresh • **S** save PNG • **M** I Ching/mo • **L** logging • **Q** set question.
	•	I Ching mode maps **QRNG bits → 6/7/8/9** with the classic 3-coin probabilities; mo mode maps **QRNG → two 1–6 “dice”**.

**Citations**
	•	**ANU Quantum Random Numbers** — API docs and JSON parameters.
	•	**Yijing (I Ching) structure** — 64 hexagrams, coin/yarrow casting, changing lines.
	•	**Randomness beacons / QRNG context** — background and standards work.

If you’d like, I can add a minimal **mo lineage table editor** (CSV → on-screen lookup) so mo results display suggested guidance inline.

Amazing — I’ve added the **mo lineage table editor** and shipped a new build.

**What you got**
	•	**v3 app (Processing):** loads data/mo_table.csv and, in **mo mode**, displays your lineage’s **Outcome / Advice / Remedy** for the 2–12 result directly in the UI.
	•	**CSV template:** data/mo_table.csv (editable in any spreadsheet). Sums 2–12 are prefilled with placeholder guidance so you can adapt to your tradition.
	•	**Helper page:** EDITING_mo_table.html (quick how-to for editing the CSV).
	•	**Logging & QRNG features** from v2 are intact.

**Download**
	•	**Processing I Ching QRNG — v3 (mo lineage table built-in):**
[Processing_IChing_QRNG_v3.zip](sandbox:/mnt/data/Processing_IChing_QRNG_v3.zip?_chatgptios_conversationID=68cfedc3-575c-8329-83fb-b970f9c8f232&_chatgptios_messageID=59ef6a53-4ea2-4f29-8b6c-0a12c7fe3d6a)
	•	**Project index (updated):**
[I Ching Toolkit — Index](sandbox:/mnt/data/iching_toolkit_index.html?_chatgptios_conversationID=68cfedc3-575c-8329-83fb-b970f9c8f232&_chatgptios_messageID=59ef6a53-4ea2-4f29-8b6c-0a12c7fe3d6a)

**How to use the mo table**
	1.	Open data/mo_table.csv.
	2.	For each row (sum 2–12), edit **outcome**, **advice**, and **remedy_note** to match your lineage table.
	3.	Save and relaunch (or press **SPACE** in the app) — your guidance appears on-screen under “Lineage guidance.”

**Notes & citations**
	•	The **mo** feature mirrors Tibetan dice divination practice (lineage-specific lookup is expected). Background on divination and mo in Tibetan Buddhism: Encyclopaedia Britannica; StudyBuddhism overviews.
	•	**QRNG source** (unchanged): Australian National University JSON API for quantum-random bytes.
	•	**I Ching structure & casting** (for the hexagram side): Encyclopaedia Britannica on Yijing basics.

Want me to pre-populate mo_table.csv with a **specific lineage’s** wording (e.g., a Manjushri mo variant) if you can share a reference?
