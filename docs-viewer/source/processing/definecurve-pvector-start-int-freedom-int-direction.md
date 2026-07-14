---
doc_id: definecurve-pvector-start-int-freedom-int-direction
title: defineCurve (PVector start, int freedom, int direction)
added_date: "2026-07-14 17:47"
last_updated: "2026-07-14 17:47"
parent_id: sketch-250309a-ink
---
# defineCurve (PVector start, int freedom, int direction)

## **defineCurve** (PVector start, int freedom, int direction)

returns a BezierCurve object derived from the parameters


### **parameters**

 <span style="background-color: #00C6BD;">
     **start**
 </span> - the start point of the curve

 <span style="background-color: #00C6BD;">
     **freedom**
 </span>
1 = free
2 = wild
3 = restricted (wide)
4 = restricted (narrow)

**freedom** is used to define a region in which the curve start, end and control points are random but within set constraints:

**free**
whole drawing area

**wild**
a circle, radius height/2 or width/2 (whichever is smallest), centred at start point

**restricted (wide)**
a circle segment, radius height/2 or width/2 (whichever is smallest), centred at start point
the segment arc angle is random between:
min = PI / 6 (30°)
max = PI (180°) 
the control points and end points have their own min and max radius (i.e. the segment is banded)

**restricted (narrow)**
a circle segment, radius height/10 or width/10 (whichever is smallest), centred at start point
the segment arc angle is random between:
min = PI / 18 (10°)
max = PI /6 (30°) 
the control points and end points have their own min and max radius (i.e. the segment is banded)

In all cases, points are checked if they are outside drawing boundaries, if so the points are scaled down to ensure the control points are all inside the drawing area.
(Note that constraining all the control points to within the drawing boundary does not necessarily mean that the resulting curve will be too. But most of the time it is.)

 <span style="background-color: #00C6BD;">
     **direction**
 </span>

for freedoms that use a circle segment to constrain the curve points
this sets the angle of the segment 

-1 = a random direction (default)
0-360°

0° points horizontal right
-90° points up
+90° points down
