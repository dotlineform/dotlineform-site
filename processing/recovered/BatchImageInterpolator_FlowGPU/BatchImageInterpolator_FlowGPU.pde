// BatchImageInterpolator_FlowGPU.pde
// Batch static-frame generator using dense optical-flow morph (Horn–Schunck) with per-pair flow caching,
// and GPU warping via a GLSL shader that reads a packed flow texture (RG channels).
// Prepared: 2025-09-02 15:57:37 (Europe/London)
// 
// HOW IT WORKS
// - Load adjacent pairs from SOURCE_DIR, prepare to fixed canvas via FIT/FILL/STRETCH.
// - For each pair, compute or load cached flow (float arrays u,v).
// - Build a flow texture (u->R, v->G, packed to 0..255 using a per-pair flowScale) and pass to shader.
// - Shader warps A and B using flow at time t, blends gamma-correct, writes frame (GPU-fast).
// - Frames saved as sequential PNGs; manifest + resume supported.
//
// QUICK CONFIG
String SOURCE_DIR   = "input";
String OUTPUT_DIR   = "out";
String FLOW_DIR     = "flows";     // per-pair cache (binary floats: u,v)
String EXTENSIONS   = "jpg,jpeg,png";
int    CANVAS_W     = 1920;
int    CANVAS_H     = 1080;
String FIT_MODE     = "FIT";       // FIT | FILL | STRETCH
color  BACKGROUND   = color(0);

int    INTER_FRAMES = 30;
int    HOLD_START   = 0;
int    HOLD_END     = 0;
String EASING       = "smoothstep"; // linear | smoothstep | easeInOutCubic
int    START_INDEX  = 0;
boolean OVERWRITE   = false;
boolean WRITE_MANIFEST = true;
boolean SHOW_PREVIEW   = true;

// FLOW (Horn–Schunck multi-scale)
int    LEVELS   = 3;
int    HS_ITERS = 80;
float  HS_ALPHA = 40.0;

// INTERNAL STATE
java.io.File[] files;
int pairIdx = 0;
int tIdx = -1;
long frameCounter;
PImage imgA0, imgB0;       // original loaded
PImage imgA, imgB;         // canvas-prepared
float[][] flowU, flowV;    // float fields (pixels)
PImage flowTex;            // packed RG texture
float flowScale;           // max |u| or |v| used for packing
PShader morph;             // GPU shader
java.io.PrintWriter manifest;

// -----------------------------------------------------------------------------

void settings() { size(CANVAS_W, CANVAS_H, P2D); }

void setup() {
  surface.setTitle("Batch Image Interpolator — GPU Flow Warper");
  hint(DISABLE_TEXTURE_MIPMAPS);
  frameRate(60);

  files = listImages(sketchPath(SOURCE_DIR), EXTENSIONS);
  if (files == null || files.length < 2) {
    println("[ERROR] Need at least two images in /" + SOURCE_DIR);
    exit();
  }
  ensureDir(sketchPath(OUTPUT_DIR));
  ensureDir(sketchPath(OUTPUT_DIR + "/" + FLOW_DIR));

  frameCounter = findResumeIndex(sketchPath(OUTPUT_DIR), START_INDEX, OVERWRITE);

  if (WRITE_MANIFEST) {
    manifest = createWriter(sketchPath(OUTPUT_DIR + "/manifest.csv"));
    manifest.println("pair_index,srcA,srcB,hold_start,inter_frames,hold_end,start_frame_idx,end_frame_idx,flow_file,flow_scale");
  }

  morph = loadShader("morph_flow.frag");
  morph.set("imgSize", (float)CANVAS_W, (float)CANVAS_H);

  loadPair(0);
  tIdx = -HOLD_START;
}

void draw() {
  if (pairIdx >= files.length - 1) {
    println("[DONE] All pairs processed.");
    if (manifest != null) { manifest.flush(); manifest.close(); }
    exit();
    return;
  }

  if (tIdx < 0) {
    renderAndSave(0.0);
    tIdx++;
    if (!SHOW_PREVIEW) return;
  } else if (tIdx <= INTER_FRAMES) {
    float t = ease((float)tIdx / max(1, INTER_FRAMES), EASING);
    renderAndSave(t);
    tIdx++;
    if (!SHOW_PREVIEW) return;
  } else if (tIdx <= INTER_FRAMES + HOLD_END) {
    renderAndSave(1.0);
    tIdx++;
    if (!SHOW_PREVIEW) return;
  } else {
    if (WRITE_MANIFEST) logManifestRow();
    pairIdx++;
    if (pairIdx >= files.length - 1) return;
    loadPair(pairIdx);
    tIdx = -HOLD_START;
  }
}

// -----------------------------------------------------------------------------
// Pair loading + flow caching + flow texture building
// -----------------------------------------------------------------------------

void loadPair(int idx) {
  // free previous
  imgA0 = null; imgB0 = null; imgA = null; imgB = null;
  flowU = null; flowV = null; flowTex = null;
  System.gc();

  imgA0 = loadImage(files[idx].getAbsolutePath());
  imgB0 = loadImage(files[idx+1].getAbsolutePath());
  if (imgA0 == null || imgB0 == null) {
    println("[ERROR] Failed to load images at pair " + idx);
    exit();
  }
  imgA = prepareToCanvas(imgA0, CANVAS_W, CANVAS_H, FIT_MODE, BACKGROUND);
  imgB = prepareToCanvas(imgB0, CANVAS_W, CANVAS_H, FIT_MODE, BACKGROUND);

  String flowPath = sketchPath(OUTPUT_DIR + "/" + FLOW_DIR + "/" + flowFileName(idx));
  float[][][] uv = null;
  if (new java.io.File(flowPath).exists()) {
    uv = loadFlow(flowPath);
    println("[FLOW] Loaded: " + flowPath);
  }
  if (uv == null) {
    // compute
    println("[FLOW] Computing Horn–Schunck flow for pair " + idx + " ...");
    float[][] u = null, v = null;
    PImage[] pyrA = buildPyr(imgA, LEVELS);
    PImage[] pyrB = buildPyr(imgB, LEVELS);
    for (int lvl = LEVELS - 1; lvl >= 0; lvl--) {
      int w = pyrA[lvl].width, h = pyrA[lvl].height;
      if (lvl < LEVELS - 1) {
        u = upscale(u, w, h);
        v = upscale(v, w, h);
      } else {
        u = zeros(w, h);
        v = zeros(w, h);
      }
      float[][] a = toGrayArray(pyrA[lvl]);
      float[][] b = toGrayArray(pyrB[lvl]);
      hornSchunck(a, b, u, v, HS_ALPHA, HS_ITERS);
    }
    flowU = u; flowV = v;
    saveFlow(flowU, flowV, flowPath);
  } else {
    flowU = uv[0]; flowV = uv[1];
  }

  // build flow texture + compute scale
  float[] scaleOut = new float[1];
  flowTex = buildFlowTexture(flowU, flowV, scaleOut);
  flowScale = max(scaleOut[0], 1e-6);
  println("[FLOW] flowScale (pixels): " + flowScale);

  if (WRITE_MANIFEST) {
    // ensure entry will include flowScale
  }
}

// -----------------------------------------------------------------------------
// Rendering (GPU shader)
// -----------------------------------------------------------------------------

void renderAndSave(float t) {
  morph.set("t", t);
  morph.set("imgSize", (float)CANVAS_W, (float)CANVAS_H);
  morph.set("flowScale", flowScale);
  morph.set("texA", imgA);
  morph.set("texB", imgB);
  morph.set("texFlow", flowTex);

  shader(morph);
  image(imgA, 0, 0, width, height); // draw one quad
  resetShader();

  String outName = String.format("frame_%06d.png", frameCounter);
  String outPath = sketchPath(OUTPUT_DIR + "/" + outName);
  if (OVERWRITE || !(new java.io.File(outPath).exists())) {
    save(outPath);
  }
  if (SHOW_PREVIEW) {
    fill(255);
    text(String.format("pair %d/%d  t=%.3f  -> %s", pairIdx+1, files.length-1, t, outName), 12, 20);
  }
  frameCounter++;
}

void logManifestRow() {
  if (manifest == null) return;
  int startIdx = (int)(frameCounter) - (HOLD_START + INTER_FRAMES + 1 + HOLD_END);
  int endIdx   = (int)(frameCounter) - 1;
  manifest.println(String.format("%d,%s,%s,%d,%d,%d,%d,%d,%s,%.6f",
    pairIdx,
    files[pairIdx].getName(),
    files[pairIdx+1].getName(),
    HOLD_START, INTER_FRAMES, HOLD_END,
    startIdx, endIdx,
    flowFileName(pairIdx),
    flowScale
  ));
}

// -----------------------------------------------------------------------------
// Helpers: listing, resume, dirs
// -----------------------------------------------------------------------------

java.io.File[] listImages(String dirPath, String extsCSV) {
  java.io.File dir = new java.io.File(dirPath);
  if (!dir.exists()) return null;
  final String[] exts = split(extsCSV.toLowerCase(), ',');
  java.io.File[] arr = dir.listFiles(new java.io.FilenameFilter() {
    public boolean accept(java.io.File d, String name) {
      String n = name.toLowerCase();
      for (String e : exts) if (n.endsWith("." + e.trim())) return true;
      return false;
    }
  });
  if (arr == null) return null;
  java.util.Arrays.sort(arr, new java.util.Comparator<java.io.File>() {
    public int compare(java.io.File a, java.io.File b) { return a.getName().compareTo(b.getName()); }
  });
  return arr;
}

void ensureDir(String path) {
  java.io.File d = new java.io.File(path);
  if (!d.exists()) d.mkdirs();
}

long findResumeIndex(String outDir, int startAt, boolean overwrite) {
  if (overwrite) return startAt;
  long maxIdx = startAt - 1;
  java.io.File d = new java.io.File(outDir);
  java.io.File[] arr = d.listFiles();
  if (arr != null) {
    for (java.io.File f : arr) {
      String n = f.getName();
      if (n.startsWith("frame_") && n.endsWith(".png") && n.length() == 15) {
        try {
          long idx = Long.parseLong(n.substring(6, 12));
          if (idx > maxIdx) maxIdx = idx;
        } catch (Exception ignore) {}
      }
    }
  }
  return maxIdx + 1;
}

// -----------------------------------------------------------------------------
// Image prep (fit/fill/stretch to canvas)
// -----------------------------------------------------------------------------

PImage prepareToCanvas(PImage src, int cw, int ch, String mode, int bg) {
  PGraphics g = createGraphics(cw, ch, P2D);
  g.beginDraw();
  g.background(bg);
  g.imageMode(CORNER);
  float[] r = computeDestRect(cw, ch, src.width, src.height, mode);
  g.image(src, r[0], r[1], r[2], r[3]);
  g.endDraw();
  return g.get();
}

float[] computeDestRect(int cw, int ch, int iw, int ih, String mode) {
  if ("STRETCH".equals(mode)) return new float[]{0,0,cw,ch};
  float canvasAR = (float)cw/ch;
  float imgAR = (float)iw/ih;
  float x=0,y=0,w=cw,h=ch;

  if ("FILL".equals(mode)) {
    if (imgAR > canvasAR) { h = ch; w = h*imgAR; x = (cw - w)/2; }
    else { w = cw; h = w/imgAR; y = (ch - h)/2; }
  } else { // FIT
    if (imgAR > canvasAR) { w = cw; h = w/imgAR; y = (ch - h)/2; }
    else { h = ch; w = h*imgAR; x = (cw - w)/2; }
  }
  return new float[]{x,y,w,h};
}

// -----------------------------------------------------------------------------
// Flow cache I/O (binary) + building packed flow texture
// -----------------------------------------------------------------------------

String flowFileName(int idx) {
  return String.format("flow_%06d.bin", idx);
}

void saveFlow(float[][] u, float[][] v, String path) {
  try {
    java.io.DataOutputStream out = new java.io.DataOutputStream(new java.io.BufferedOutputStream(new java.io.FileOutputStream(path)));
    int h = u.length, w = u[0].length;
    out.writeInt(w); out.writeInt(h);
    for (int y=0; y<h; y++) for (int x=0; x<w; x++) out.writeFloat(u[y][x]);
    for (int y=0; y<h; y++) for (int x=0; x<w; x++) out.writeFloat(v[y][x]);
    out.flush(); out.close();
  } catch (Exception e) {
    println("[WARN] Failed to save flow: " + e);
  }
}

float[][][] loadFlow(String path) {
  try {
    java.io.DataInputStream in = new java.io.DataInputStream(new java.io.BufferedInputStream(new java.io.FileInputStream(path)));
    int w = in.readInt(); int h = in.readInt();
    float[][] u = new float[h][w];
    float[][] v = new float[h][w];
    for (int y=0; y<h; y++) for (int x=0; x<w; x++) u[y][x] = in.readFloat();
    for (int y=0; y<h; y++) for (int x=0; x<w; x++) v[y][x] = in.readFloat();
    in.close();
    return new float[][][]{u,v};
  } catch (Exception e) {
    println("[WARN] Failed to load flow, recomputing. " + e);
    return null;
  }
}

PImage buildFlowTexture(float[][] u, float[][] v, float[] scaleOut) {
  int h = u.length, w = u[0].length;
  float maxmag = 1e-6;
  for (int y=0; y<h; y++) for (int x=0; x<w; x++) {
    float uu = abs(u[y][x]);
    float vv = abs(v[y][x]);
    if (uu > maxmag) maxmag = uu;
    if (vv > maxmag) maxmag = vv;
  }
  scaleOut[0] = maxmag;
  PImage tex = createImage(w, h, ARGB);
  tex.loadPixels();
  for (int y=0; y<h; y++) {
    int row = y*w;
    for (int x=0; x<w; x++) {
      float uu = u[y][x] / maxmag; // [-1,1]
      float vv = v[y][x] / maxmag; // [-1,1]
      int R = int(constrain((uu*0.5 + 0.5)*255.0, 0, 255));
      int G = int(constrain((vv*0.5 + 0.5)*255.0, 0, 255));
      int A = 255;
      tex.pixels[row + x] = (A<<24) | (R<<16) | (G<<8) | 0; // B=0, store only RG
    }
  }
  tex.updatePixels();
  return tex;
}

// -----------------------------------------------------------------------------
// Horn–Schunck core + gradient utilities (CPU) — same as non-GPU variant
// -----------------------------------------------------------------------------

PImage[] buildPyr(PImage img, int levels) {
  levels = max(1, levels);
  PImage[] pyr = new PImage[levels];
  pyr[0] = img.get();
  for (int i=1; i<levels; i++) {
    PImage prev = pyr[i-1];
    PImage g = prev.copy();
    g.filter(BLUR, 1);
    PImage d = createImage(max(1, prev.width/2), max(1, prev.height/2), ARGB);
    g.resize(d.width, d.height);
    d.copy(g, 0, 0, g.width, g.height, 0, 0, d.width, d.height);
    pyr[i] = d;
  }
  return pyr;
}

float[][] zeros(int w, int h) {
  float[][] z = new float[h][w];
  return z;
}

float[][] toGrayArray(PImage p) {
  p.loadPixels();
  float[][] g = new float[p.height][p.width];
  for (int y=0; y<p.height; y++) {
    int row = y * p.width;
    for (int x=0; x<p.width; x++) {
      int c = p.pixels[row + x];
      float r = red(c)/255.0, gg = green(c)/255.0, b = blue(c)/255.0;
      g[y][x] = 0.2126*r + 0.7152*gg + 0.0722*b; // sRGB luma
    }
  }
  return g;
}

float[][] upscale(float[][] a, int newW, int newH) {
  float[][] out = new float[newH][newW];
  int h = a.length, w = a[0].length;
  for (int y=0; y<newH; y++) {
    float fy = (y * (h-1.0)) / max(1, newH-1.0);
    int y0 = floor(fy), y1 = min(y0+1, h-1); float wy = fy - y0;
    for (int x=0; x<newW; x++) {
      float fx = (x * (w-1.0)) / max(1, newW-1.0);
      int x0 = floor(fx), x1 = min(x0+1, w-1); float wx = fx - x0;
      float v00 = a[y0][x0], v01 = a[y0][x1], v10 = a[y1][x0], v11 = a[y1][x1];
      out[y][x] = mix(mix(v00, v01, wx), mix(v10, v11, wx), wy);
    }
  }
  return out;
}

float mix(float a, float b, float t) { return a + (b - a) * t; }

void hornSchunck(float[][] A, float[][] B, float[][] u, float[][] v, float alpha, int iters) {
  int h = A.length, w = A[0].length;
  float[][] Ix = sobelX(A);
  float[][] Iy = sobelY(A);
  float[][] It = new float[h][w];
  for (int y=0; y<h; y++) for (int x=0; x<w; x++) It[y][x] = B[y][x] - A[y][x];

  float a2 = alpha*alpha;
  float[][] uAvg = new float[h][w];
  float[][] vAvg = new float[h][w];

  for (int k=0; k<iters; k++) {
    boxAverage(u, uAvg);
    boxAverage(v, vAvg);
    for (int y=1; y<h-1; y++) {
      for (int x=1; x<w-1; x++) {
        float ix = Ix[y][x], iy = Iy[y][x], it = It[y][x];
        float denom = a2 + ix*ix + iy*iy;
        float P = ix*uAvg[y][x] + iy*vAvg[y][x] + it;
        u[y][x] = uAvg[y][x] - (ix * P) / max(1e-6, denom);
        v[y][x] = vAvg[y][x] - (iy * P) / max(1e-6, denom);
      }
    }
  }
}

void boxAverage(float[][] src, float[][] dst) {
  int h = src.length, w = src[0].length;
  for (int y=1; y<h-1; y++) {
    for (int x=1; x<w-1; x++) {
      float s = 0;
      for (int j=-1; j<=1; j++)
        for (int i=-1; i<=1; i++)
          s += src[y+j][x+i];
      dst[y][x] = s / 9.0;
    }
  }
  // edges
  for (int x=0; x<w; x++) { dst[0][x] = src[0][x]; dst[h-1][x] = src[h-1][x]; }
  for (int y=0; y<h; y++) { dst[y][0] = src[y][0]; dst[y][w-1] = src[y][w-1]; }
}

float[][] sobelX(float[][] a) {
  int h = a.length, w = a[0].length;
  float[][] g = new float[h][w];
  int[] kx = {-1,0,1,-2,0,2,-1,0,1};
  for (int y=1; y<h-1; y++) for (int x=1; x<w-1; x++) {
    float s=0; int t=0;
    for (int j=-1; j<=1; j++) for (int i=-1; i<=1; i++,t++) s += a[y+j][x+i]*kx[t];
    g[y][x]=s/8.0;
  }
  return g;
}

float[][] sobelY(float[][] a) {
  int h = a.length, w = a[0].length;
  float[][] g = new float[h][w];
  int[] ky = {-1,-2,-1,0,0,0,1,2,1};
  for (int y=1; y<h-1; y++) for (int x=1; x<w-1; x++) {
    float s=0; int t=0;
    for (int j=-1; j<=1; j++) for (int i=-1; i<=1; i++,t++) s += a[y+j][x+i]*ky[t];
    g[y][x]=s/8.0;
  }
  return g;
}
