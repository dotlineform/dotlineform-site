---
doc_id: random-seeding
title: random seeding
added_date: "2026-07-14 17:47"
last_updated: "2026-07-14 17:47"
parent_id: sketch-250309a-ink
---
# random seeding


drawing looks the same each run:

	•	**Static Noise:** In your vector field function, you’re using a constant value (staticTime = 1.0) and not modifying the noise seed. The Processing noise() function is deterministic (producing the same output each run unless seeded differently).

	•	**No Random Seeding:** If you haven’t called randomSeed() or noiseSeed() with a dynamic value (like based on the current time), the pseudo-random number generators (both for random() and noise()) use their default seeds, which results in the same random sequence on each run.

If you want a different drawing each run, you could:

	•	Call randomSeed(millis()) or noiseSeed(millis()) in your setup() function.
	•	Or incorporate some additional randomness in functions like setLineBoundary (e.g., by adding random offsets to the control points).
