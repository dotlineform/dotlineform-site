---
doc_id: drawline
title: drawLine
added_date: "2026-07-14 17:47"
last_updated: "2026-07-14 17:47"
parent_id: sketch-250309a-ink
---
# drawLine


Below is a new function called **drawLine** that takes two parameters: a start point (a PVector) and a style (a String). It uses the template from **demo_createLineBounded** to set up line and ink options, calls **setLineBoundary** with the provided style, creates a BezierCurve, and finally draws the vector field line. A label is also added near the start point.

void drawLine(PVector start, String style) {
  *// Initialize line options for the vector field line.*
  LineOptions lineOptions = new LineOptions();
  lineOptions.numParticles = 1000;
  lineOptions.lineWidth = 2;
  
  *// Set ink parameters for the vector field effect.*
  *// These parameters control the decay of stroke width along the line.*
  float inkFraction = 0.1;      *// Fraction of the stroke drawn at full strength.*
  String decayType = "quickslow"; *// Decay type (e.g., "linear", "exponential", etc.)*
  float exponent = 10;          *// Used for exponential decay.*
  float slope = 100;            *// Used for sigmoidal decay.*
  float initialMultiplier = 3;  *// Full-strength multiplier.*
  float velocity = 50;          *// Not used in quickslow mode.*
  
  *// Create a VectorInkOptions object with vector-specific parameters.*
  float distortionScale = 1;    *// Maximum displacement in pixels.*
  float noiseScale = 0.05;      *// Frequency of noise variations.*
  VectorInkOptions vectorInkOptions = new VectorInkOptions(distortionScale, noiseScale,
      inkFraction, decayType, exponent, slope, initialMultiplier, velocity);
  
  *// Create a CurveOptions object using the setLineBoundary function and the provided style.*
  CurveOptions curveOptions = setLineBoundary(start, style);
  
  *// Create a BezierCurve from the CurveOptions.*
  BezierCurve myCurve = createBezierCurve(curveOptions);
  
  *// Draw the vector field line using the curve and vector ink options.*
  createLine_VectorField(lineOptions, vectorInkOptions, myCurve);
  
  *// Label the line: place text to the left of the start point.*
  textAlign(RIGHT, CENTER);
  textSize(12);
  fill(0);
  text("Line: " + style, start.x - 20, start.y);
}

**How It Works**
	•	**Parameters:**
	•	start: A PVector that sets the apex of the line boundary (and is used as the start point).
	•	style: A String (“quick”, “natural”, or “wild”) that determines the arc (segment of a circle) in which the control points and end point will lie.
	•	**Process:**
	1.	**LineOptions** and **VectorInkOptions** are created with fixed parameters.
	2.	**setLineBoundary(start, style)** returns a CurveOptions object with control points and end point computed from an arc segment based on the style.
	3.	**createBezierCurve(curveOptions)** converts the CurveOptions into a BezierCurve object.
	4.	**createLine_VectorField** is called to draw the distorted vector field line.
	5.	A label is drawn to the left of the start point displaying the style.

You can now call **drawLine** with your desired start point and style to produce a drawing of a line. For example:

drawLine(new PVector(200, height/2), "wild");

This will create a line starting at (200, height/2) with the “wild” style applied to its boundary.
