// LayerPermutations.pde
// Build static composites for EVERY permutation of n images.
// Place source images in "data/input". Outputs go to "output/".
//
// Usage:
// 1) Put source images (PNG/JPG) into "data/input" in this sketch.
// 2) Run the sketch; composites are saved to "output/" next to the sketch folder.
//
// Notes:
// - Permutations grow fast: n! (e.g., 6 images => 720 outputs). Use MAX_PERMS while testing.
// - Modes implemented here: NORMAL, MULTIPLY, SCREEN, OVERLAY, LIGHTEN, DARKEN, DIFFERENCE, ADD, SUBTRACT, SOFTLIGHT
// - You can fix one mode for all layers, or cycle through a list of modes per layer index.
//
// ------------------------------------
// User Settings
// ------------------------------------
String INPUT_DIR   = "input";       // relative to /data
String OUTPUT_DIR  = "output";      // relative to sketch folder
int TARGET_W = -1;                  // -1 = use first image width
int TARGET_H = -1;                  // -1 = use first image height
float LAYER_OPACITY = 1.0;          // 0..1 opacity for each added layer
boolean RESIZE_TO_FIRST = true;     // force all layers to size of first image
boolean CYCLE_MODES = true;         // cycle through modes list per layer
int MAX_PERMS = -1;                 // -1 = no cap; e.g. set 50 while testing

// Choose one or more modes to use (cycled or single)
String[] MODES = new String[]{
  "MULTIPLY", "SCREEN", "OVERLAY", "LIGHTEN", "DARKEN"
};

// ------------------------------------
// Runtime Variables
// ------------------------------------
ArrayList<PImage> images = new ArrayList<PImage>();
ArrayList<String> names  = new ArrayList<String>();
ArrayList<int[]> perms   = new ArrayList<int[]>();
int produced = 0;

void settings() {
  size(800, 800); // canvas not used for output; headless pipeline
}

void setup() {
  println("=== Layer Permutations ===");
  println("Source folder: data/" + INPUT_DIR);
  println("Output folder: " + OUTPUT_DIR);

  // Load images
  File dir = new File(dataPath(INPUT_DIR));
  if (!dir.exists() || !dir.isDirectory()) {
    println("✖ Input folder not found: " + dir.getAbsolutePath());
    println("Create 'data/input' and add images.");
    exit();
  }

  // Filter supported extensions
  String[] exts = {".png", ".jpg", ".jpeg"};
  File[] files = dir.listFiles();
  if (files == null || files.length == 0) {
    println("✖ No files in input folder.");
    exit();
  }

  for (File f : files) {
    String nm = f.getName().toLowerCase();
    if (endsWithAny(nm, exts)) {
      PImage im = loadImage(INPUT_DIR + "/" + f.getName());
      if (im == null) continue;
      images.add(im);
      names.add(f.getName());
      println("Loaded: " + f.getName() + " (" + im.width + "x" + im.height + ")");
    }
  }

  if (images.size() < 2) {
    println("✖ Need at least 2 images. Found: " + images.size());
    exit();
  }

  // Target size
  if (RESIZE_TO_FIRST) {
    TARGET_W = images.get(0).width;
    TARGET_H = images.get(0).height;
  } else {
    if (TARGET_W <= 0 || TARGET_H <= 0) {
      TARGET_W = images.get(0).width;
      TARGET_H = images.get(0).height;
    }
  }

  // Normalize sizes
  for (int i = 0; i < images.size(); i++) {
    PImage src = images.get(i);
    if (src.width != TARGET_W || src.height != TARGET_H) {
      PImage scaled = createImage(TARGET_W, TARGET_H, ARGB);
      scaled.copy(src, 0, 0, src.width, src.height, 0, 0, TARGET_W, TARGET_H);
      images.set(i, scaled);
      println("Resized: " + names.get(i) + " -> " + TARGET_W + "x" + TARGET_H);
    }
  }

  // Build permutations
  int n = images.size();
  int[] baseIdx = new int[n];
  for (int i = 0; i < n; i++) baseIdx[i] = i;
  permute(baseIdx, 0);

  println("Images: " + images.size());
  println("Permutations: " + perms.size());

  // Ensure output dir
  File outDir = new File(sketchPath(OUTPUT_DIR));
  outDir.mkdirs();

  // Process permutations
  for (int p = 0; p < perms.size(); p++) {
    if (MAX_PERMS > 0 && produced >= MAX_PERMS) break;

    int[] order = perms.get(p);
    PImage out = images.get(order[0]).copy();

    // Blend each subsequent layer
    for (int li = 1; li < order.length; li++) {
      PImage top = images.get(order[li]);
      String mode = CYCLE_MODES ? MODES[(li - 1) % MODES.length] : MODES[0];
      out = blendTwo(out, top, mode, LAYER_OPACITY);
    }

    // Build filename with order + modes used
    String ordStr = joinInt(order, "-");
    String modeStr = (CYCLE_MODES ? join(MODES, "-") : MODES[0]);
    String fname = String.format("perm_%s__modes_%s.png", ordStr, modeStr);

    out.save(sketchPath(OUTPUT_DIR + "/" + fname));
    produced++;

    if (p % 25 == 0) println("Saved: " + fname);
  }

  println("✔ Done. Wrote " + produced + " composite(s) to: " + sketchPath(OUTPUT_DIR));
  exit();
}

// ------------------------------------
// Blending
// ------------------------------------
// Blend top into base using mode and opacity (0..1)
PImage blendTwo(PImage base, PImage top, String mode, float opacity) {
  PImage out = createImage(base.width, base.height, ARGB);
  base.loadPixels();
  top.loadPixels();
  out.loadPixels();

  int len = base.pixels.length;
  for (int i = 0; i < len; i++) {
    int cb = base.pixels[i];
    int ct = top.pixels[i];

    float br = red(cb), bg = green(cb), bb = blue(cb), ba = alpha(cb) / 255.0;
    float tr = red(ct), tg = green(ct), tb = blue(ct), ta = alpha(ct) / 255.0;

    // Effective alpha of top after user opacity
    float aTop = constrain(ta * opacity, 0, 1);

    // Apply blend mode to RGB (0..255 math)
    float rBlend = applyMode(br, tr, mode);
    float gBlend = applyMode(bg, tg, mode);
    float bBlend = applyMode(bb, tb, mode);

    // Alpha composite: out = (1 - aTop)*base + aTop*blend
    float r = (1 - aTop) * br + aTop * rBlend;
    float g = (1 - aTop) * bg + aTop * gBlend;
    float b = (1 - aTop) * bb + aTop * bBlend;
    float a = 255 * (ba + aTop - ba * aTop); // standard Porter-Duff "over"

    out.pixels[i] = color(constrain(r, 0, 255), constrain(g, 0, 255), constrain(b, 0, 255), constrain(a, 0, 255));
  }

  out.updatePixels();
  return out;
}

// Apply blend mode to a single channel (0..255)
float applyMode(float b, float t, String mode) {
  float r;
  if (mode.equals("NORMAL")) {
    r = t;
  } else if (mode.equals("MULTIPLY")) {
    r = (b * t) / 255.0;
  } else if (mode.equals("SCREEN")) {
    r = 255 - ((255 - b) * (255 - t)) / 255.0;
  } else if (mode.equals("OVERLAY")) {
    r = (b < 128) ? (2 * b * t / 255.0) : (255 - 2 * (255 - b) * (255 - t) / 255.0);
  } else if (mode.equals("LIGHTEN")) {
    r = max(b, t);
  } else if (mode.equals("DARKEN")) {
    r = min(b, t);
  } else if (mode.equals("DIFFERENCE")) {
    r = abs(b - t);
  } else if (mode.equals("ADD")) {
    r = b + t;          // will be clamped later
  } else if (mode.equals("SUBTRACT")) {
    r = b - t;          // will be clamped later
  } else if (mode.equals("SOFTLIGHT")) {
    // Approximate soft light (Photoshop-like)
    float tN = t / 255.0;
    r = (1 - 2 * tN) * b * b / 255.0 + 2 * tN * b;
  } else {
    // Fallback to NORMAL
    r = t;
  }
  return constrain(r, 0, 255);
}

// ------------------------------------
// Permutations
// ------------------------------------
void permute(int[] arr, int l) {
  if (l == arr.length - 1) {
    perms.add(arr.clone());
    return;
  }
  for (int i = l; i < arr.length; i++) {
    swap(arr, l, i);
    permute(arr, l + 1);
    swap(arr, l, i);
  }
}

void swap(int[] a, int i, int j) {
  int tmp = a[i]; a[i] = a[j]; a[j] = tmp;
}

// ------------------------------------
// Helpers
// ------------------------------------
boolean endsWithAny(String s, String[] suffixes) {
  for (String suf : suffixes) if (s.endsWith(suf)) return true;
  return false;
}

String joinInt(int[] arr, String sep) {
  String[] ss = new String[arr.length];
  for (int i = 0; i < arr.length; i++) ss[i] = str(arr[i]);
  return join(ss, sep);
}