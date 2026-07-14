---
doc_id: optical-flow-morph-explainer
title: "Optical-flow Morph — Pure Processing Implementation (Horn–Schunck)"
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# Optical‑flow Morph — Pure Processing (Horn–Schunck)

> Original prompt — 2025-09-02 15:44:35 (Europe/London) Explain Optical‑flow morph in more detail. Implementation needs to be pure Processing. Suggest any additional libraries.

Dense optical‑flow morphing implemented directly in Processing (Java). Single‑file sketch included below.

## Overview

Compute dense flow A→B using a multi‑scale Horn–Schunck solver, then for any t ∈ [0,1] warp A forward by t·F and B backward by (1−t)·F and blend (premultiplied + gamma‑correct recommended).

## Single‑file Processing sketch

```
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
  for (int i=1; i 1e-6) {
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
```

## Libraries you can add (optional)

- **BoofCV** (pure Java) — pyramids, KLT, dense flow; drop jars into `code/`.
- **OpenCV for Processing** / **JavaCV** — Farnebäck, TV‑L1, DIS flows (native binaries required).

Prepared: 2025-09-02 15:44:35 (Europe/London). Ready for Apple Notes/GitHub.
