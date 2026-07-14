---
doc_id: createline-vectorfield-v2
title: createLine_VectorField (v2)
added_date: "2026-07-14 17:47"
last_updated: "2026-07-14 17:47"
parent_id: sketch-250309a-ink
---
# createLine_VectorField (v2)





noise()
[https://processing.org/reference/noise_.html](https://processing.org/reference/noise_.html)

Syntax
| noise(x)       |                |
|----------------|----------------|
| noise(x, y)    |                |
| noise(x, y, z) |                |

Parameters
| x                           | (float)                     | x-coordinate in noise space |
|-----------------------------|-----------------------------|-----------------------------|
| y                           | (float)                     | y-coordinate in noise space |
| z                           | (float)                     | z-coordinate in noise space |


z is time based (e.g. frameCount)

    // Use staticTime instead of frameCount for a static result.
    // (frameCount is a built-in global variable that automatically increments by 1 each time a new frame is drawn.)
    // Multiplying staticTime by 0.01 scales down the time value before it’s used in the noise function.
    // The noise() function is sensitive to the magnitude of its inputs, and smaller values tend to produce smoother, more gradual variations.
    // By using 0.01 as a multiplier, you effectively compress the range of staticTime so that even if staticTime is increased, its effect on the noise output remains subtle.
    // This scaling helps achieve a controlled, organic distortion rather than abrupt changes.
    // You can adjust the multiplier if you want a stronger or weaker time effect.
 <span style="background-color: #FF9502;">
     so basically in a static drawing we don’t need 3rd parameter!


 </span>For a static drawing, you don’t strictly need the third argument if you only want a 2D noise field. You can call:

float noiseX = noise(base.x * noiseScale, base.y * noiseScale);
float noiseY = noise(base.y * noiseScale, base.x * noiseScale);

This will give you a fixed 2D noise value. However, keeping a constant third argument (like using a local variable) allows you to control an additional dimension of noise if desired, but it’s not required for a static result.

 <span style="background-color: #00C6BD;">
     why is staticTime multiplied by 0.01?
 </span>

Multiplying staticTime by 0.01 scales down the time value before it’s used in the noise function. The noise() function is sensitive to the magnitude of its inputs, and smaller values tend to produce smoother, more gradual variations. By using 0.01 as a multiplier, you effectively compress the range of staticTime so that even if staticTime is increased, its effect on the noise output remains subtle. This scaling helps achieve a controlled, organic distortion rather than abrupt changes. 
 <span style="background-color: #FF9502;">
     You can adjust the multiplier if you want a stronger or weaker time effect.
 </span>


 <span style="background-color: #00C6BD;">
     in createLine_VectorField, need to use InkOptions parameter as used in the other createline functions

-> v2
 </span>

**Explanation**
	•	**Smooth Stroke Generation:**
The function samples numPoints along the Bezier curve to create a smooth base stroke.
	•	**Noise-Based Distortion:**
Each base point is displaced using Perlin noise. Instead of using a time-varying frameCount, a local variable staticTime is used (set to 1.0 by default) for static drawings.
	•	**InkOptions Integration:**
For each segment between consecutive distorted points, we calculate the midpoint’s normalized parameter (avgT) and use InkOptions (inkFraction, decayType, exponent, slope, initialMultiplier) to compute a decay factor. This factor modulates the stroke weight (baseLineWidth * factor) for that segment.
	•	**Segment Drawing:**
Instead of drawing a continuous shape with curveVertex(), the stroke is rendered as a series of short line segments with varying stroke weight, better mimicking the decay dynamics used in the other createLine functions.


 <span style="background-color: #00C6BD;">
     this uses line function instead of the curveVertex function. why?
 </span>

v1 uses curveVector function
v2 uses line function

this is why:

The reason for using the line() function in this case is that it allows you to vary the stroke weight for each segment along the stroke. In our vector field approach, we compute a decay factor for each segment (based on the midpoint’s normalized position) using the InkOptions parameters, which then adjusts the stroke weight accordingly.

Using line() lets you draw each segment with its own stroke weight, giving you fine control over how the thickness of the stroke changes along its length. On the other hand, curveVertex() creates one continuous curve where you set a single stroke weight for the entire shape, making it more difficult to achieve variable thickness along the curve.

In summary, the use of line() is a deliberate choice to achieve per-segment variation in stroke thickness, which better mimics the organic, uneven absorption of ink.


 <span style="background-color: #00C6BD;">
     the resulting ink line is very jagged. how can it be made much smoother?
 </span>

The jagged appearance usually means the sampling resolution is too low or the distortion is too extreme. Here are a few suggestions to smooth out the line:
	1.	**Increase the Number of Sample Points:**
Increase lineOptions.numParticles so that more points are sampled along the Bezier curve. This produces smaller segments, which results in a smoother overall curve.
	2.	**Reduce the Distortion Magnitude:**
Lower the value of distortionScale (or adjust the noise parameters) to reduce how far each point is displaced. Smaller displacements lead to smoother transitions between points.
	3.	**Apply Smoothing to the Distorted Points:**
You can apply a smoothing algorithm (like a moving average or a low-pass filter) to the distorted points before drawing them. This will help remove abrupt changes between adjacent points.
	4.	**Switch to Continuous Curve Drawing:**
Instead of drawing each segment with line(), you can use curveVertex() to draw one continuous curve through the points. This method naturally smooths out the drawing, although you may lose per-segment stroke weight variation.

For example, to increase smoothness, you might try:

lineOptions.numParticles = 2000;  *// Increase number of sample points*
distortionScale = 10;              *// Reduce maximum displacement*

These adjustments should make the resulting ink line much smoother.

______________

move to a VectorInkOptions class which extends InkOptions: distortionScale, noiseScale, staticTime

 float distortionScale = 20;  
  float noiseScale = 0.05;     // Frequency of noise variations; adjust for wavy effect.
