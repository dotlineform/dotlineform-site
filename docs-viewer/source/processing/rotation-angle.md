---
doc_id: rotation-angle
title: rotation angle
added_date: "2026-07-14 17:47"
last_updated: "2026-07-14 17:47"
parent_id: sketch-250309a-ink
---
# rotation angle


 <span style="background-color: #00C6BD;">
     in processing, when a line is drawn at an angle, where is angle = 0? pointing upwards?
 </span>

In Processing, angles are measured in radians using the standard mathematical convention. This means:
	•	**0 radians** is along the positive x-axis (pointing to the right).
	•	**PI/2 radians (90°)** points upward.
	•	**PI radians (180°)** points to the left.
	•	**3*PI/2 radians (270°)** points downward.

So, if you draw a line at angle 0, it will be horizontal and point to the right, not upward.

 <span style="background-color: #00C6BD;">
     so the angles go in a counter-clockwise direction!

 </span>
Yes, mathematically angles in Processing are measured in radians with 0 along the positive x-axis and increase in a counter-clockwise direction. However, because Processing’s coordinate system has its origin at the top-left and the y-axis increases downward, a positive angle will visually appear rotated clockwise relative to what you might expect from a standard mathematical (Cartesian) coordinate system.

In summary:
	•	**Mathematically:** 0 is to the right, PI/2 is up if using a standard system.
	•	**In Processing:** 0 is to the right, but PI/2 is actually down (due to the inverted y-axis).

So while the trigonometric functions (cos, sin) assume a counter-clockwise increase, the on-screen effect may seem reversed.
