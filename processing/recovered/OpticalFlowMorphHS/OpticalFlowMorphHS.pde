// OpticalFlowMorphHS.pde
// Dense optical-flow morph (Horn–Schunck) implemented in pure Processing (Java).
// Designed for offline static frame generation (not real-time).
//
// HOW TO USE
// - Place A.jpg and B.jpg in the "data/" folder of the sketch.
// - Set W,H to your desired working resolution (start smaller to test).
// - Run to generate intermediate frames in "out/".
//
// TIP: Integrate morphFrame(...) into your BatchImageInterpolator to replace crossfade.
//
// Prepared: 2025-09-02 15:44:35 (Europe/London)
// Model: GPT-5 Thinking

PImage imgA, imgB;
int W = 1280, H = 720;      // working resolution (adjust for your project)
int LEVELS = 3;             // pyramid levels (coarsest to finest)
int HS_ITERS = 80;          // iterations per level
float HS_ALPHA = 40.0;      // smoothness (bigger = smoother flow)

void settings() { size(W, H, P2D); }
void setup() {
  surface.setTitle("Optical-Flow Morph (Horn–Schunck) — Pure Processing");
  imgA = loadImage("A.jpg");
  imgB = loadImage("B.jpg");
  if (imgA == null || imgB == null) {
    println("[ERROR] Put A.jpg and B.jpg in the data/ folder.");
    exit();
  }
  imgA.resize(W, H);
  imgB.resize(W, H);

  // Build Gaussian pyramids
  PImage[] pyrA = buildPyr(imgA, LEVELS);
  PImage[] pyrB = buildPyr(imgB, LEVELS);

  // Compute dense flow u,v from A->B (start at coarsest)
  float[][] u = null, v = null;
  for (int lvl = LEVELS-1; lvl >= 0; lvl--) {
    int w = pyrA[lvl].width, h = pyrA[lvl].height;

    // Upscale flow to current level (skip for coarsest)
    if (lvl < LEVELS-1) {
      u = upscale(u, w, h);
      v = upscale(v, w, h);
    } else {
      u = zeros(w, h);
      v = zeros(w, h);
    }

    // Convert images to grayscale float arrays
    float[][] a = toGrayArray(pyrA[lvl]);
    float[][] b = toGrayArray(pyrB[lvl]);

    // Horn–Schunck refinement at this scale
    hornSchunck(a, b, u, v, HS_ALPHA, HS_ITERS);
  }

  // Generate in-betweens
  ensureDir(sketchPath("out"));
  for (int i = 0; i <= 30; i++) { // 31 frames including endpoints
    float t = i/30.0;
    PImage frame = morphFrame(imgA, imgB, u, v, t, true /*gammaCorrect*/, true /*premult*/);
    image(frame, 0, 0);
    saveFrame("out/morph####.png");
  }
  println("[DONE] Frames written to out/");
  exit();
}

// =================== Utility: pyramids, arrays, filtering ===================

PImage[] buildPyr(PImage img, int levels) {
  PImage[] pyr = new PImage[levels];
  pyr[0] = img.get();
  for (int i=1; i<levels; i++) {
    PImage prev = pyr[i-1];
    PImage g = prev.copy();
    g.filter(BLUR, 1); // mild blur before downsample
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
      // perceptual luma (sRGB)
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

// =================== Horn–Schunck dense flow ===================

void hornSchunck(float[][] A, float[][] B, float[][] u, float[][] v, float alpha, int iters) {
  int h = A.length, w = A[0].length;

  // Gradients (Ix, Iy) via simple Sobel; It = B - A
  float[][] Ix = sobelX(A);
  float[][] Iy = sobelY(A);
  float[][] It = new float[h][w];
  for (int y=0; y<h; y++) for (int x=0; x<w; x++) It[y][x] = B[y][x] - A[y][x];

  // Iterative refinement
  float a2 = alpha*alpha;
  float[][] uAvg = new float[h][w];
  float[][] vAvg = new float[h][w];

  for (int k=0; k<iters; k++) {
    boxAverage(u, uAvg);  // local smoothness (3x3 box)
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

// 3x3 box average
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
  // copy edges
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

// =================== Warping & blending ===================

PImage morphFrame(PImage A, PImage B, float[][] u, float[][] v, float t,
                  boolean gammaCorrect, boolean premult) {
  int w = A.width, h = A.height;
  PImage out = createImage(w, h, ARGB);
  A.loadPixels(); B.loadPixels(); out.loadPixels();

  for (int y=0; y<h; y++) {
    for (int x=0; x<w; x++) {
      float uf = u[y][x], vf = v[y][x];

      // sample coords
      float ax = x - t*uf, ay = y - t*vf;
      float bx = x + (1.0 - t)*uf, by = y + (1.0 - t)*vf;

      int ca = bilinear(A, ax, ay);
      int cb = bilinear(B, bx, by);

      // unpack
      float Aa = alpha(ca)/255.0, Ar = red(ca)/255.0, Ag = green(ca)/255.0, Ab = blue(ca)/255.0;
      float Ba = alpha(cb)/255.0, Br = red(cb)/255.0, Bg = green(cb)/255.0, Bb = blue(cb)/255.0;

      if (gammaCorrect) {
        Ar = pow(Ar, 2.2); Ag = pow(Ag, 2.2); Ab = pow(Ab, 2.2);
        Br = pow(Br, 2.2); Bg = pow(Bg, 2.2); Bb = pow(Bb, 2.2);
      }

      if (premult) {
        Ar *= Aa; Ag *= Aa; Ab *= Aa;
        Br *= Ba; Bg *= Ba; Bb *= Ba;
      }

      float wB = t;            // can be replaced by confidence mask mix
      float wA = 1.0 - wB;

      float R = wA*Ar + wB*Br;
      float G = wA*Ag + wB*Bg;
      float Bl= wA*Ab + wB*Bb;
      float Aout = wA*Aa + wB*Ba;

      if (premult && Aout > 1e-6) {
        R /= Aout; G /= Aout; Bl /= Aout;
      }
      if (gammaCorrect) {
        R = pow(max(0, R), 1.0/2.2);
        G = pow(max(0, G), 1.0/2.2);
        Bl= pow(max(0, Bl), 1.0/2.2);
      }

      out.pixels[y*w + x] = color(constrain(R*255,0,255), constrain(G*255,0,255), constrain(Bl*255,0,255), constrain(Aout*255,0,255));
    }
  }
  out.updatePixels();
  return out;
}

int bilinear(PImage img, float fx, float fy) {
  int w = img.width, h = img.height;
  if (fx < 0) fx = 0; if (fy < 0) fy = 0;
  if (fx > w-1) fx = w-1; if (fy > h-1) fy = h-1;

  int x0 = floor(fx), y0 = floor(fy);
  int x1 = min(x0+1, w-1), y1 = min(y0+1, h-1);
  float tx = fx - x0, ty = fy - y0;

  int c00 = img.pixels[y0*w + x0];
  int c01 = img.pixels[y0*w + x1];
  int c10 = img.pixels[y1*w + x0];
  int c11 = img.pixels[y1*w + x1];

  float a00=alpha(c00), r00=red(c00), g00=green(c00), b00=blue(c00);
  float a01=alpha(c01), r01=red(c01), g01=green(c01), b01=blue(c01);
  float a10=alpha(c10), r10=red(c10), g10=green(c10), b10=blue(c10);
  float a11=alpha(c11), r11=red(c11), g11=green(c11), b11=blue(c11);

  float a0 = mix(a00, a01, tx), a1 = mix(a10, a11, tx);
  float r0 = mix(r00, r01, tx), r1 = mix(r10, r11, tx);
  float g0 = mix(g00, g01, tx), g1 = mix(g10, g11, tx);
  float b0 = mix(b00, b01, tx), b1 = mix(b10, b11, tx);

  return color(mix(r0, r1, ty), mix(g0, g1, ty), mix(b0, b1, ty), mix(a0, a1, ty));
}

void ensureDir(String path) {
  java.io.File d = new java.io.File(path);
  if (!d.exists()) d.mkdirs();
}
