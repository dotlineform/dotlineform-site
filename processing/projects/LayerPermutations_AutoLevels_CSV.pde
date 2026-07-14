// LayerPermutations_AutoLevels_CSV.pde
// Static composites for ALL permutations, with Auto Levels/Auto Contrast and CSV-driven per-layer rules.
//
// NEW:
// - CSV rules file: data/layer_rules.csv
//   Columns (header required): layer,mode,opacity,weight
//   * layer: 1-based layer position in the stack (1 = bottom/base, 2 = next, ..., n = top)
//   * mode:  Blend mode string (NORMAL, MULTIPLY, SCREEN, OVERLAY, LIGHTEN, DARKEN, DIFFERENCE, ADD, SUBTRACT, SOFTLIGHT)
//            Only used for BLEND_STRATEGY == "SEQUENTIAL". If blank, fallback to cycling/default.
//   * opacity: 0..1 opacity for that layer (SEQUENTIAL only). If blank, fallback to LAYER_OPACITY.
//   * weight:  Non-negative weight for AVERAGE strategy. If omitted/blank, defaults to 1.0. All weights are normalized.
//
// Place source images in "data/input". Place CSV in "data/layer_rules.csv". Outputs go to "output/".

String INPUT_DIR   = "input";       // relative to /data
String OUTPUT_DIR  = "output";      // relative to sketch folder
int TARGET_W = -1;                  // -1 = use first image width
int TARGET_H = -1;                  // -1 = use first image height
float LAYER_OPACITY = 1.0;          // default opacity for SEQUENTIAL (used if CSV has no value)
boolean RESIZE_TO_FIRST = true;     // force all layers to size of first image
boolean CYCLE_MODES = true;         // cycle through MODES list per layer if CSV is missing mode
int MAX_PERMS = -1;                 // -1 = no cap; e.g. set 50 while testing

// Blending strategy: "SEQUENTIAL" (Photoshop-like stacking) or "AVERAGE" (mean of all layers; CSV weights supported)
String BLEND_STRATEGY = "SEQUENTIAL";

// Auto Levels / Auto Contrast
boolean AUTO_LEVELS = true;              // apply normalization to final composite
boolean AUTO_LEVELS_PER_CHANNEL = false; // false ~ Auto Contrast; true ~ Auto Levels
float AUTO_CLIP_PERCENT = 0.5;           // percent to clip at low/high tails

// Default list for SEQUENTIAL if CSV leaves mode blank
String[] MODES = new String[]{ "MULTIPLY", "SCREEN", "OVERLAY", "LIGHTEN", "DARKEN" };

// ------------------------------------
// Runtime
// ------------------------------------
ArrayList<PImage> images = new ArrayList<PImage>();
ArrayList<String> names  = new ArrayList<String>();
ArrayList<int[]> perms   = new ArrayList<int[]>();
int produced = 0;

// CSV layer rules (1-based layer index -> rule)
class LayerRule {
  String mode;
  float opacity = Float.NaN; // NaN indicates "unset"
  float weight  = Float.NaN; // for AVERAGE strategy
}
HashMap<Integer, LayerRule> rules = new HashMap<Integer, LayerRule>();

void settings() { size(800, 800); }

void setup() {
  println("=== Layer Permutations + Auto Levels + CSV Rules ===");
  println("Source folder: data/" + INPUT_DIR);
  println("CSV: data/layer_rules.csv (optional)");
  println("Output folder: " + OUTPUT_DIR);

  // Load images
  File dir = new File(dataPath(INPUT_DIR));
  if (!dir.exists() || !dir.isDirectory()) {
    println("✖ Input folder not found: " + dir.getAbsolutePath());
    exit();
  }
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

  // Load CSV rules if present
  loadLayerRulesCSV();

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

    // Build filename with order + strategy
    String ordStr = joinInt(order, "-");
    String blendStr = BLEND_STRATEGY;
    String autoStr = AUTO_LEVELS ? (AUTO_LEVELS_PER_CHANNEL ? "AutoLevels" : "AutoContrast") + "_clip" + nf(AUTO_CLIP_PERCENT, 0, 2) : "None";
    String fname = String.format("perm_%s__blend_%s__auto_%s.png", ordStr, blendStr, autoStr);

    out.save(sketchPath(OUTPUT_DIR + "/" + fname));
    produced++;
    if (p % 25 == 0) println("Saved: " + fname);
  }

  println("✔ Done. Wrote " + produced + " composite(s) to: " + sketchPath(OUTPUT_DIR));
  exit();
}

// ------------------------------------
// CSV loading
// ------------------------------------
void loadLayerRulesCSV() {
  String csvPath = dataPath("layer_rules.csv");
  File f = new File(csvPath);
  if (!f.exists()) {
    println("CSV not found (optional): " + csvPath);
    return;
  }
  Table t = loadTable("layer_rules.csv", "header");
  if (t == null) {
    println("Failed to load CSV at data/layer_rules.csv");
    return;
  }
  println("Loaded CSV rules (" + t.getRowCount() + " rows).");
  for (TableRow row : t.rows()) {
    int layer = row.getInt("layer"); // 1-based
    if (layer <= 0) continue;
    LayerRule r = new LayerRule();
    String m = row.getString("mode");
    if (m != null) r.mode = m.trim().toUpperCase();
    if (row.getString("opacity") != null && row.getString("opacity").length() > 0) {
      r.opacity = row.getFloat("opacity");
    }
    if (row.getString("weight") != null && row.getString("weight").length() > 0) {
      r.weight = row.getFloat("weight");
    }
    rules.put(layer, r);
  }
}

// ------------------------------------
// Composite Strategies
// ------------------------------------

// Photoshop-like stacking with per-layer CSV rules
PImage sequentialComposite(int[] order) {
  // order length = n; layer positions are 1..n (1 is base)
  PImage out = images.get(order[0]).copy(); // layer 1: base

  for (int li = 1; li < order.length; li++) {
    int layerPos = li + 1; // 1-based position of current top
    PImage top = images.get(order[li]);

    // Determine mode & opacity from CSV or defaults
    String mode = null;
    float opacity = LAYER_OPACITY;
    if (rules.containsKey(layerPos)) {
      LayerRule r = rules.get(layerPos);
      if (r.mode != null && r.mode.length() > 0) mode = r.mode;
      if (!Float.isNaN(r.opacity)) opacity = r.opacity;
    }
    if (mode == null) {
      // fallback to cycle or first
      mode = CYCLE_MODES ? MODES[(li - 1) % MODES.length] : MODES[0];
    }
    out = blendTwo(out, top, mode, opacity);
  }
  return out;
}

// Weighted average (CSV weights) or equal-weight if none provided
PImage averageComposite(int[] order) {
  int w = images.get(0).width;
  int h = images.get(0).height;
  PImage out = createImage(w, h, RGB);
  out.loadPixels();

  int n = order.length;
  float[] weights = new float[n];
  boolean anyWeight = false;

  for (int li = 0; li < n; li++) {
    int layerPos = li + 1; // 1..n
    float wv = 1.0;
    if (rules.containsKey(layerPos) && !Float.isNaN(rules.get(layerPos).weight)) {
      wv = max(0, rules.get(layerPos).weight);
      anyWeight = true;
    }
    weights[li] = wv;
  }

  // Normalize weights to sum to 1
  float sumW = 0;
  for (float wv : weights) sumW += wv;
  if (sumW <= 0) {
    // fallback to equal
    for (int i = 0; i < n; i++) weights[i] = 1.0 / n;
  } else {
    for (int i = 0; i < n; i++) weights[i] /= sumW;
  }

  float[] ar = new float[w * h];
  float[] ag = new float[w * h];
  float[] ab = new float[w * h];

  for (int li = 0; li < n; li++) {
    PImage layer = images.get(order[li]);
    float wv = weights[li];
    layer.loadPixels();
    for (int i = 0; i < layer.pixels.length; i++) {
      int c = layer.pixels[i];
      ar[i] += red(c)   * wv;
      ag[i] += green(c) * wv;
      ab[i] += blue(c)  * wv;
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
    float a = 255 * (ba + aTop - ba * aTop);

    out.pixels[i] = color(constrain(r, 0, 255), constrain(g, 0, 255), constrain(b, 0, 255), constrain(a, 0, 255));
  }

  out.updatePixels();
  return out;
}

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
    r = b + t;
  } else if (mode.equals("SUBTRACT")) {
    r = b - t;
  } else if (mode.equals("SOFTLIGHT")) {
    float tN = t / 255.0;
    r = (1 - 2 * tN) * b * b / 255.0 + 2 * tN * b;
  } else {
    r = t; // NORMAL fallback
  }
  return constrain(r, 0, 255);
}

// ------------------------------------
// Auto Levels / Auto Contrast with percentile clipping
// ------------------------------------
PImage autoLevelsPercentile(PImage img, boolean perChannel, float clipPercent) {
  clipPercent = max(0, min(clipPercent, 20));
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
    int y = int(0.2126*r + 0.7152*g + 0.0722*b);
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
  if (inMax <= inMin + 1e-6) return v;
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

// Helpers
boolean endsWithAny(String s, String[] suffixes) { for (String suf : suffixes) if (s.endsWith(suf)) return true; return false; }
String joinInt(int[] arr, String sep) { String[] ss = new String[arr.length]; for (int i = 0; i < arr.length; i++) ss[i] = str(arr[i]); return join(ss, sep); }