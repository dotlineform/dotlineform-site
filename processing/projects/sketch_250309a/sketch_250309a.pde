import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import controlP5.*;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.lang.reflect.Field;

ControlP5 cp5;

PFont normalFont;
PFont boldFont;

int controlPoints;     // Number of control points
boolean debug_showGeometry = false;   // draw any control points or boundaries. note: they will get cleared anyway unless drawn in draw()
int margin = 20;
int col1X = margin;
int col1Width = 200;           // Settings column width
int col2Width = 60;           // DecayType column width
int col2X = col1X + col1Width + margin;
int sliderWidth = 80; 
int labelAreaWidth = 90;
int col3X = col2X + col2Width + margin; 
int col3Width = sliderWidth + labelAreaWidth;
int col4X = col3X + col3Width + margin;   // Column 4 starts to the right of Column 3
int sliderY = 20;
int sliderHeight = 10;
int sliderSpacing = 15;
String[] decayTypes = {"linear", "exponential", "quadratic", "cubic", "logarithmic", "sigmoidal", "quickslow"};
// Define default and selected colors for decay buttons
int defaultButtonColor = color(173, 216, 230);
int selectedButtonColor = color(0, 0, 139);

CurvePoints currentCurve;

String currentSettingName = "";

boolean needsRedraw = true;

// store all the ink type curves
HashMap<String, CurvePoints> curvePoints_offset = new HashMap<String, CurvePoints>();

// helper function cacheInkParametersFields() used in setupDesign()
// to reduce expensive use of Java reflection
HashMap<String, Field> inkParamsFieldCache = new HashMap<String, Field>();

// Interface for setting a field value on an InkParameters object
interface FieldSetter {
  void setField(InkParameters ip, JSONObject groupJson, String fieldName);
}
    
// Global cache for FieldSetter functions, keyed by the field name.
HashMap<String, FieldSetter> fieldSetterCache = new HashMap<String, FieldSetter>();

class DrawingOptions {
  int drawingMargin; // margin as a percentage of the drawing area
  
  // Default constructor with a default drawing margin (e.g., 10%)
  DrawingOptions() {
    drawingMargin = 10;
  }
  
  // Parameterized constructor
  DrawingOptions(int drawingMargin) {
    this.drawingMargin = drawingMargin;
  }
}

// CurvePoints: start, control points, and end of a curve
class CurvePoints {
  PVector start;
  PVector control1;
  PVector control2;
  PVector end;
  
  // Constructor to initialize all points
  CurvePoints(PVector start, PVector control1, PVector control2, PVector end) {
    this.start = start;
    this.control1 = control1;
    this.control2 = control2;
    this.end = end;
  }
  
  // Optional: return a string representation of the curve points
  public String toString() {
    return "CurvePoints(start=" + start + ", control1=" + control1 + ", control2=" + control2 + ", end=" + end + ")";
  }
}

// Boundary sets the parameters for the circle segment that will contain the curve
class Boundary {
  PVector start;    // starting point for the boundary
  int arcAngle;     // degrees 0-360
  int arcRadius;    // pixels
  int arcDirection; // degrees 0-360
  
  // Default constructor: sets start to (0,0) and others to 0
  Boundary() {
    start = new PVector(0, 0);
    arcAngle = 0;
    arcRadius = 0;
    arcDirection = 0;
  }
  // Parameterized constructor
  Boundary(PVector start, int arcAngle, int arcRadius, int arcDirection) {
    this.start = start;
    this.arcAngle = arcAngle;
    this.arcRadius = arcRadius;
    this.arcDirection = arcDirection;
  }
}
HashMap<String, Boundary> inkTypeBoundaries;

class SliderConfig {
  String name;
  float min;
  float max;
  float defaultValue;
  
  SliderConfig(String name, float min, float max, float defaultValue) {
    this.name = name;
    this.min = min;
    this.max = max;
    this.defaultValue = defaultValue;
  }
}
HashMap<String, SliderConfig[]> inkTypeSliderConfig;

class InkType {
  String name;             // e.g., "vector", "texture"
  String drawFunctionName; // e.g., "drawCurve_VectorField"

  InkType(String name, String drawFunctionName) {
    this.name = name;
    this.drawFunctionName = drawFunctionName;
  }
}
LinkedHashMap<String, InkType> inkTypes = new LinkedHashMap<String, InkType>();

// InkParameters holds all the possible parameters to be used in the drawCurve_ functions
class InkParameters {
  // setting default values for default constructor
  public float distortionScale = 1;    // Default distortion scale
  public float distortionScaleMin = 0;
  public float distortionScaleMax = 10;

  public float noiseScale = 0.05;      // Default noise scale
  public float noiseScaleMin = 0;
  public float noiseScaleMax = 1;
  
  public float inkFraction = 0.1;      // the fraction (0 to 1) of the stroke drawn at full strength.
  public float inkFractionMin = 0;
  public float inkFractionMax = 1;

  public float exponent = 10;          // For exponential decay.
  public float exponentMin = 0;
  public float exponentMax = 20;

  public float slope = 100;            // For sigmoidal decay.
  public float slopeMin = 0;
  public float slopeMax = 100;   // adjust max slope to 0–100 for more pronounced range

  public float initialMultiplier = 3;  // Multiplier for stroke width when full ink is available.
  public float initialMultiplierMin = 0;
  public float initialMultiplierMax = 10;

  public float velocity = 50;          // Intended to be in the range 1 to 100.
  public float velocityMin = 0;
  public float velocityMax = 100;

  public int numParticles = 1000;      // Number of particles to simulate the ink stroke.
  public int numParticlesMin = 0;
  public int numParticlesMax = 2000;

  public int lineWidth = 1;          // Default line width
  public int lineWidthMin = 0;
  public int lineWidthMax = 10;

  public PImage brushTexture = null;    // Default no brush texture
  
  public int greyscale = 0;  // Greyscale color of ink (0 = black, 255 = white)
  public int greyscaleMin = 0;
  public int greyscaleMax = 255;
  
  public String decayType = "quickslow"; // "linear", "exponential", etc.

  public int alpha = 255;       // transparency: 0 (transparent) to 255 (opaque)
  public int alphaMin = 0;
  public int alphaMax = 255;

  // Default constructor uses the above values.
  InkParameters() {
  }

  // Parameterized constructor (doesn't include the min/max values)
  InkParameters(float ds, float ns, float inkFrac, float exp, float slp, float initMult, float vel, int np, String decay, int lineW, PImage brushT, int greyscaleVal, int alphaVal) {
    distortionScale = ds;
    noiseScale = ns;
    inkFraction = inkFrac;
    exponent = exp;
    slope = slp;
    initialMultiplier = initMult;
    velocity = vel;
    numParticles = np;
    decayType = decay;
    lineWidth = lineW;
    brushTexture = brushT;
    this.greyscale = greyscaleVal;
    this.alpha = alphaVal;
  }
}
HashMap<String, InkParameters> inkTypeParameters;

// for droplets, code in droplets.pde, include the followuing in associated function called from setup()
//DisplayOptions dispOpts = new DisplayOptions();
//DropletRanges dropRanges = new DropletRanges();
//DrawingOptions drawOpts = new DrawingOptions();
//createDroplets(10, dispOpts, dropRanges, drawOpts);

void setup() {
  size(1600, 1200);
  pixelDensity(displayDensity());
  fullScreen();
  background(255);
  randomSeed(millis());

  // comment out depending upon whether design or create artwork
  setupDesign();

}

void draw() {

  if (needsRedraw) {
    background(255);       // clear background
    // comment out depending upon whether design or create artwork
    drawDesign();
    needsRedraw = false;   // reset the flag after updating the drawing
  }

}

// Check if a file exists in the data folder.
boolean fileExists(String filename) {
  return (new java.io.File(dataPath(filename))).exists();
}

void exportDrawing() {
  // Save the current canvas as a JPEG file named "exportedDrawing.jpg" in the sketch folder
  //key press handler calls this function when you press the s key:
  saveFrame("exportedDrawing.jpg");
}

// Computes a scaling factor for 'pt' so that if it's out of bounds,
// scaling the vector (pt - start) by this factor brings it to the canvas edge.
float computeScalingFactor(PVector start, PVector pt) {
  PVector v = PVector.sub(pt, start);
  float s = 1.0;  // Default: if point is inside, no scaling needed
  
  // If the candidate is outside the left boundary:
  if (pt.x < 0 && v.x < 0) {
    float tLeft = -start.x / v.x;
    s = min(s, tLeft);
  }
  // Right boundary:
  if (pt.x > width && v.x > 0) {
    float tRight = (width - start.x) / v.x;
    s = min(s, tRight);
  }
  // Top boundary:
  if (pt.y < 0 && v.y < 0) {
    float tTop = -start.y / v.y;
    s = min(s, tTop);
  }
  // Bottom boundary:
  if (pt.y > height && v.y > 0) {
    float tBottom = (height - start.y) / v.y;
    s = min(s, tBottom);
  }
  
  return s;
}

//offset a curve by x and y
CurvePoints offsetCurve(CurvePoints cp, float offsetX, float offsetY) {
  PVector newStart = new PVector(cp.start.x + offsetX, cp.start.y + offsetY);
  PVector newControl1 = new PVector(cp.control1.x + offsetX, cp.control1.y + offsetY);
  PVector newControl2 = new PVector(cp.control2.x + offsetX, cp.control2.y + offsetY);
  PVector newEnd = new PVector(cp.end.x + offsetX, cp.end.y + offsetY);
  return new CurvePoints(newStart, newControl1, newControl2, newEnd);
}

// Helper function: returns a random point within a circle of radius r centered at center.
PVector randomPointInCircle(float r, PVector center) {
  float angle = random(TWO_PI);
  // Use sqrt(random(1)) for uniform distribution over the area.
  float radius = sqrt(random(1)) * r;
  return new PVector(center.x + radius * cos(angle), center.y + radius * sin(angle));
}

// create a Boundary object that fits into a rectangle
Boundary boundaryFromRect(float x, float y, float w, float h) {

  // The start is halfway down the left edge.
  PVector start = new PVector(x, y + h/2.0);
  
  // The arc radius is set to the width of the rectangle.
  int r = int(w);
  
  // Compute the arc angle in radians for a chord of length h in a circle of radius w.
  float ratio = h / (2.0 * w);
  ratio = constrain(ratio, 0, 1);  // Ensure the value is in the valid range.
  float arcAngleRadians = 2 * asin(ratio);
  int arcAngleDegrees = int(degrees(arcAngleRadians));

  // Draw the rectangle and arc segment.
  // We'll assume an arcDirection of 0 degrees (i.e. horizontally centered).
  // So the arc is drawn from -arcAngleRadians/2 to +arcAngleRadians/2.
  // note: will only work if draw() doesn't clear the screen!
  if (debug_showGeometry) {
    noFill();
    stroke(200);
    rect(x, y, w, h);
    arc(start.x, start.y, 2*r, 2*r, -arcAngleRadians/2, arcAngleRadians/2);
  }
  // Create and return the Boundary with the computed values.
  return new Boundary(start, arcAngleDegrees, r, 0);
}

void cacheInkParametersFields() {
  Field[] fields = InkParameters.class.getDeclaredFields();
  for (Field f : fields) {
    f.setAccessible(true);
    inkParamsFieldCache.put(f.getName(), f);
  }
}

void cacheInkParametersFieldSetters() {
  // Assume inkParamsFieldCache is already populated (e.g., via cacheInkParametersFields())
  for (String key : inkParamsFieldCache.keySet()) {
    Field field = inkParamsFieldCache.get(key);
    if (field == null) continue;
    if (field.getType() == float.class) {
      fieldSetterCache.put(key, new FieldSetter() {
        public void setField(InkParameters ip, JSONObject groupJson, String fieldName) {
          try {
            field.setFloat(ip, groupJson.getFloat(fieldName));
          } catch(Exception e) {
            e.printStackTrace();
          }
        }
      });
      } else if (field.getType() == int.class) {
        fieldSetterCache.put(key, new FieldSetter() {
          public void setField(InkParameters ip, JSONObject groupJson, String fieldName) {
            try {
              field.setInt(ip, groupJson.getInt(fieldName));
            } catch(Exception e) {
              e.printStackTrace();
            }
        }
      });
      } else if (field.getType() == String.class) {
        fieldSetterCache.put(key, new FieldSetter() {
          public void setField(InkParameters ip, JSONObject groupJson, String fieldName) {
            try {
              field.set(ip, groupJson.getString(fieldName));
            } catch(Exception e) {
              e.printStackTrace();
            }
          }
        });
      }
    }
  }

// setup the UI for creating ink styles, with settings saved in a json file
void setupDesign() {

  cp5 = new ControlP5(this);

  // Set font for the UI
  PFont cp5Font = createFont("Arial", 8, true);
  cp5.setFont(cp5Font);
  normalFont = createFont("Arial", 14);
  boldFont = createFont("Arial-BoldMT", 14);
  textFont(normalFont);

  // Initialize global hash maps

  cacheInkParametersFields();
  cacheInkParametersFieldSetters();

  // use inkTypes to get an InkType object by it's name (particle, vector etc)
  // InkType is for data about an ink type, e.g. what drawCurve_ function to use
  inkTypes = new LinkedHashMap<String, InkType>();
  
  // use inkTypeParameters to get an ink type's InkParameters object
  inkTypeParameters = new HashMap<String, InkParameters>();

  // use inkTypeSliderConfig to get the config settings (name, min, max, default value) for an ink type's sliders
  inkTypeSliderConfig = new HashMap<String, SliderConfig[]>();

  // use inkTypeBoundaries to get an ink type's boundary
  inkTypeBoundaries = new HashMap<String, Boundary>();

  // populate the hashmaps

  inkTypes.put("vector field", new InkType("vector field", "drawCurve_VectorField"));
  inkTypes.put("particle", new InkType("particle", "drawCurve_Particle"));
  inkTypes.put("particle diffuse", new InkType("particle diffuse", "drawCurve_Particle_Diffuse"));
  inkTypes.put("particle texture", new InkType("particle texture", "drawCurve_Particle_Texture"));

  inkTypeParameters.put("vector field", new InkParameters());
  inkTypeParameters.put("particle", new InkParameters());
  inkTypeParameters.put("particle diffuse", new InkParameters());
  inkTypeParameters.put("particle texture", new InkParameters());


  // default slider values read from InkParameters hash map (default values are defined in the class)
  // for each slider, these defaults are then saved into a SliderConfig object along with the other config values (name, min, max)
  // these values are then used when creating the sliders in drawUI_Sliders()

  // vector field
  InkParameters vectorParams = inkTypeParameters.get("vector field");
  inkTypeSliderConfig.put("vector field", new SliderConfig[] {
    new SliderConfig("distortionScale", vectorParams.distortionScaleMin, vectorParams.distortionScaleMax, vectorParams.distortionScale),
    new SliderConfig("noiseScale", vectorParams.noiseScaleMin, vectorParams.noiseScaleMax, vectorParams.noiseScale),
    new SliderConfig("inkFraction", vectorParams.inkFractionMin, vectorParams.inkFractionMax, vectorParams.inkFraction),
    new SliderConfig("exponent", vectorParams.exponentMin, vectorParams.exponentMax, vectorParams.exponent),
    new SliderConfig("slope", vectorParams.slopeMin, vectorParams.slopeMax, vectorParams.slope),
    new SliderConfig("initialMultiplier", vectorParams.initialMultiplierMin, vectorParams.initialMultiplierMax, vectorParams.initialMultiplier),
    new SliderConfig("velocity", vectorParams.velocityMin, vectorParams.velocityMax, vectorParams.velocity),
    new SliderConfig("numParticles", vectorParams.numParticlesMin, vectorParams.numParticlesMax, vectorParams.numParticles),
    new SliderConfig("lineWidth", vectorParams.lineWidthMin, vectorParams.lineWidthMax, vectorParams.lineWidth),
    new SliderConfig("greyscale", vectorParams.greyscaleMin, vectorParams.greyscaleMax, vectorParams.greyscale)
  });

  // particle
  InkParameters particleParams = inkTypeParameters.get("particle"); //so we can get default values
  inkTypeSliderConfig.put("particle", new SliderConfig[] {
    new SliderConfig("inkFraction", particleParams.inkFractionMin, particleParams.inkFractionMax, particleParams.inkFraction),
    new SliderConfig("slope", particleParams.slopeMin, particleParams.slopeMax, particleParams.slope),
    new SliderConfig("initialMultiplier", particleParams.initialMultiplierMin, particleParams.initialMultiplierMax, particleParams.initialMultiplier),
    new SliderConfig("velocity", particleParams.velocityMin, particleParams.velocityMax, particleParams.velocity),
    new SliderConfig("numParticles", particleParams.numParticlesMin, particleParams.numParticlesMax, particleParams.numParticles),
    new SliderConfig("lineWidth", particleParams.lineWidthMin, particleParams.lineWidthMax, particleParams.lineWidth),
    new SliderConfig("greyscale", particleParams.greyscaleMin, particleParams.greyscaleMax, particleParams.greyscale)
  });

  // particle diffuse
  InkParameters particleDiffuseParams = inkTypeParameters.get("particle diffuse");
  inkTypeSliderConfig.put("particle diffuse", new SliderConfig[] {
    new SliderConfig("inkFraction", particleDiffuseParams.inkFractionMin, particleDiffuseParams.inkFractionMax, particleDiffuseParams.inkFraction),
    new SliderConfig("slope", particleDiffuseParams.slopeMin, particleDiffuseParams.slopeMax, particleDiffuseParams.slope),
    new SliderConfig("initialMultiplier", particleDiffuseParams.initialMultiplierMin, particleDiffuseParams.initialMultiplierMax, particleDiffuseParams.initialMultiplier),
    new SliderConfig("velocity", particleDiffuseParams.velocityMin, particleDiffuseParams.velocityMax, particleDiffuseParams.velocity),
    new SliderConfig("numParticles", particleDiffuseParams.numParticlesMin, particleDiffuseParams.numParticlesMax, particleDiffuseParams.numParticles),
    new SliderConfig("lineWidth", particleDiffuseParams.lineWidthMin, particleDiffuseParams.lineWidthMax, particleDiffuseParams.lineWidth),
    new SliderConfig("greyscale", particleDiffuseParams.greyscaleMin, particleDiffuseParams.greyscaleMax, particleDiffuseParams.greyscale)
  });

  // particle texture
  InkParameters particleTextureParams = inkTypeParameters.get("particle texture");
  inkTypeSliderConfig.put("particle texture", new SliderConfig[] {
    new SliderConfig("inkFraction", particleTextureParams.inkFractionMin, particleTextureParams.inkFractionMax, particleTextureParams.inkFraction),
    new SliderConfig("exponent", particleTextureParams.exponentMin, particleTextureParams.exponentMax, particleTextureParams.exponent),
    new SliderConfig("slope", particleTextureParams.slopeMin, particleTextureParams.slopeMax, particleTextureParams.slope),
    new SliderConfig("initialMultiplier", particleTextureParams.initialMultiplierMin, particleTextureParams.initialMultiplierMax, particleTextureParams.initialMultiplier),
    new SliderConfig("velocity", particleTextureParams.velocityMin, particleTextureParams.velocityMax, particleTextureParams.velocity),
    new SliderConfig("numParticles", particleTextureParams.numParticlesMin, particleTextureParams.numParticlesMax, particleTextureParams.numParticles),
    new SliderConfig("lineWidth", particleTextureParams.lineWidthMin, particleTextureParams.lineWidthMax, particleTextureParams.lineWidth),
    new SliderConfig("greyscale", particleTextureParams.greyscaleMin, particleTextureParams.greyscaleMax, particleTextureParams.greyscale)
  });

  // draw the UI
  createDesign_Settings();  //col 1: buttons to manage the json file
  createDesign_InkTypes();  //col 2-4: decay types, sliders and the curves

  // define the curve for first slider group
  currentCurve = defineCurve(inkTypeBoundaries.get("vector field"));
  updateCurvePointsOffset();  // Populate curvePoints_offset to include all the offset curves

}

// called from draw() to draw the curves. a flag in draw() is used to ensure this is only called when a slider changes :-)
void drawDesign() {

  // Draw the current curve if it exists.
  if (currentCurve != null && inkTypeBoundaries != null && inkTypes != null && inkTypeParameters != null) {
    
    // Loop over each ink type (order preserved by inkTypes LinkedHashMap).
    for (String inkKey : inkTypes.keySet()) {
      Boundary b = inkTypeBoundaries.get(inkKey);
      if (b == null) continue;
      
      // Compute the offset so that the curve's start aligns with the boundary's start.
      CurvePoints offsetCP = curvePoints_offset.get(inkKey);
      
      // Retrieve the InkParameters for this ink type.
      InkParameters ip = inkTypeParameters.get(inkKey);
      if (ip == null) continue;
      
      // Retrieve the InkType object to determine which draw function to use.
      InkType it = inkTypes.get(inkKey);
      
      if (it.drawFunctionName.equals("drawCurve_VectorField")) {
        drawCurve_VectorField(ip, offsetCP);
      }
      else if (it.drawFunctionName.equals("drawCurve_Particle")) {
        drawCurve_Particle(ip, offsetCP);
      }
      else if (it.drawFunctionName.equals("drawCurve_Particle_Diffuse")) {
        drawCurve_Particle_Diffuse(ip, offsetCP);
      }
      else if (it.drawFunctionName.equals("drawCurve_Particle_Texture")) {
        drawCurve_Particle_Texture(ip, offsetCP);
      }
      else {
        // don't draw anything
      }
    }

    // Draw composite group: all ink types overlaid
    Boundary compositeBoundary = inkTypeBoundaries.get("composite");
    if (compositeBoundary != null && currentCurve != null) {
      float offsetX = compositeBoundary.start.x - currentCurve.start.x;
      float offsetY = compositeBoundary.start.y - currentCurve.start.y;
      CurvePoints cpComposite = offsetCurve(currentCurve, offsetX, offsetY);
      for (String inkKey2 : inkTypes.keySet()) {
        if (!inkKey2.equals("composite")) {
          InkType it2 = inkTypes.get(inkKey2);
          InkParameters ip2 = inkTypeParameters.get(inkKey2);
          if (it2.drawFunctionName.equals("drawCurve_VectorField")) {
            drawCurve_VectorField(ip2, cpComposite);
          } else if (it2.drawFunctionName.equals("drawCurve_Particle")) {
            drawCurve_Particle(ip2, cpComposite);
          } else if (it2.drawFunctionName.equals("drawCurve_Particle_Diffuse")) {
            drawCurve_Particle_Diffuse(ip2, cpComposite);
          } else if (it2.drawFunctionName.equals("drawCurve_Particle_Texture")) {
            drawCurve_Particle_Texture(ip2, cpComposite);
          }
        }
      }
    }
  }
}

// draw the UI elements in col 1
void createDesign_Settings() {
  
  // Refresh Button: modified so that clicking it generates and stores a new curve.
  cp5.addButton("refresh")
    .setLabel("Refresh")
    .setPosition(col1X, margin)    // Now at y = margin (e.g., 20)
    .setSize(col1Width, 20)
    .onRelease(new CallbackListener() {
      public void controlEvent(CallbackEvent event) {
        currentCurve = defineCurve(inkTypeBoundaries.get("vector field"));
        updateCurvePointsOffset();  // Update the offset curves for all ink types
        needsRedraw = true;
      }
    });
    cp5.getController("refresh").bringToFront();

  cp5.addButton("save")
    .setLabel("save")
    .setPosition(col1X, margin + 30)
    .setSize(col1Width, 20)
    .onRelease(new CallbackListener() {
      public void controlEvent(CallbackEvent event) {
        Textfield tf = cp5.get(Textfield.class, "settingName");
        String fileName = tf.getText().trim();
        if (!fileName.endsWith(".json")) {
          fileName += ".json";
        }
        saveInkParameters();
        generateSettingButtons(col1Width, margin + 120);  // see below
      }
    });

  cp5.addTextfield("settingName")
    .setPosition(col1X, margin + 60)      // position the text field directly below the save button
    .setSize(col1Width, 20)
    .setText("")
    .setAutoClear(false)
    .setColorBackground(color(200))       // white background
    .setColorValue(color(0));             // black text

  Textfield settingNameField = cp5.get(Textfield.class, "settingName");
  settingNameField.addListener(new ControlListener() {
    public void controlEvent(ControlEvent event) {
      // Check if the text field is focused.
      if (settingNameField.isFocus()) {
        // When selected, change background to a light grey (e.g., 220).
        settingNameField.setColorBackground(color(220));
      } else {
        // When not focused, set the background to white.
        settingNameField.setColorBackground(color(255));
      }
    }
  });

  cp5.addButton("default")
    .setLabel("default")
    .setPosition(col1X, margin + 90)    // 20 + 60 = 80
    .setSize(col1Width, 20)
    .setColorBackground(color(144, 238, 144)) // light green
    .setColorActive(color(144, 238, 144))     // light green
    .setColorLabel(color(0)) 
    .onRelease(new CallbackListener() {
      public void controlEvent(CallbackEvent event) {
        // Reset default and load buttons to light blue
        cp5.getController("default").setColorBackground(color(173, 216, 230));
        for (ControllerInterface<?> ctrl : cp5.getAll()) {
          String name = ctrl.getName();
          if (name.startsWith("loadSetting_")) {
            ctrl.setColorBackground(color(173, 216, 230));
          }
        }
        // Highlight default button in light green
        event.getController().setColorBackground(color(144, 238, 144));
        loadDefaultInkParameters();
      }
    });
  cp5.getController("default").bringToFront();

  generateSettingButtons(col1Width, margin + 120);
}

// Dynamically generate load buttons for each saved setting.
// These buttons will be positioned beneath the existing UI elements in col1
void generateSettingButtons(int firstColumnWidth, int topY) {
  // Filename is assumed to be "sliderSettings.json" in the data folder.
  String fileName = "sliderSettings.json";
  String fullPath = dataPath(fileName);
  
  if (!fileExists(fileName)) {
    println("No slider settings file found at " + fullPath);
    return;
  }
  
  JSONObject root = loadJSONObject(fullPath);
  JSONArray settingsArray = root.getJSONArray("settings");
  if (settingsArray == null || settingsArray.size() == 0) {
    println("No saved settings in " + fullPath);
    return;
  }
  
  int n = settingsArray.size();
  
  // Layout parameters:
  int buttonWidth = firstColumnWidth;  // Use the firstColumnWidth for button width.
  int buttonHeight = 20;               // Fixed button height.
  int baseX = 20;                      // Left column x-position.
  
  // For vertical stacking with no gap, use spacing equal to buttonHeight.
  int spacing = buttonHeight + 5;
  
  // Remove any existing dynamic load buttons (those whose names contain "loadSetting_")
  for (int i = cp5.getAll().size() - 1; i >= 0; i--) {
    ControllerInterface<?> c = cp5.getAll().get(i);
    if (c.getName().contains("loadSetting_")) {
      cp5.remove(c);
    }
  }
  
  // For each saved setting, create a button arranged vertically with no gap.
  for (int i = 0; i < n; i++) {
    JSONObject setting = settingsArray.getJSONObject(i);
    String settingName = setting.getString("name").toLowerCase(); // Ensure lower case.
    String finalSettingName = settingName;
    String btnName = "loadSetting_" + i;
    
    cp5.addButton(btnName)
       .setLabel(settingName)
       .setPosition(baseX, topY + i * spacing)
       .setSize(buttonWidth, buttonHeight)
       .setColorBackground(color(173, 216, 230))  // Light blue background.
       .setColorForeground(color(173, 216, 230))
       .setColorActive(color(150, 200, 220))
       .setColorLabel(color(0))                   // Label text in black.
       .onRelease(new CallbackListener() {
         public void controlEvent(CallbackEvent event) {
           // Reset default button to light blue
           cp5.getController("default").setColorBackground(color(173, 216, 230));
           // Reset all load buttons to light blue
           for (ControllerInterface<?> ctrl : cp5.getAll()) {
             String name = ctrl.getName();
             if (name.startsWith("loadSetting_")) {
               ctrl.setColorBackground(color(173, 216, 230));  // light blue
             }
           }
           // Highlight this button in light green
           event.getController().setColorBackground(color(144, 238, 144));  // light green
           // Load the selected settings
           loadInkParameters(finalSettingName);
         }
       });
  }
  println("Vertical load buttons generated.");
}

void loadDefaultInkParameters() {
    // Loop over each ink type.
    for (String inkKey : inkTypeParameters.keySet()) {
      // Get the default InkParameters for this ink type.
      InkParameters defaults = inkTypeParameters.get(inkKey);
      // Get the slider config array for this ink type.
      SliderConfig[] configs = inkTypeSliderConfig.get(inkKey);
      if (configs == null) continue;
      
      // For each slider parameter in the config, update the corresponding CP5 slider to the default value.
      for (int i = 0; i < configs.length; i++) {
        SliderConfig sc = configs[i];
        float defaultValue = sc.defaultValue; // default value as set in the slider config
        // Alternatively, if you want to pull it from the defaults in InkParameters, you could use reflection.
        // For simplicity, we use the defaultValue from the config.
        String sliderName = inkKey + "_" + sc.name;
        cp5.getController(sliderName).setValue(defaultValue);
      }
      
      // Update the decay type buttons for this ink type to the default decay type stored in InkParameters.
      updateDecaySelection(inkKey, defaults.decayType);
    }
    println("Default ink parameters loaded.");
  }

void createDesign_InkTypes(){

  int decayButtonX = col2X;             // Column 2 x-position (e.g., 340)
  int decayButtonY = margin;            // Start at top of column 2
  int decayButtonWidth = col2Width;     // Width of decay type buttons (150)
  int decayButtonHeight = 15;
  String[] decayTypesFinal = {"linear", "exponential", "quadratic", "cubic", "logarithmic", "sigmoidal", "quickslow"};

  // These variables are used to position the sliders in the middle column.
  int sliderX = col3X + labelAreaWidth;

  // Define starting y position for the first ink type group.
  int groupStartY = sliderY;  // sliderY is already defined (e.g., 20)
  int currentY = groupStartY;  // starting y for the first group
  int groupSpacing = 30;       // vertical gap between groups
  int headerToSlidersGap = 10;

  // Pre-calculate the maximum group height across all ink types.
  float maxGroupHeight = 0;
  for (String inkKey : inkTypeSliderConfig.keySet()) {
    SliderConfig[] params = inkTypeSliderConfig.get(inkKey);
    int groupHeight = headerToSlidersGap + (params.length - 1) * sliderSpacing + sliderHeight;
    if (groupHeight > maxGroupHeight) {
      maxGroupHeight = groupHeight;
    }
  }
  // Outer loop: for each ink type key in our HashMap.
  int groupIndex = 0;
  for (String inkKey : inkTypes.keySet()) {
    String thisInk = inkKey;   // capture the key in a variable for inner classes
    InkType currentInk = inkTypes.get(inkKey);

    // Retrieve the slider config for this ink type (min, max, default value).
    SliderConfig[] params = inkTypeSliderConfig.get(inkKey);
    if(params == null) continue;  // Skip if no sliders defined for this ink type.
    
    // Use currentY as the headerY for this group.
    int headerY = currentY;
    
    // Draw the header label for this ink type (using the ink type's name).
    // needs to use CP5 otherwise it will be cleared by draw()
    cp5.addTextlabel(currentInk.name + "_header")
       .setText(currentInk.name.toLowerCase())
       .setPosition(col2X, headerY - 10)
       .setSize(100, 20)
       .setColorValue(color(0))
       .setFont(createFont("Arial", 8));

    InkParameters ip = inkTypeParameters.get(inkKey);

    // Inner loop: create sliders for this ink type.
    for (int i = 0; i < params.length; i++) {
      SliderConfig sp = params[i];
      int sliderYPos = headerY + headerToSlidersGap + i * sliderSpacing;
      // Create a unique slider name by combining the ink type key and parameter name.
      String sliderName = inkKey + "_" + sp.name;
      cp5.addSlider(sliderName)
       .setPosition(sliderX, sliderYPos)
       .setSize(sliderWidth, sliderHeight)
       .setRange(sp.min, sp.max)
       .setValue(sp.defaultValue)
       .onChange(new CallbackListener() {
          @Override
          public void controlEvent(CallbackEvent event) {
            float newValue = event.getController().getValue();
            println("Slider " + event.getController().getName() + " changed to " + newValue);
            Field field = inkParamsFieldCache.get(sp.name);
            if (field != null) {
              try {
                if (field.getType() == float.class) {
                  field.setFloat(ip, newValue);
                } else if (field.getType() == int.class) {
                  field.setInt(ip, (int)newValue);
                }
              } catch(Exception e) {
                e.printStackTrace();
              }
            }
            needsRedraw = true;
          }
      });
      cp5.getController(sliderName).getCaptionLabel().hide();
      // reduce font size for the slider value displayed inside the slider
      ((Slider)cp5.getController(sliderName)).getValueLabel().setFont(createFont("Arial", 6));
      cp5.addTextlabel(sliderName + "_label")
        .setPosition(col3X, sliderYPos)
        .setSize(labelAreaWidth, sliderHeight)
        .setText(sp.name)
        .setColorValue(color(0))
        .setFont(createFont("Arial", 6));

      // Retrieve the cached Field object using sp.name and assign it to a local variable.
      Field field = inkParamsFieldCache.get(sp.name);
      
      // Use a try/catch block to update the corresponding field in the InkParameters object.
      try {       
        if (field != null) {
          if (field.getType() == float.class) {
            field.setFloat(ip, sp.defaultValue);
          } else if (field.getType() == int.class) {
            field.setInt(ip, (int)sp.defaultValue);
          } else if (field.getType() == String.class) {
            field.set(ip, sp.defaultValue + "");
          }
        }
      } catch (Exception e) {
        e.printStackTrace();
      }
    };

    // use the maximum computed group height.
    int groupHeight = int(maxGroupHeight);
    
    // create boundary for the curve
    Boundary groupBoundary = boundaryFromRect(col4X, headerY, width - col4X - margin, groupHeight);
    inkTypeBoundaries.put(thisInk, groupBoundary);

    // Draw the boundary for this group in Column 4.
    // note: this would need to be moved to draw() now otherwise it will get cleared anyway
    if (debug_showGeometry) {
      drawBoundary(groupBoundary);
    }
    
    // Now, create the decayType buttons in Column 2.
    String[] decayTypes = {"linear", "exponential", "quadratic", "cubic", "logarithmic", "sigmoidal", "quickslow"};
    // Starting y for decay buttons, aligned with the top of the slider group.
    int decayStartY = headerY + headerToSlidersGap;
    for (int j = 0; j < decayTypes.length; j++) {
      String dt = decayTypes[j].toLowerCase();
      String dtLabel = dt;
      // Trim the decay label to the first 3 characters.
      if (dtLabel.length() > 3) {
        dtLabel = dtLabel.substring(0, 3);
      }
      String decayButtonName = thisInk + "_decay_" + dt;
      cp5.addButton(decayButtonName)
        .setLabel(dtLabel)
        .setPosition(col2X, decayStartY + j * sliderSpacing)
        .setSize(col2Width, decayButtonHeight)
        .setColorBackground(defaultButtonColor)
        .setColorActive(selectedButtonColor)
        .setColorLabel(color(0))
        .onRelease(new CallbackListener() {
          public void controlEvent(CallbackEvent event) {
            // Get the button's name.
            String btnName = event.getController().getName();
            // Extract the selected decay type from the button name.
            String selectedDecay = btnName.substring(btnName.lastIndexOf("_") + 1);
            //decayType = selectedDecay;
            println("Selected decay type for " + thisInk + ": " + selectedDecay);
            updateDecaySelection(thisInk, selectedDecay);
            needsRedraw = true;
          }
        });
      }
      updateDecaySelection(thisInk, ip.decayType);

      // update currentY to be the start of the next group.
      currentY += groupHeight + groupSpacing;
      groupIndex++;
  }

  // Add a composite group that draws all lines on top of each other
  String compositeInkKey = "composite";
  int compositeHeaderY = currentY;

  // Create header for composite group
  cp5.addTextlabel(compositeInkKey + "_header")
     .setText("composite")
     .setPosition(col2X, compositeHeaderY - 10)
     .setSize(100, 20)
     .setColorValue(color(0))
     .setFont(createFont("Arial", 8));

  // Define boundary for composite group
  Boundary compositeBoundary = boundaryFromRect(col4X, compositeHeaderY, width - col4X - margin, int(maxGroupHeight));
  inkTypeBoundaries.put(compositeInkKey, compositeBoundary);

  // Optionally draw boundary (if debug_showGeometry is true)
  if (debug_showGeometry) {
    drawBoundary(compositeBoundary);
  }

  // Composite alpha controls
  int compositeSliderStartY = compositeHeaderY + headerToSlidersGap;
  int alphaIndex = 0;
  for (String inkKey : inkTypes.keySet()) {
    if (inkKey.equals("composite")) continue;
    InkParameters ip = inkTypeParameters.get(inkKey);
    final InkParameters ipLocal = ip;
    String sliderName = "composite_alpha_" + inkKey;
    cp5.addSlider(sliderName)
      .setPosition(sliderX, compositeSliderStartY + alphaIndex * sliderSpacing)
      .setSize(sliderWidth, sliderHeight)
      .setRange(ip.alphaMin, ip.alphaMax)
      .setValue(ip.alpha)
      .onChange(new CallbackListener() {
        public void controlEvent(CallbackEvent event) {
          float newVal = event.getController().getValue();
          ipLocal.alpha = (int)newVal;
          needsRedraw = true;
        }
      });
    cp5.getController(sliderName).getCaptionLabel().hide();
    ((Slider)cp5.getController(sliderName)).getValueLabel().setFont(createFont("Arial", 6));
    cp5.addTextlabel(sliderName + "_label")
      .setText(inkKey)
      .setPosition(col3X, compositeSliderStartY + alphaIndex * sliderSpacing)
      .setColorValue(color(0))
      .setFont(createFont("Arial", 6));
    alphaIndex++;
  }

  // Update currentY for consistency if more UI were added later
  currentY += int(maxGroupHeight) + groupSpacing;
}

void updateCurvePointsOffset() {
  // For each ink type, compute the offset curve based on the currentCurve and its boundary.
  for (String inkKey : inkTypes.keySet()) {
    Boundary b = inkTypeBoundaries.get(inkKey);
    // Ensure we have a valid boundary and a defined currentCurve.
    if (b == null || currentCurve == null) continue;
      float offsetX = b.start.x - currentCurve.start.x;
      float offsetY = b.start.y - currentCurve.start.y;
      CurvePoints offsetCP = offsetCurve(currentCurve, offsetX, offsetY);
      curvePoints_offset.put(inkKey, offsetCP);
    }
  println("Updated curvePoints_offset for all ink types.");
}

// format the decay buttons to show the selected Decay for an ink type
void updateDecaySelection(String inkKey, String selectedDecay) {
  
  // Update the InkParameters for this ink type
  InkParameters ip = inkTypeParameters.get(inkKey);
  if (ip != null) {
    ip.decayType = selectedDecay;
  }
  
  // Reset all decay buttons for this ink type to default appearance.
  for (int k = 0; k < decayTypes.length; k++) {
    String key = inkKey + "_decay_" + decayTypes[k].toLowerCase();
    ControllerInterface<?> ctrl = cp5.getController(key);
    ctrl.setColorBackground(defaultButtonColor);
    ctrl.setColorLabel(color(0));
  }
  
  // Set the selected decay button's appearance.
  String buttonKey = inkKey + "_decay_" + selectedDecay.toLowerCase();
  cp5.getController(buttonKey).setColorBackground(selectedButtonColor);
  cp5.getController(buttonKey).setColorLabel(color(255));
  
  println("Updated decay type for " + inkKey + ": " + selectedDecay);
}

void drawBoundary(Boundary b) {
  stroke(200);
  noFill();
  
  // If the arc angle is 360, draw a full circle.
  if (b.arcAngle == 360) {
    ellipse(b.start.x, b.start.y, 2 * b.arcRadius, 2 * b.arcRadius);
  } 
  // If arcAngle is greater than 0 (but less than 360), draw an arc and radial lines.
  else if (b.arcAngle > 0) {
    // Convert arcDirection to radians.
    float thetaOffset = radians(b.arcDirection);
    // Calculate half of the arc angle in radians.
    float halfArc = radians(b.arcAngle) / 2.0;
    
    // Draw the arc with diameter = 2 * arcRadius.
    arc(b.start.x, b.start.y, 2 * b.arcRadius, 2 * b.arcRadius, thetaOffset - halfArc, thetaOffset + halfArc);
    
    // Compute the endpoints of the arc.
    float angle1 = thetaOffset - halfArc;
    float angle2 = thetaOffset + halfArc;
    float x1 = b.start.x + b.arcRadius * cos(angle1);
    float y1 = b.start.y + b.arcRadius * sin(angle1);
    float x2 = b.start.x + b.arcRadius * cos(angle2);
    float y2 = b.start.y + b.arcRadius * sin(angle2);
    
    // Draw lines from the start to each endpoint.
    line(b.start.x, b.start.y, x1, y1);
    line(b.start.x, b.start.y, x2, y2);
  }
  
  // Draw a small marker at the start point.
  fill(150);
  noStroke();
  ellipse(b.start.x, b.start.y, 8, 8);
}

void loadInkParameters(String settingName) {
  String fileName = "sliderSettings.json";
  String fullPath = dataPath(fileName);
  if (!fileExists(fileName)) {
    println("No slider settings file found at " + fullPath);
    return;
  }
  
  JSONObject root = loadJSONObject(fullPath);
  JSONArray settingsArray = root.getJSONArray("settings");
  
  // Look for the setting with the matching name.
  for (int i = 0; i < settingsArray.size(); i++) {
    JSONObject setting = settingsArray.getJSONObject(i);
    if (setting.getString("name").equals(settingName)) {
      
      // Get the JSON object that holds slider settings for each ink type.
      JSONObject inkTypesJson = setting.getJSONObject("inkTypes");
      
      // For each ink type in the saved settings:
      for (Object key : inkTypesJson.keys()) {
        String inkKey = key.toString();
        JSONObject groupJson = inkTypesJson.getJSONObject(inkKey);
        // Retrieve the slider config (min, max etc) for this ink type.
        SliderConfig[] params = inkTypeSliderConfig.get(inkKey);
        if (params == null) continue;
        
        // For each parameter in the group, update its slider value.
        for (int j = 0; j < params.length; j++) {
          float value = groupJson.getFloat(params[j].name);
          String sliderName = inkKey + "_" + params[j].name;
          cp5.getController(sliderName).setValue(value);
        }
        
        // decay type buttons
        if (groupJson.hasKey("decayType")) {
          String savedDecay = groupJson.getString("decayType").toLowerCase();
          updateDecaySelection(inkKey, savedDecay);
        }

        // Update the global InkParameters for this ink type based on the loaded values.
        InkParameters ip = inkTypeParameters.get(inkKey);
        if (ip != null) {
          // For each parameter in the slider config array, update the corresponding field in ip using reflection.
          for (int j = 0; j < params.length; j++) {
            String fieldName = params[j].name;
            if (groupJson.hasKey(fieldName)) {
              FieldSetter setter = fieldSetterCache.get(fieldName);
              if (setter != null) {
                setter.setField(ip, groupJson, fieldName);
              }
            }
          }
          // Update decayType separately.
          if (groupJson.hasKey("decayType")) {
            ip.decayType = groupJson.getString("decayType");
          }
        }
      }
      println("Loaded setting: " + settingName);
      return;
    }
  }
  println("No setting found with name: " + settingName);
}

// Save slider settings and selected decay button to a JSON file.
void saveInkParameters() {
  String fileName = "sliderSettings.json";
  String fullPath = dataPath(fileName);

  
  JSONObject root;
  JSONArray settingsArray;
  
  // If the file exists, load it; otherwise, create a new JSON object.
  if (fileExists(fileName)) {
    root = loadJSONObject(fullPath);
    settingsArray = root.getJSONArray("settings");
    if (settingsArray == null) {
      settingsArray = new JSONArray();
    }
  } else {
    root = new JSONObject();
    settingsArray = new JSONArray();
  }
  
  // Get the setting name from the text field named "settingName".
  Textfield tf = cp5.get(Textfield.class, "settingName");
  String settingName = tf.getText().trim();
  println("Saving setting name: " + settingName);
  
  // Create a new JSON object for the current slider settings.
  JSONObject newSetting = new JSONObject();
  newSetting.setString("name", settingName);
  
  // Create a JSON object to hold slider settings for each ink type.
  JSONObject inkTypesJson = new JSONObject();
  
  // Iterate over each ink type.
  for (String inkKey : inkTypes.keySet()) {
    // Create a JSON object for this ink type group.
    JSONObject groupJson = new JSONObject();
    // Get the slider parameters for this ink type.
    SliderConfig[] params = inkTypeSliderConfig.get(inkKey);
    if (params == null) continue;
    
    // For each slider parameter, retrieve the current value from the controller.
    for (int i = 0; i < params.length; i++) {
      String sliderName = inkKey + "_" + params[i].name;
      // Retrieve the current slider value from cp5.
      float value = cp5.getController(sliderName).getValue();
      groupJson.setFloat(params[i].name, value);
    }
    
    // Retrieve the decay type for this ink type.
    String selectedDecay = "";
    for (int k = 0; k < decayTypes.length; k++) {
      InkParameters ip = inkTypeParameters.get(inkKey);
      if(ip != null) {
        groupJson.setString("decayType", ip.decayType);
      } else {
        groupJson.setString("decayType", "quickslow");
      }
    }
    
    // Store this group's settings into the inkTypes JSON object.
    inkTypesJson.setJSONObject(inkKey, groupJson);
  }
  
  newSetting.setJSONObject("inkTypes", inkTypesJson);

  // Save composite alpha settings so composite curve can be recreated
  JSONObject compositeJson = new JSONObject();
  for (String inkKey : inkTypes.keySet()) {
    if (inkKey.equals("composite")) continue;
    String sliderName = "composite_alpha_" + inkKey;
    float alphaVal = cp5.getController(sliderName).getValue();
    compositeJson.setInt(inkKey, (int)alphaVal);
  }
  newSetting.setJSONObject("compositeAlphas", compositeJson);
  
  // Check if a setting with this name already exists; if so, replace it.
  boolean found = false;
  for (int i = 0; i < settingsArray.size(); i++) {
    JSONObject existingSetting = settingsArray.getJSONObject(i);
    if (existingSetting.getString("name").equals(settingName)) {
      settingsArray.setJSONObject(i, newSetting);
      found = true;
      println("Existing setting found. Replacing with new settings.");
      break;
    }
  }
  
  if (!found) {
    settingsArray.append(newSetting);
    println("No existing setting found. Appending new settings.");
  }
  
  root.setJSONArray("settings", settingsArray);
  saveJSONObject(root, fullPath);
  println("Slider settings saved to " + fullPath);
}

// Overloaded version: when no boundary parameter is provided, use the default boundary.
CurvePoints defineCurve() {
  // Use a default boundary with start at (0,0) or any desired default
  Boundary defaultBoundary = new Boundary(new PVector(0,0), 0, 0, 0);
  return defineCurve(defaultBoundary);
}

// define control points for a bezier curve.
CurvePoints defineCurve(Boundary boundary) {
  PVector start = boundary.start;  // extract the start point from boundary
  PVector cp1;
  PVector cp2;
  PVector end;

  // For circle/arc-based styles.
  // radius of circle or arc; maximum distance of end point from start.
  float radiusMax;

  // Initialize variables with default values.
  float arcAngle = 0;
  float cp1Min = 0, cp1Max = 0, cp2Min = 0, cp2Max = 0, endMin = 0, endMax = 0;

  if (boundary.arcRadius == 0) {
    // no boundary segment provided, so generate control points and endpoint anywhere.
    cp1 = new PVector(random(width), random(height));
    cp2 = new PVector(random(width), random(height));
    end = new PVector(random(width), random(height));
    return new CurvePoints(start, cp1, cp2, end);
  }
   // Convert the boundary's arcDirection to radians.
  float thetaOffset = radians(boundary.arcDirection);
  // Allowed angular range is ± half the arcAngle (converted to radians)
  float halfArc = radians(boundary.arcAngle) / 2.0;
  
  // Generate random angles for the control points and end point within the allowed arc.
  float angle1 = thetaOffset + random(-halfArc, halfArc);
  float angle2 = thetaOffset + random(-halfArc, halfArc);
  float angle3 = thetaOffset + random(-halfArc, halfArc);
  
  // Choose random radii (distances from the start) ensuring the points lie within the boundary.
  // You can adjust these multipliers as needed for aesthetics.
  float r1 = random(0.2, 0.5) * boundary.arcRadius;
  float r2 = random(0.2, 0.7) * boundary.arcRadius;
  float r3 = random(0.4, 1.0) * boundary.arcRadius;
  
  // Compute control and end points.
  cp1 = new PVector(start.x + r1 * cos(angle1), start.y + r1 * sin(angle1));
  cp2 = new PVector(start.x + r2 * cos(angle2), start.y + r2 * sin(angle2));
  end = new PVector(start.x + r3 * cos(angle3), start.y + r3 * sin(angle3));
    
  if (debug_showGeometry) {
    strokeWeight(1);
    stroke(150);
    noFill();
    // Draw arc boundaries for controlPoint1.
    arc(start.x, start.y, 2*cp1Min, 2*cp1Min, thetaOffset - arcAngle/2, thetaOffset + arcAngle/2);
    arc(start.x, start.y, 2*cp1Max, 2*cp1Max, thetaOffset - arcAngle/2, thetaOffset + arcAngle/2);
    // Draw arc boundaries for controlPoint2.
    arc(start.x, start.y, 2*cp2Min, 2*cp2Min, thetaOffset - arcAngle/2, thetaOffset + arcAngle/2);
    arc(start.x, start.y, 2*cp2Max, 2*cp2Max, thetaOffset - arcAngle/2, thetaOffset + arcAngle/2);
    // Draw arc boundaries for the endpoint.
    arc(start.x, start.y, 2*endMin, 2*endMin, thetaOffset - arcAngle/2, thetaOffset + arcAngle/2);
    arc(start.x, start.y, 2*endMax, 2*endMax, thetaOffset - arcAngle/2, thetaOffset + arcAngle/2);
    noStroke();
    fill(150);
    ellipse(cp1.x, cp1.y, 8, 8);
    ellipse(cp2.x, cp2.y, 8, 8);
    ellipse(end.x, end.y, 8, 8);
    ellipse(start.x, start.y, 8, 8);
    // Draw connecting lines for the endpoint outer arc.
    PVector endOuterLeft = new PVector(start.x + endMax*cos(thetaOffset - arcAngle/2), start.y + endMax*sin(thetaOffset - arcAngle/2));
    PVector endOuterRight = new PVector(start.x + endMax*cos(thetaOffset + arcAngle/2), start.y + endMax*sin(thetaOffset + arcAngle/2));
    stroke(150);
    line(start.x, start.y, endOuterLeft.x, endOuterLeft.y);
    line(start.x, start.y, endOuterRight.x, endOuterRight.y);
  }

  // check if cp1, cp2, or end are out-of-bounds,
  // if so compute a uniform scaling factor, and adjust them relative to start
  // so that outermost point now sits on edge of drawing and curve is reduced proportionally.
  float s1 = computeScalingFactor(start, cp1);
  float s2 = computeScalingFactor(start, cp2);
  float s3 = computeScalingFactor(start, end);
  float s_total = min(s1, min(s2, s3));
  if (s_total < 1.0) {
    cp1 = PVector.add(start, PVector.mult(PVector.sub(cp1, start), s_total));
    cp2 = PVector.add(start, PVector.mult(PVector.sub(cp2, start), s_total));
    end = PVector.add(start, PVector.mult(PVector.sub(end, start), s_total));
  }
  return new CurvePoints(start, cp1, cp2, end);
}

CurvePoints randomCurvePoints(Boundary boundary) {
  PVector start = boundary.start;
  PVector cp1;
  PVector cp2;
  PVector end;
  
  if (boundary.arcRadius == 0) {
    // No boundary provided, generate control points and endpoint anywhere
    cp1 = new PVector(random(width), random(height));
    cp2 = new PVector(random(width), random(height));
    end = new PVector(random(width), random(height));
  } else {
    float radiusMax = boundary.arcRadius;
    float arcAngle = boundary.arcAngle;
    float cp1Min = 0.2 * radiusMax;
    float cp1Max = 0.3 * radiusMax;
    float cp2Min = 0.3 * radiusMax;
    float cp2Max = 0.5 * radiusMax;
    float endMin = 0.5 * radiusMax;
    float endMax = radiusMax;
    
    // Convert boundary direction from degrees to radians
    float thetaOffset = radians(boundary.arcDirection);
    
    float theta1 = thetaOffset + random(-arcAngle/2, arcAngle/2);
    float r1 = random(cp1Min, cp1Max);
    cp1 = new PVector(start.x + r1 * cos(theta1), start.y + r1 * sin(theta1));
    
    float theta2 = thetaOffset + random(-arcAngle/2, arcAngle/2);
    float r2 = random(cp2Min, cp2Max);
    cp2 = new PVector(start.x + r2 * cos(theta2), start.y + r2 * sin(theta2));
    
    float theta3 = thetaOffset + random(-arcAngle/2, arcAngle/2);
    float r3 = random(endMin, endMax);
    end = new PVector(start.x + r3 * cos(theta3), start.y + r3 * sin(theta3));
    
    if (debug_showGeometry) {
      strokeWeight(1);
      stroke(150);
      noFill();
      // Draw arc boundaries for controlPoint1
      arc(start.x, start.y, 2*cp1Min, 2*cp1Min, thetaOffset - arcAngle/2, thetaOffset + arcAngle/2);
      arc(start.x, start.y, 2*cp1Max, 2*cp1Max, thetaOffset - arcAngle/2, thetaOffset + arcAngle/2);
      // Draw arc boundaries for controlPoint2
      arc(start.x, start.y, 2*cp2Min, 2*cp2Min, thetaOffset - arcAngle/2, thetaOffset + arcAngle/2);
      arc(start.x, start.y, 2*cp2Max, 2*cp2Max, thetaOffset - arcAngle/2, thetaOffset + arcAngle/2);
      // Draw arc boundaries for the endpoint
      arc(start.x, start.y, 2*endMin, 2*endMin, thetaOffset - arcAngle/2, thetaOffset + arcAngle/2);
      arc(start.x, start.y, 2*endMax, 2*endMax, thetaOffset - arcAngle/2, thetaOffset + arcAngle/2);
      noStroke();
      fill(150);
      ellipse(cp1.x, cp1.y, 8, 8);
      ellipse(cp2.x, cp2.y, 8, 8);
      ellipse(end.x, end.y, 8, 8);
      ellipse(start.x, start.y, 8, 8);
      // Draw connecting lines for the endpoint outer arc
      PVector endOuterLeft = new PVector(start.x + endMax*cos(thetaOffset - arcAngle/2), start.y + endMax*sin(thetaOffset - arcAngle/2));
      PVector endOuterRight = new PVector(start.x + endMax*cos(thetaOffset + arcAngle/2), start.y + endMax*sin(thetaOffset + arcAngle/2));
      stroke(150);
      line(start.x, start.y, endOuterLeft.x, endOuterLeft.y);
      line(start.x, start.y, endOuterRight.x, endOuterRight.y);
    }
  }
  
  // Adjust control points if any are out of bounds
  float s1 = computeScalingFactor(start, cp1);
  float s2 = computeScalingFactor(start, cp2);
  float s3 = computeScalingFactor(start, end);
  float s_total = min(s1, min(s2, s3));
  if (s_total < 1.0) {
    cp1 = PVector.add(start, PVector.mult(PVector.sub(cp1, start), s_total));
    cp2 = PVector.add(start, PVector.mult(PVector.sub(cp2, start), s_total));
    end = PVector.add(start, PVector.mult(PVector.sub(end, start), s_total));
  }
  
  return new CurvePoints(start, cp1, cp2, end);
}

// draw an ink stroke as a series of overlapping particles
void drawCurve_Particle(InkParameters inkParams, CurvePoints cp) {
  // drawCurve_Particle draws an ink stroke as a series of overlapping particles (droplets)
  // along a Bezier curve. Each particle's size is modulated by a decay function based on its position along the stroke.
  
  // Extract line options:
  // - lineWidth: the base stroke width which is later scaled by the decay factor.
  float lineWidth = inkParams.lineWidth;
  
  // Extract ink options:
  // - inkFraction: fraction of the stroke drawn at full strength.
  // - decayType, exponent, slope, initialMultiplier, velocity: parameters to control the decay behavior.
  float inkFraction = inkParams.inkFraction;
  String decayType = inkParams.decayType;
  float exponent = inkParams.exponent;
  float slope = inkParams.slope;
  float initialMultiplier = inkParams.initialMultiplier;
  float velocity = inkParams.velocity;  // Not used in 'quickslow' mo/ Create an array to store positions along the provided Bezier curve
  int numParticles = inkParams.numParticles;   // - numParticles: determines the density of particles along the stroke.

  // Create an array to store positions along the Bezier curve.
  PVector[] positions = new PVector[numParticles];
  
  // Generate positions along the Bezier curve.
  // 't' is a normalized parameter (0 to 1) representing the position along the curve.
  // A slight random offset is added to simulate natural variation.
  for (int i = 0; i < numParticles; i++) {
    float t = i / float(numParticles - 1);
    float x = bezierPoint(cp.start.x, cp.control1.x, cp.control2.x, cp.end.x, t);
    float y = bezierPoint(cp.start.y, cp.control1.y, cp.control2.y, cp.end.y, t);
    PVector pos = new PVector(x, y);
    pos.add(PVector.random2D().mult(0.5));  // Slight random offset for natural variation
    positions[i] = pos;
  }
  
  noStroke();
  fill(inkParams.greyscale, inkParams.alpha);  // Use greyscale slider for color and alpha for transparency
  
  // Draw droplets along the Bezier curve with sizes determined by the decay function
  // For each particle, compute a decay factor based on its normalized position 't'.
  // The decay factor modifies the base lineWidth to simulate the fading or diffusion of ink.
  for (int i = 0; i < numParticles; i++) {
    float t = i / float(numParticles - 1);
    float factor;
    
    if (t < inkFraction) {
      factor = initialMultiplier;
    } else {
      float x = (t - inkFraction) / (1 - inkFraction);
      if(decayType.equalsIgnoreCase("linear")) {
        factor = map(t, inkFraction, 1, initialMultiplier, 0);
      } else if(decayType.equalsIgnoreCase("exponential")) {
        factor = pow(1 - x, exponent) * initialMultiplier;
      } else if(decayType.equalsIgnoreCase("quadratic")) {
        factor = (1 - sq(x)) * initialMultiplier;
      } else if(decayType.equalsIgnoreCase("cubic")) {
        factor = (1 - pow(x, 3)) * initialMultiplier;
      } else if(decayType.equalsIgnoreCase("logarithmic")) {
        factor = (1 - log(1 + 9 * x) / log(10)) * initialMultiplier;
      } else if(decayType.equalsIgnoreCase("sigmoidal")) {
        float slopeNorm = slope;  // full 0–100 range for maximum contrast
        factor = (1 / (1 + exp(slopeNorm * (t - 0.5)))) * initialMultiplier;
      } else if(decayType.equalsIgnoreCase("quickslow")) {
        factor = (1 - sqrt(x)) * initialMultiplier;
      } else {
        factor = map(t, inkFraction, 1, initialMultiplier, 0);
      }
    }
    // Calculate the droplet size by scaling lineWidth with the decay factor.   
    float dropletSize = lineWidth * factor;
    ellipse(positions[i].x, positions[i].y, dropletSize, dropletSize);
  }
}

// draw an ink stroke with a textured brush appearance.
void drawCurve_Particle_Texture(InkParameters inkParams, CurvePoints cp) {

  // Each particle is rendered using a brush texture with alpha blending to mimic a painted stroke.

  int numParticles = inkParams.numParticles;
  float lineWidth = inkParams.lineWidth;
  
  // Create an array to store positions along the provided Bezier curve
  PVector[] positions = new PVector[numParticles];
  
  // Generate positions along the curve using Processing's bezierPoint function
  for (int i = 0; i < numParticles; i++) {
    float t = i / float(numParticles - 1);
    float x = bezierPoint(cp.start.x, cp.control1.x, cp.control2.x, cp.end.x, t);
    float y = bezierPoint(cp.start.y, cp.control1.y, cp.control2.y, cp.end.y, t);
    PVector pos = new PVector(x, y);
    pos.add(PVector.random2D().mult(0.5));  // Slight random offset for natural variation
    positions[i] = pos;
  }
  
  // Set blend mode to enable alpha blending for our brush texture
  blendMode(BLEND);
  
  // Load the brush texture once, outside the loop
  PImage brushImg;
  if (inkParams.brushTexture != null) {
    brushImg = inkParams.brushTexture;
  } else {
    brushImg = loadImage("brush.png");
    inkParams.brushTexture = brushImg;
  }
  // For each position along the curve, compute a decay factor to determine the brush size.
  for (int i = 0; i < numParticles; i++) {
    float t = i / float(numParticles - 1);
    float factor;
    // Determine the decay factor based on t and the ink options.
    if (t < inkParams.inkFraction) {
      factor = inkParams.initialMultiplier;
    } else {
      float xVal = (t - inkParams.inkFraction) / (1 - inkParams.inkFraction);
      if (inkParams.decayType.equalsIgnoreCase("linear")) {
        factor = map(t, inkParams.inkFraction, 1, inkParams.initialMultiplier, 0);
      } else if (inkParams.decayType.equalsIgnoreCase("exponential")) {
        factor = pow(1 - xVal, inkParams.exponent) * inkParams.initialMultiplier;
      } else if (inkParams.decayType.equalsIgnoreCase("quadratic")) {
        factor = (1 - sq(xVal)) * inkParams.initialMultiplier;
      } else if (inkParams.decayType.equalsIgnoreCase("cubic")) {
        factor = (1 - pow(xVal, 3)) * inkParams.initialMultiplier;
      } else if (inkParams.decayType.equalsIgnoreCase("logarithmic")) {
        factor = (1 - log(1 + 9 * xVal) / log(10)) * inkParams.initialMultiplier;
      } else if (inkParams.decayType.equalsIgnoreCase("sigmoidal")) {
        float slopeNorm = inkParams.slope;  // full 0–100 range for maximum contrast
        factor = (1 / (1 + exp(slopeNorm * (xVal - 0.5)))) * inkParams.initialMultiplier;
      } else if (inkParams.decayType.equalsIgnoreCase("quickslow")) {
        factor = (1 - sqrt(xVal)) * inkParams.initialMultiplier;
      } else {
        factor = map(t, inkParams.inkFraction, 1, inkParams.initialMultiplier, 0);
      }
    }
    // Determine brush size using the base lineWidth scaled by the decay factor.
    float brushSize = lineWidth * factor;
    // Set tint with an alpha value to enable soft blending (per-curve alpha)
    tint(inkParams.greyscale, inkParams.greyscale, inkParams.greyscale, inkParams.alpha);  // Use greyscale slider for brush tint and alpha for transparency
    // Draw the brush texture centered at the calculated position.
    imageMode(CENTER);
    image(brushImg, positions[i].x, positions[i].y, brushSize, brushSize);
  }
  // Restore default image mode (top-left corner alignment).
  imageMode(CORNER);
}

// draw an ink stroke using a blur filter to simulate ink diffusion and bleed on porous paper.
void drawCurve_Particle_Diffuse(InkParameters inkParams, CurvePoints cp) {
  // draws an ink stroke onto an offscreen buffer,
  // then applies a blur filter to simulate ink diffusion and bleed on porous paper.

  // create an offscreen graphics layer to draw the stroke.
  PGraphics strokeLayer = createGraphics(width, height);
  strokeLayer.beginDraw();
  // Clear buffer with a transparent background.
  strokeLayer.clear();
  strokeLayer.noStroke();
  strokeLayer.fill(inkParams.greyscale, inkParams.alpha);  // Use greyscale slider for color and alpha for transparency

  int numParticles = inkParams.numParticles;
  float lineWidth = inkParams.lineWidth;
  
  // Create an array to store positions along the provided Bezier curve.
  PVector[] positions = new PVector[numParticles];
  
  // Compute positions along the curve using bezierPoint.
  // float 't' ranges from 0 to 1, and a small random offset is added for natural variation.
  for (int i = 0; i < numParticles; i++) {
    float t = i / float(numParticles - 1);
    float x = bezierPoint(cp.start.x, cp.control1.x, cp.control2.x, cp.end.x, t);
    float y = bezierPoint(cp.start.y, cp.control1.y, cp.control2.y, cp.end.y, t);
    PVector pos = new PVector(x, y);
    pos.add(PVector.random2D().mult(0.5));  // Slight random offset for natural variation
    positions[i] = pos;
  }
  
  // Draw each droplet along the curve onto the offscreen buffer using a decay function,
  // similar to createLine_Particle.
  for (int i = 0; i < numParticles; i++) {
    float t = i / float(numParticles - 1);
    float factor;
    
    if (t < inkParams.inkFraction) {
      factor = inkParams.initialMultiplier;
    } else {
      float xVal = (t - inkParams.inkFraction) / (1 - inkParams.inkFraction);
      if (inkParams.decayType.equalsIgnoreCase("linear")) {
        factor = map(t, inkParams.inkFraction, 1, inkParams.initialMultiplier, 0);
      } else if (inkParams.decayType.equalsIgnoreCase("exponential")) {
        factor = pow(1 - xVal, inkParams.exponent) * inkParams.initialMultiplier;
      } else if (inkParams.decayType.equalsIgnoreCase("quadratic")) {
        factor = (1 - sq(xVal)) * inkParams.initialMultiplier;
      } else if (inkParams.decayType.equalsIgnoreCase("cubic")) {
        factor = (1 - pow(xVal, 3)) * inkParams.initialMultiplier;
      } else if (inkParams.decayType.equalsIgnoreCase("logarithmic")) {
        factor = (1 - log(1 + 9 * xVal) / log(10)) * inkParams.initialMultiplier;
      } else if (inkParams.decayType.equalsIgnoreCase("sigmoidal")) {
        float slopeNorm = inkParams.slope;  // full 0–100 range for maximum contrast
        factor = (1 / (1 + exp(slopeNorm * (xVal - 0.5)))) * inkParams.initialMultiplier;
      } else if (inkParams.decayType.equalsIgnoreCase("quickslow")) {
        factor = (1 - sqrt(xVal)) * inkParams.initialMultiplier;
      } else {
        factor = map(t, inkParams.inkFraction, 1, inkParams.initialMultiplier, 0);
      }
    }
    
    // Determine the droplet size by scaling lineWidth with the computed decay factor.
    float dropletSize = lineWidth * factor;
    strokeLayer.ellipse(positions[i].x, positions[i].y, dropletSize, dropletSize);
  }
  
  strokeLayer.endDraw();
  
  // Simulate diffusion/bleed by applying iterative blur filters.
  int diffusionIterations = 3;  // Number of iterations; adjust to control the diffusion effect.
  float blurAmount = 1.0;         // Blur radius for each iteration.
  for (int i = 0; i < diffusionIterations; i++) {
    strokeLayer.filter(BLUR, blurAmount);
  }
  
  // Composite the diffused stroke from the offscreen buffer onto the main canvas.
  image(strokeLayer, 0, 0);
}

// drawCurve_VectorField draws a smooth stroke along a Bezier curve, then distorts it 
void drawCurve_VectorField(InkParameters inkParams, CurvePoints cp) {

  // using a noise-based vector field to simulate organic, wavy ink edges.
  // The stroke thickness is modulated along its length
  
  // Generate a smooth stroke along the Bezier curve.
  int numPoints = inkParams.numParticles;  // Number of points sampled along the curve.
  float baseLineWidth = inkParams.lineWidth; // Base stroke width.
  
  // Array to hold the original, smooth points.
  PVector[] basePoints = new PVector[numPoints];
  for (int i = 0; i < numPoints; i++) {
    float t = i / float(numPoints - 1); // Normalized parameter (0 to 1)
    float x = bezierPoint(cp.start.x, cp.control1.x, cp.control2.x, cp.end.x, t);
    float y = bezierPoint(cp.start.y, cp.control1.y, cp.control2.y, cp.end.y, t);
    basePoints[i] = new PVector(x, y);
  }
  
  // Use the distortion parameters
  float distortionScale = inkParams.distortionScale; // Maximum displacement in pixels
  float noiseScale = inkParams.noiseScale; // Frequency of noise variations; adjust for wavy effect.
  float staticTime = 1.0;      // Static time value for noise (for a static drawing) - not required for a 2D drawing but kept for possible future use
  
  // Distort the stroke using a noise-based vector field.
  PVector[] distortedPoints = new PVector[numPoints];
  for (int i = 0; i < numPoints; i++) {
    PVector base = basePoints[i];

    float noiseX = noise(base.x * noiseScale, base.y * noiseScale, staticTime * 0.01);
    float noiseY = noise(base.y * noiseScale, base.x * noiseScale, staticTime * 0.01);
    float dx = map(noiseX, 0, 1, -distortionScale, distortionScale);
    float dy = map(noiseY, 0, 1, -distortionScale, distortionScale);
    distortedPoints[i] = new PVector(base.x + dx, base.y + dy);
  }
  
  // 3. Draw the distorted stroke as a series of line segments with variable stroke weight.
  noFill();
  stroke(inkParams.greyscale, inkParams.alpha);  // Use greyscale slider for stroke color and alpha for transparency
  
  for (int i = 0; i < numPoints - 1; i++) {
    float t1 = i / float(numPoints - 1);
    float t2 = (i + 1) / float(numPoints - 1);
    float avgT = (t1 + t2) / 2.0;  // Midpoint parameter
    
    // Compute the decay factor based on avgT.
    float factor;
    if (avgT < inkParams.inkFraction) {
      factor = inkParams.initialMultiplier;
    } else {
      float xVal = (avgT - inkParams.inkFraction) / (1 - inkParams.inkFraction);
      if (inkParams.decayType.equalsIgnoreCase("linear")) {
        factor = map(avgT, inkParams.inkFraction, 1, inkParams.initialMultiplier, 0);
      } else if (inkParams.decayType.equalsIgnoreCase("exponential")) {
        factor = pow(1 - xVal, inkParams.exponent) * inkParams.initialMultiplier;
      } else if (inkParams.decayType.equalsIgnoreCase("quadratic")) {
        factor = (1 - sq(xVal)) * inkParams.initialMultiplier;
      } else if (inkParams.decayType.equalsIgnoreCase("cubic")) {
        factor = (1 - pow(xVal, 3)) * inkParams.initialMultiplier;
      } else if (inkParams.decayType.equalsIgnoreCase("logarithmic")) {
        factor = (1 - log(1 + 9 * xVal) / log(10)) * inkParams.initialMultiplier;
      } else if (inkParams.decayType.equalsIgnoreCase("sigmoidal")) {
        float slopeNorm = inkParams.slope;  // full 0–100 range for maximum contrast
        factor = (1 / (1 + exp(slopeNorm * (xVal - 0.5)))) * inkParams.initialMultiplier;
      } else if (inkParams.decayType.equalsIgnoreCase("quickslow")) {
        factor = (1 - sqrt(xVal)) * inkParams.initialMultiplier;
      } else {
        factor = map(avgT, inkParams.inkFraction, 1, inkParams.initialMultiplier, 0);
      }
    }
    
    // Modulate the segment's stroke weight.
    float segmentWeight = baseLineWidth * factor;
    strokeWeight(segmentWeight);
    line(distortedPoints[i].x, distortedPoints[i].y, distortedPoints[i+1].x, distortedPoints[i+1].y);
  }
}




