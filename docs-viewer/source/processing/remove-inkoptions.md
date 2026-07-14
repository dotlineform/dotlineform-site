---
doc_id: remove-inkoptions
title: remove inkOptions
added_date: "2026-07-14 17:47"
last_updated: "2026-07-14 17:47"
parent_id: sketch-250309a-ink
---
# remove inkOptions


Below is an overview of the changes you need to make so that all references to InkOptions (and its global defaults) are replaced by InkParameters (and/or specialized types stored in inkTypeOptions):

⸻

**1. Remove the InkOptions Class**
	•	**Delete the InkOptions Class Definition:**
Remove the entire class definition for InkOptions. (Search for class InkOptions { ... } and delete it.)

⸻

**2. Update Function Signatures**
	•	**For Drawing Functions:**
For every drawing function that previously had an InkOptions parameter, update the signature so that it accepts an InkParameters object (or a specialized subclass that extends InkParameters) instead.
For example:
	•	Change

void drawCurve_Particle(InkOptions inkOptions, CurvePoints cp)

to

void drawCurve_Particle(InkParameters inkParams, CurvePoints cp)


	•	Do the same for drawCurve_Particle_Diffuse, drawCurve_VectorField, and drawCurve_Particle_Texture.

	•	**Inside the Functions:**
Inside each function, replace any references to the old InkOptions object (like inkOptions.inkFraction) with the corresponding field from the InkParameters object (e.g. inkParams.inkFraction).

⸻

**3. Update Constructors for Specialized Options**
	•	**For VectorInkOptions and TextureInkOptions:**
If these classes currently extend InkOptions, update them so they extend InkParameters (or if you prefer, have them include an InkParameters field).
For example, change:

class VectorInkOptions extends InkOptions { ... }

to:

class VectorInkOptions extends InkParameters { ... }

Then update their constructors accordingly so that when you construct a new VectorInkOptions you pass the needed parameters (which now come from an InkParameters object).

	•	**Ensure all references to lineWidth, decayType, etc., are read from the InkParameters fields.**

⸻

**4. Update Call Sites in draw()**
	•	**When Creating Options Objects:**
In your draw() function (and anywhere else you build options objects), remove any code that creates a new InkOptions object. Instead, retrieve the parameters from your inkTypeOptions HashMap. For example, if you previously had:

InkOptions inkOptions = new InkOptions(ip.inkFraction, ip.exponent, ip.slope, ip.initialMultiplier, ip.velocity, ip.numParticles, ip.decayType, ip.lineWidth);
drawCurve_Particle(inkOptions, offsetCP);

Change it to:

*// ip is the InkParameters retrieved from inkTypeOptions.*
drawCurve_Particle(ip, offsetCP);

Similarly, update calls for the other drawCurve_* functions.

	•	**Remove References to Global Variables:**
Anywhere you previously used global variables like inkFraction, exponent, etc., change these references to use the appropriate fields from the InkParameters object (e.g. ip.inkFraction). That way, the UI now controls the values stored in inkTypeOptions rather than in separate globals.

⸻

**5. Update UI Code to Use InkParameters**
	•	**When Creating or Updating Sliders:**
In your UI creation (for example, in drawUI_InkType), when you update the InkParameters object using reflection or by direct assignment, that object comes from inkTypeOptions. Make sure your code uses something like:

InkParameters ip = inkTypeOptions.get(inkKey);

and then later updates ip.<field> values (either via reflection or via explicit assignment).

	•	**Populating inkTypeOptions:**
In your setup(), ensure you populate inkTypeOptions with InkParameters objects containing the proper default values. For example:

inkTypeOptions.put("vector field", new InkParameters(1, 0.05, 0.1, 10, 100, 3, 50, 1000, "quickslow", 1, null));
inkTypeOptions.put("particle", new InkParameters(0, 0, 0.1, 10, 100, 3, 50, 1000, "quickslow", 1, null));
*// ... and similarly for the other ink types.*



⸻

**6. Verify Your Build Order**
	•	**Initialization Order:**
Make sure that your global hash maps (inkTypeOptions, inkTypes, inkTypeSliders, inkTypeBoundaries) are all initialized at the beginning of setup() before any code references them.
	•	**Update All References:**
Search your code for any remaining references to InkOptions and update them to InkParameters (or specialized subclasses). Check both function signatures and call sites.

⸻

**Summary**
	1.	**Delete InkOptions class.**
	2.	**Change all function signatures that previously took InkOptions to now accept InkParameters.**
	3.	**Update VectorInkOptions and TextureInkOptions to extend InkParameters and update their constructors.**
	4.	*In draw(), use inkTypeOptions.get(inkKey) to retrieve an InkParameters object (ip) and pass it to the drawCurve_ functions instead of creating a new InkOptions.**
	5.	**In the UI code, update slider defaults and value assignments to update the fields in the InkParameters objects stored in inkTypeOptions.**
	6.	**Ensure all globals are initialized before use.**

By following these steps, you’ll remove the redundant InkOptions class and have a unified set of parameters in InkParameters (and its specialized variants) that are used by all your drawing functions and UI code.

⸻

Would you like me to apply a patch using the oboe.edit_file tool with these changes?
