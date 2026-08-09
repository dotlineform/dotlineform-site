// StaticBatchGenerator.pde
// Pure batch image generator — no animation loop. Everything runs inside setup() and exits.
// Modes: CROSSFADE (gamma shader), FLOW_CPU (Horn–Schunck), FLOW_GPU (GPU warper).
// Prepared: 2025-09-02 17:43:52 (Europe/London)

// ------------- CONFIG -------------
String SOURCE_DIR   = "input";   // ordered images go here
String OUTPUT_DIR   = "out";
String FLOW_DIR     = "flows";   // per-pair flow cache (for FLOW_CPU/FLOW_GPU)
String EXTENSIONS   = "jpg,jpeg,png";

int    CANVAS_W     = 1920;
int    CANVAS_H     = 1080;
String FIT_MODE     = "FIT";     // FIT | FILL | STRETCH
color  BACKGROUND   = color(0);

String MODE         = "FLOW_CPU"; // CROSSFADE | FLOW_CPU | FLOW_GPU
int    INTER_FRAMES = 30;
int    HOLD_START   = 0;
int    HOLD_END     = 0;
String EASING       = "smoothstep"; // linear | smoothstep | easeInOutCubic
int    START_INDEX  = 0;
boolean OVERWRITE   = false;
boolean WRITE_MANIFEST = true;

// HS params (FLOW_*)
int    LEVELS   = 3;
int    HS_ITERS = 80;
float  HS_ALPHA = 40.0;

// blending
boolean GAMMA_CORRECT = true;
boolean PREMULTIPLIED = true;

// ------------- INTERNAL -------------
java.io.File[] files;
long frameCounter;
java.io.PrintWriter manifest;

// GPU resources (for CROSSFADE and FLOW_GPU)
PShader shCross;
PShader shFlow;
PImage flowTex;
float flowScale;

void settings(){ size(CANVAS_W, CANVAS_H, P2D); }

void setup(){
  surface.setTitle("Static Batch Generator (" + MODE + ")");

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
    String header = "pair_index,srcA,srcB,hold_start,inter_frames,hold_end,start_frame_idx,end_frame_idx,mode,extra";
    manifest.println(header);
  }

  if ("CROSSFADE".equals(MODE)) {
    shCross = loadShader("crossfade.frag");
  } else if ("FLOW_GPU".equals(MODE)) {
    shFlow = loadShader("morph_flow.frag");
    shFlow.set("imgSize", (float)CANVAS_W, (float)CANVAS_H);
    hint(DISABLE_TEXTURE_MIPMAPS);
  }

  // --- process all pairs inside setup ---
  for (int pairIdx = 0; pairIdx < files.length - 1; pairIdx++) {
    println("\n[PAIR] " + (pairIdx+1) + "/" + (files.length-1) + "  " + files[pairIdx].getName() + " -> " + files[pairIdx+1].getName());

    // load and prep
    PImage srcA = loadImage(files[pairIdx].getAbsolutePath());
    PImage srcB = loadImage(files[pairIdx+1].getAbsolutePath());
    if (srcA == null || srcB == null) { println("[ERROR] load fail"); exit(); }
    PImage A = prepareToCanvas(srcA, CANVAS_W, CANVAS_H, FIT_MODE, BACKGROUND);
    PImage B = prepareToCanvas(srcB, CANVAS_W, CANVAS_H, FIT_MODE, BACKGROUND);

    float[][] u = null, v = null;
    String extra = "";

    if ("CROSSFADE".equals(MODE)) {
      // nothing extra
    } else {
      // FLOW modes: load or compute flow
      String flowPath = sketchPath(OUTPUT_DIR + "/" + FLOW_DIR + "/" + flowFileName(pairIdx));
      float[][][] uv = null;
      if (new java.io.File(flowPath).exists()) {
        uv = loadFlow(flowPath);
        if (uv != null) { u = uv[0]; v = uv[1]; println("[FLOW] Loaded " + flowPath); }
      }
      if (uv == null) {
        println("[FLOW] Computing HS flow ...");
        PImage[] pyrA = buildPyr(A, LEVELS);
        PImage[] pyrB = buildPyr(B, LEVELS);
        for (int lvl = LEVELS - 1; lvl >= 0; lvl--) {
          int w = pyrA[lvl].width, h = pyrA[lvl].height;
          if (lvl < LEVELS - 1) { u = upscale(u, w, h); v = upscale(v, w, h); }
          else { u = zeros(w, h); v = zeros(w, h); }
          float[][] a = toGrayArray(pyrA[lvl]);
          float[][] b = toGrayArray(pyrB[lvl]);
          hornSchunck(a, b, u, v, HS_ALPHA, HS_ITERS);
        }
        saveFlow(u, v, flowPath);
        println("[FLOW] Saved " + flowPath);
      }
      if ("FLOW_GPU".equals(MODE)) {
        float[] scaleOut = new float[1];
        flowTex = buildFlowTexture(u, v, scaleOut);
        flowScale = max(scaleOut[0], 1e-6);
        extra = "flowScale=" + nf(flowScale,1,4);
      }
    }

    // HOLD_START
    for (int h=0; h<HOLD_START; h++) {
      writeFrame(A, B, u, v, 0.0);
    }

    // INTERPOLATED FRAMES
    for (int i=0; i<=INTER_FRAMES; i++) {
      float t = ease(i / max(1.0, (float)INTER_FRAMES), EASING);
      writeFrame(A, B, u, v, t);
    }

    // HOLD_END
    for (int h=0; h<HOLD_END; h++) {
      writeFrame(A, B, u, v, 1.0);
    }

    // manifest
    if (WRITE_MANIFEST) {
      int startIdx = (int)(frameCounter) - (HOLD_START + INTER_FRAMES + 1 + HOLD_END);
      int endIdx   = (int)(frameCounter) - 1;
      String modeInfo = MODE + (extra.length()>0 ? " " + extra : "");
      manifest.println(String.format("%d,%s,%s,%d,%d,%d,%d,%d,%s,%s",
        pairIdx, files[pairIdx].getName(), files[pairIdx+1].getName(),
        HOLD_START, INTER_FRAMES, HOLD_END, startIdx, endIdx, MODE, extra));
    }
  }

  if (manifest != null) { manifest.flush(); manifest.close(); }
  println("\n[DONE] Static batch generation completed.");
  exit();
}

// ------------- write one frame (no draw loop) -------------
void writeFrame(PImage A, PImage B, float[][] u, float[][] v, float t){
  String outName = String.format("frame_%06d.png", frameCounter);
  String outPath = sketchPath(OUTPUT_DIR + "/" + outName);
  if (!OVERWRITE && (new java.io.File(outPath).exists())) { frameCounter++; return; }

  if ("CROSSFADE".equals(MODE)) {
    PGraphics g = createGraphics(CANVAS_W, CANVAS_H, P2D);
    g.beginDraw();
    shCross.set("t", t);
    shCross.set("texA", A);
    shCross.set("texB", B);
    g.shader(shCross);
    g.image(A, 0, 0, CANVAS_W, CANVAS_H);
    g.resetShader();
    g.endDraw();
    g.save(outPath);
  } else if ("FLOW_CPU".equals(MODE)) {
    PImage frame = morphFrame(A, B, u, v, t, GAMMA_CORRECT, PREMULTIPLIED);
    frame.save(outPath);
  } else if ("FLOW_GPU".equals(MODE)) {
    PGraphics g = createGraphics(CANVAS_W, CANVAS_H, P2D);
    g.beginDraw();
    shFlow.set("t", t);
    shFlow.set("imgSize", (float)CANVAS_W, (float)CANVAS_H);
    shFlow.set("flowScale", flowScale);
    shFlow.set("texA", A);
    shFlow.set("texB", B);
    shFlow.set("texFlow", flowTex);
    g.shader(shFlow);
    g.image(A, 0, 0, CANVAS_W, CANVAS_H);
    g.resetShader();
    g.endDraw();
    g.save(outPath);
  }
  frameCounter++;
}

// ------------- helpers (dirs, listing, resume) -------------
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
  if (arr != null) for (java.io.File f : arr) {
    String n = f.getName();
    if (n.startsWith("frame_") && n.endsWith(".png") && n.length() == 15) {
      try { long idx = Long.parseLong(n.substring(6, 12)); if (idx > maxIdx) maxIdx = idx; } catch (Exception e) {}
    }
  }
  return maxIdx + 1;
}

// ------------- image prep -------------
PImage prepareToCanvas(PImage src, int cw, int ch, String mode, int bg) {
  PGraphics g = createGraphics(cw, ch, P2D);
  g.beginDraw();
  g.background(bg);
  float[] r = computeDestRect(cw, ch, src.width, src.height, mode);
  g.image(src, r[0], r[1], r[2], r[3]);
  g.endDraw();
  return g.get();
}

float[] computeDestRect(int cw, int ch, int iw, int ih, String mode) {
  if ("STRETCH".equals(mode)) return new float[]{0,0,cw,ch};
  float canvasAR = (float)cw/ch; float imgAR = (float)iw/ih;
  float x=0,y=0,w=cw,h=ch;
  if ("FILL".equals(mode)) {
    if (imgAR > canvasAR) { h = ch; w = h*imgAR; x = (cw - w)/2; }
    else { w = cw; h = w/imgAR; y = (ch - h)/2; }
  } else {
    if (imgAR > canvasAR) { w = cw; h = w/imgAR; y = (ch - h)/2; }
    else { h = ch; w = h*imgAR; x = (cw - w)/2; }
  }
  return new float[]{x,y,w,h};
}

// ------------- FLOW cache I/O + flow texture packing -------------
String flowFileName(int idx) { return String.format("flow_%06d.bin", idx); }

void saveFlow(float[][] u, float[][] v, String path) {
  try {
    java.io.DataOutputStream out = new java.io.DataOutputStream(new java.io.BufferedOutputStream(new java.io.FileOutputStream(path)));
    int h = u.length, w = u[0].length;
    out.writeInt(w); out.writeInt(h);
    for (int y=0; y<h; y++) for (int x=0; x<w; x++) out.writeFloat(u[y][x]);
    for (int y=0; y<h; y++) for (int x=0; x<w; x++) out.writeFloat(v[y][x]);
    out.flush(); out.close();
  } catch (Exception e) { println("[WARN] saveFlow: " + e); }
}

float[][][] loadFlow(String path) {
  try {
    java.io.DataInputStream in = new java.io.DataInputStream(new java.io.BufferedInputStream(new java.io.FileInputStream(path)));
    int w = in.readInt(); int h = in.readInt();
    float[][] u = new float[h][w]; float[][] v = new float[h][w];
    for (int y=0; y<h; y++) for (int x=0; x<w; x++) u[y][x] = in.readFloat();
    for (int y=0; y<h; y++) for (int x=0; x<w; x++) v[y][x] = in.readFloat();
    in.close(); return new float[][][]{u,v};
  } catch (Exception e) { println("[WARN] loadFlow: " + e); return null; }
}

PImage buildFlowTexture(float[][] u, float[][] v, float[] scaleOut) {
  int h = u.length, w = u[0].length;
  float maxmag = 1e-6;
  for (int y=0; y<h; y++) for (int x=0; x<w; x++) {
    float uu = abs(u[y][x]); float vv = abs(v[y][x]);
    if (uu>maxmag) maxmag = uu; if (vv>maxmag) maxmag = vv;
  }
  scaleOut[0] = maxmag;
  PImage tex = createImage(w, h, ARGB);
  tex.loadPixels();
  for (int y=0; y<h; y++) {
    int row = y*w;
    for (int x=0; x<w; x++) {
      float uu = u[y][x] / maxmag; float vv = v[y][x] / maxmag; // [-1,1]
      int R = int(constrain((uu*0.5 + 0.5)*255.0, 0, 255));
      int G = int(constrain((vv*0.5 + 0.5)*255.0, 0, 255));
      int A = 255;
      tex.pixels[row + x] = (A<<24) | (R<<16) | (G<<8) | 0;
    }
  }
  tex.updatePixels();
  return tex;
}

// ------------- Horn–Schunck + utils -------------
PImage[] buildPyr(PImage img, int levels) {
  levels = max(1, levels);
  PImage[] pyr = new PImage[levels];
  pyr[0] = img.get();
  for (int i=1; i<levels; i++) {
    PImage prev = pyr[i-1];
    PImage g = prev.copy(); g.filter(BLUR, 1);
    PImage d = createImage(max(1, prev.width/2), max(1, prev.height/2), ARGB);
    g.resize(d.width, d.height);
    d.copy(g, 0, 0, g.width, g.height, 0, 0, d.width, d.height);
    pyr[i] = d;
  }
  return pyr;
}

float[][] zeros(int w, int h) { return new float[h][w]; }

float[][] toGrayArray(PImage p) {
  p.loadPixels();
  float[][] g = new float[p.height][p.width];
  for (int y=0; y<p.height; y++) {
    int row = y * p.width;
    for (int x=0; x<p.width; x++) {
      int c = p.pixels[row + x];
      float r = red(c)/255.0, gg = green(c)/255.0, b = blue(c)/255.0;
      g[y][x] = 0.2126*r + 0.7152*gg + 0.0722*b;
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
    for (int y=1; y<h-1; y++) for (int x=1; x<w-1; x++) {
      float ix = Ix[y][x], iy = Iy[y][x], it = It[y][x];
      float denom = a2 + ix*ix + iy*iy;
      float P = ix*uAvg[y][x] + iy*vAvg[y][x] + it;
      u[y][x] = uAvg[y][x] - (ix * P) / max(1e-6, denom);
      v[y][x] = vAvg[y][x] - (iy * P) / max(1e-6, denom);
    }
  }
}

void boxAverage(float[][] src, float[][] dst) {
  int h = src.length, w = src[0].length;
  for (int y=1; y<h-1; y++) for (int x=1; x<w-1; x++) {
    float s = 0;
    for (int j=-1; j<=1; j++) for (int i=-1; i<=1; i++) s += src[y+j][x+i];
    dst[y][x] = s / 9.0;
  }
  for (int x=0; x<w; x++) { dst[0][x] = src[0][x]; dst[h-1][x] = src[h-1][x]; }
  for (int y=0; y<h; y++) { dst[y][0] = src[y][0]; dst[y][w-1] = src[y][w-1]; }
}

float[][] sobelX(float[][] a) {
  int h = a.length, w = a[0].length;
  float[][] g = new float[h][w];
  int[] kx = new int[]{-1,0,1,-2,0,2,-1,0,1};
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
  int[] ky = new int[]{-1,-2,-1,0,0,0,1,2,1};
  for (int y=1; y<h-1; y++) for (int x=1; x<w-1; x++) {
    float s=0; int t=0;
    for (int j=-1; j<=1; j++) for (int i=-1; i<=1; i++,t++) s += a[y+j][x+i]*ky[t];
    g[y][x]=s/8.0;
  }
  return g;
}

// ------------- Warping & blending (CPU) -------------
PImage morphFrame(PImage A, PImage B, float[][] u, float[][] v, float t,
                  boolean gammaCorrect, boolean premult) {
  int w = A.width, h = A.height;
  PImage out = createImage(w, h, ARGB);
  A.loadPixels(); B.loadPixels(); out.loadPixels();
  for (int y=0; y<h; y++) for (int x=0; x<w; x++) {
    float uf = u[y][x], vf = v[y][x];
    float ax = x - t*uf, ay = y - t*vf;
    float bx = x + (1.0 - t)*uf, by = y + (1.0 - t)*vf;
    int ca = bilinear(A, ax, ay);
    int cb = bilinear(B, bx, by);
    float Aa = alpha(ca)/255.0, Ar = red(ca)/255.0, Ag = green(ca)/255.0, Ab = blue(ca)/255.0;
    float Ba = alpha(cb)/255.0, Br = red(cb)/255.0, Bg = green(cb)/255.0, Bb = blue(cb)/255.0;
    if (gammaCorrect) { Ar=pow(Ar,2.2); Ag=pow(Ag,2.2); Ab=pow(Ab,2.2);
                        Br=pow(Br,2.2); Bg=pow(Bg,2.2); Bb=pow(Bb,2.2); }
    if (premult) { Ar*=Aa; Ag*=Aa; Ab*=Aa; Br*=Ba; Bg*=Ba; Bb*=Ba; }
    float wB=t, wA=1.0-wB;
    float R=wA*Ar+wB*Br, G=wA*Ag+wB*Bg, Bl=wA*Ab+wB*Bb, Aout=wA*Aa+wB*Ba;
    if (premult && Aout>1e-6){ R/=Aout; G/=Aout; Bl/=Aout; }
    if (gammaCorrect){ R=pow(max(0,R),1.0/2.2); G=pow(max(0,G),1.0/2.2); Bl=pow(max(0,Bl),1.0/2.2); }
    out.pixels[y*w+x] = color(constrain(R*255,0,255),constrain(G*255,0,255),constrain(Bl*255,0,255),constrain(Aout*255,0,255));
  }
  out.updatePixels(); return out;
}

int bilinear(PImage img, float fx, float fy) {
  int w = img.width, h = img.height;
  if (fx < 0) fx = 0; if (fy < 0) fy = 0;
  if (fx > w-1) fx = w-1; if (fy > h-1) fy = h-1;
  int x0 = floor(fx), y0 = floor(fy);
  int x1 = min(x0+1, w-1), y1 = min(y0+1, h-1);
  float tx = fx - x0, ty = fy - y0;
  int c00 = img.pixels[y0*w + x0], c01 = img.pixels[y0*w + x1];
  int c10 = img.pixels[y1*w + x0], c11 = img.pixels[y1*w + x1];
  float a00=alpha(c00), r00=red(c00), g00=green(c00), b00=blue(c00);
  float a01=alpha(c01), r01=red(c01), g01=green(c01), b01=blue(c01);
  float a10=alpha(c10), r10=red(c10), g10=green(c10), b10=blue(c10);
  float a11=alpha(c11), r11=red(c11), g11=green(c11), b11=blue(c11);
  float a0=mix(a00,a01,tx), a1=mix(a10,a11,tx);
  float r0=mix(r00,r01,tx), r1=mix(r10,r11,tx);
  float g0=mix(g00,g01,tx), g1=mix(g10,g11,tx);
  float b0=mix(b00,b01,tx), b1=mix(b10,b11,tx);
  return color(mix(r0,r1,ty), mix(g0,g1,ty), mix(b0,b1,ty), mix(a0,a1,ty));
}

// ------------- math -------------
float ease(float t, String mode){
  t = constrain(t,0,1);
  if ("linear".equals(mode)) return t;
  if ("smoothstep".equals(mode)) return t*t*(3.0 - 2.0*t);
  if ("easeInOutCubic".equals(mode)) return t < 0.5 ? 4*t*t*t : 1 - pow(-2*t + 2, 3)/2.0;
  return t;
}
