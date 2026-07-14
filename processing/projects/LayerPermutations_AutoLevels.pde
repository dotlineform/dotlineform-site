// LayerPermutations_AutoLevels.pde
// Build static composites for EVERY permutation of n images, with optional Auto Levels/Auto Contrast post-process.
// Place source images in "data/input". Outputs go to "output/".
//
// Changes vs previous version:
// - Added AUTO_LEVELS pass with percentile clipping (to approximate Photoshop "Auto Levels"/"Auto Contrast").
// - Added BLEND_STRATEGY: "SEQUENTIAL" (layer by layer) or "AVERAGE" (mean of all layers for low-opacity effect).
// - Added AUTO_LEVELS_PER_CHANNEL toggle (true ~ Auto Levels; false ~ Auto Contrast).
// - Added AUTO_CLIP_PERCENT to ignore extreme tails (e.g., 0.5%).
/*
USAGE
1) Put source images (PNG/JPG) into "data/input" in this sketch.
2) Run the sketch; composites are saved to "output/" next to the sketch folder.
*/

// ------------------------------------
// User Settings
// ------------------------------------
String INPUT_DIR   = "input";       // relative to /data
String OUTPUT_DIR  = "output";      // relative to sketch folder
int TARGET_W = -1;                  // -1 = use first image width
int TARGET_H = -1;                  // -1 = use first image height
float LAYER_OPACITY = 1.0;          // 0..1 opacity for each added layer (used in SEQUENTIAL)
boolean RESIZE_TO_FIRST = true;     // force all layers to size of first image
boolean CYCLE_MODES = true;         // cycle through modes list per layer
int MAX_PERMS = -1;                 // -1 = no cap; e.g. set 50 while testing

// Blending strategy: "SEQUENTIAL" (Photoshop-like stacking) or "AVERAGE" (equal-weight mean of all layers)
String BLEND_STRATEGY = "SEQUENTIAL";

// Auto Levels / Auto Contrast
boolean AUTO_LEVELS = true;             // apply auto normalization to the final composite
boolean AUTO_LEVELS_PER_CHANNEL = false; // false ~ Auto Contrast (preserve balance), true ~ Auto Levels (per channel)
float AUTO_CLIP_PERCENT = 0.5;          // percentage to clip from low & high ends (e.g., 0.5 -> 0.5%)

// Choose one or more modes to use (cycled or single) for SEQUENTIAL blend
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

void settings() { size(800, 800); }

void setup() {
  println("=== Layer Permutations + Auto Levels ===");
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
    PImage out;

    if (BLEND_STRATEGY.equals("AVERAGE")) {
      out = averageComposite(order);
    } else {
      out = sequentialComposite(order);
    }

    if (AUTO_LEVELS) {
      out = autoLevelsPercentile(out, AUTO_LEVELS_PER_CHANNEL, AUTO_CLIP_PERCENT);
    }

    // Build filename with order + modes + flags
    String ordStr = joinInt(order, "-");
    String modeStr = (BLEND_STRATEGY.equals("SEQUENTIAL")
      ? (CYCLE_MODES ? join(MODES, "-") : MODES[0])
      : "AVERAGE");
    String autoStr = AUTO_LEVELS ? (AUTO_LEVELS_PER_CHANNEL ? "AutoLevels" : "AutoContrast") + "_clip" + nf(AUTO_CLIP_PERCENT, 0, 2) : "None";
    String fname = String.format("perm_%s__blend_%s__auto_%s.png", ordStr, modeStr, autoStr);

    out.save(sketchPath(OUTPUT_DIR + "/" + fname));
    produced++;

    if (p % 25 == 0) println("Saved: " + fname);
  }

  println("✔ Done. Wrote " + produced + " composite(s) to: " + sketchPath(OUTPUT_DIR));
  exit();
}

// ------------------------------------
// Composite Strategies
// ------------------------------------

// Photoshop-like stacking with modes and per-layer opacity
PImage sequentialComposite(int[] order) {
  PImage out = images.get(order[0]).copy();
  for (int li = 1; li < order.length; li++) {
    PImage top = images.get(order[li]);
    String mode = CYCLE_MODES ? MODES[(li - 1) % MODES.length] : MODES[0];
    out = blendTwo(out, top, mode, LAYER_OPACITY);
  }
  return out;
}

// Equal-weight average of all layers (good for "low-opacity so all contribute")
PImage averageComposite(int[] order) {
  int w = images.get(0).width;
  int h = images.get(0).height;
  PImage out = createImage(w, h, RGB);
  out.loadPixels();

  int n = order.length;
  float invN = 1.0 / n;

  // Initialize accumulators
  float[] ar = new float[w * h];
  float[] ag = new float[w * h];
  float[] ab = new float[w * h];

  for (int oi = 0; oi < n; oi++) {
    PImage layer = images.get(order[oi]);
    layer.loadPixels();
    for (int i = 0; i < layer.pixels.length; i++) {
      int c = layer.pixels[i];
      ar[i] += red(c)   * invN;
      ag[i] += green(c) * invN;
      ab[i] += blue(c)  * invN;
    }
  }

  for (int i = 0; i < out.pixels.length; i++) {
    out.pixels[i] = color(constrain(ar[i], 0, 255), constrain(ag[i], 0, 255), constrain(ab[i], 0, 255));
  }
  out.updatePixels();
  return out;
}

// ------------------------------------
// Blending (SEQUENTIAL)
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
    float a = 255 * (ba + aTop - ba * aTop); // Porter-Duff "over"

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
// Auto Levels / Auto Contrast with percentile clipping
// ------------------------------------
PImage autoLevelsPercentile(PImage img, boolean perChannel, float clipPercent) {
  // clipPercent is percentage (0..100). Here we expect 0..100, but user passes e.g. 0.5 meaning 0.5%.
  // Guard:
  clipPercent = max(0, min(clipPercent, 20)); // limit to 0..20% for safety
  // Build histograms (0..255) either per channel or combined
  int[] histR = new int[256];
  int[] histG = new int[256];
  int[] histB = new int[256];
  int[] histAll = new int[256];

  img.loadPixels();
  int N = img.pixels.length;
  for (int i = 0; i < N; i++) {
    int c = img.pixels[i];
    int r = int(red(c));
    int g = int(green(c));
    int b = int(blue(c));
    histR[r]++; histG[g]++; histB[b]++;
    int y = int(0.2126*r + 0.7152*g + 0.0722*b); // luma-like
    histAll[y]++;
  }

  if (perChannel) {
    int[] lo = new int[3];
    int[] hi = new int[3];
    lo[0] = percentileLow(histR, N, clipPercent);
    hi[0] = percentileHigh(histR, N, clipPercent);
    lo[1] = percentileLow(histG, N, clipPercent);
    hi[1] = percentileHigh(histG, N, clipPercent);
    lo[2] = percentileLow(histB, N, clipPercent);
    hi[2] = percentileHigh(histB, N, clipPercent);
    return rescalePerChannel(img, lo, hi);
  } else {
    int lo = percentileLow(histAll, N, clipPercent);
    int hi = percentileHigh(histAll, N, clipPercent);
    return rescaleUnified(img, lo, hi);
  }
}

int percentileLow(int[] hist, int totalPixels, float clipPercent) {
  int clip = int(totalPixels * (clipPercent / 100.0));
  int cum = 0;
  for (int v = 0; v < 256; v++) {
    cum += hist[v];
    if (cum >= clip) return v;
  }
  return 0;
}

int percentileHigh(int[] hist, int totalPixels, float clipPercent) {
  int clip = int(totalPixels * (clipPercent / 100.0));
  int cum = 0;
  for (int v = 255; v >= 0; v--) {
    cum += hist[v];
    if (cum >= clip) return v;
  }
  return 255;
}

PImage rescalePerChannel(PImage img, int[] lo, int[] hi) {
  PImage out = createImage(img.width, img.height, RGB);
  img.loadPixels(); out.loadPixels();
  for (int i = 0; i < img.pixels.length; i++) {
    int c = img.pixels[i];
    float r = red(c), g = green(c), b = blue(c);
    r = mapClamp(r, lo[0], hi[0], 0, 255);
    g = mapClamp(g, lo[1], hi[1], 0, 255);
    b = mapClamp(b, lo[2], hi[2], 0, 255);
    out.pixels[i] = color(r, g, b);
  }
  out.updatePixels();
  return out;
}

PImage rescaleUnified(PImage img, int lo, int hi) {
  PImage out = createImage(img.width, img.height, RGB);
  img.loadPixels(); out.loadPixels();
  for (int i = 0; i < img.pixels.length; i++) {
    int c = img.pixels[i];
    float r = red(c), g = green(c), b = blue(c);
    r = mapClamp(r, lo, hi, 0, 255);
    g = mapClamp(g, lo, hi, 0, 255);
    b = mapClamp(b, lo, hi, 0, 255);
    out.pixels[i] = color(r, g, b);
  }
  out.updatePixels();
  return out;
}

float mapClamp(float v, float inMin, float inMax, float outMin, float outMax) {
  if (inMax <= inMin + 1e-6) return v; // avoid div by zero; leave as is
  float t = (v - inMin) / (inMax - inMin);
  t = constrain(t, 0, 1);
  return outMin + t * (outMax - outMin);
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

void swap(int[] a, int i, int j) { int tmp = a[i]; a[i] = a[j]; a[j] = tmp; }

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