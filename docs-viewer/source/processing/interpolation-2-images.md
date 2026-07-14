---
doc_id: interpolation-2-images
title: Interpolation 2 images
added_date: "2026-07-14 11:38"
last_updated: "2026-07-14 11:38"
parent_id: composites-engine
---
# Interpolation 2 images



```
Interpolation between 2 images

```


Here’s a compact starter + a full HTML explainer you can download.

**TL;DR (quickest path)**
	•	**Fastest crossfade in Processing** (GPU): draw A, then draw B with tint(255, alpha) where alpha = 255 * t.
	•	**Best-looking fade**: do it **gamma-correct** (linear-light) via a tiny fragment shader.
	•	**Export to video**: save PNG frames, then ffmpeg -r 30 -i out/frame%04d.png -c:v libx264 -crf 18 out.mp4.

**Minimal Processing (fast GPU crossfade)**


```
*// CrossfadeTwoImages.pde*
```


```

PImage imgA, imgB;
int frames = 150;          
```


```
*// number of transition frames*
```


```

int w = 3840, h = 2160;    
```


```
*// adjust for your target resolution*
```


```


void settings() { size(w, h, P2D); }
void setup() {
  surface.setTitle("Two-Image Crossfade");
  imgA = loadImage("A.jpg"); 
```


```
*// or PNG; alpha is respected*
```


```

  imgB = loadImage("B.jpg");
  imageMode(CORNER);
  frameRate(30);
}

void draw() {
  float t = constrain((float)frameCount / frames, 0, 1);

  
```


```
*// Draw A*
```


```

  pushStyle();
  tint(255, 255);
  image(imgA, 0, 0, width, height);

  
```


```
*// Draw B with alpha*
```


```

  int alpha = int(255 * t);
  tint(255, alpha);
  image(imgB, 0, 0, width, height);
  popStyle();

  saveFrame("out/frame####.png");
  if (frameCount >= frames) exit();
}

```


**Gamma-correct version (nicer tonality)**

Use a fragment shader to interpolate in linear light.

**GammaCorrectCrossfade.pde**


```
PImage imgA, imgB;
PShader crossfade;
int frames = 150;
int w = 3840, h = 2160;

void settings() { size(w, h, P2D); }
void setup() {
  surface.setTitle("Gamma-Correct Crossfade");
  imgA = loadImage("A.jpg");
  imgB = loadImage("B.jpg");
  crossfade = loadShader("crossfade.frag");
  frameRate(30);
}

void draw() {
  float t = constrain((float)frameCount / frames, 0, 1);
  crossfade.set("t", t);
  crossfade.set("texA", imgA);
  crossfade.set("texB", imgB);
  shader(crossfade);
  image(imgA, 0, 0, width, height);  
```


```
*// any quad; shader samples both*
```


```

  resetShader();
  saveFrame("out/frame####.png");
  if (frameCount >= frames) exit();
}

```


**data/crossfade.frag**

```

#ifdef GL_ES
precision mediump float;
precision mediump int;
#endif

uniform sampler2D texA;
uniform sampler2D texB;
uniform float t;
varying vec4 vertTexCoord;


```


```
*// approximate sRGB <-> linear*
```


```

vec3 srgb_to_linear(vec3 c)  { return pow(c, vec3(2.2)); }
vec3 linear_to_srgb(vec3 c)  { return pow(c, vec3(1.0/2.2)); }

void main() {
  vec2 uv = vertTexCoord.st;
  vec4 a = texture2D(texA, uv);
  vec4 b = texture2D(texB, uv);

  
```


```
*// premultiply alpha so PNG transparency blends cleanly*
```


```

  vec3 a_rgb = srgb_to_linear(a.rgb) * a.a;
  vec3 b_rgb = srgb_to_linear(b.rgb) * b.a;
  float a_a = a.a;
  float b_a = b.a;

  vec3 mix_rgb = mix(a_rgb, b_rgb, t);
  float mix_a  = mix(a_a,  b_a,  t);

  vec3 out_rgb = mix_a > 0.0 ? mix_rgb / mix_a : vec3(0.0);
  out_rgb = linear_to_srgb(out_rgb);
  gl_FragColor = vec4(out_rgb, mix_a);
}

```


**Export frames to video (FFmpeg)**


```
*# from the sketch folder*
```


```

ffmpeg -r 30 -i out/frame%04d.png -s 3840x2160 \
  -pix_fmt yuv420p -crf 18 -preset medium -c:v libx264 crossfade_uhd_30fps.mp4

```


**Extras you might want**
	•	**Alignment first** (homography / landmarks) to reduce ghosting, then crossfade.
	•	**Feature-based morph** (Delaunay triangles warped per-frame, then blend).
	•	**Optical-flow morph** (dense flow A→B, warp + blend) for that “melting” look.
	•	**UHD performance**: stick to P2D and shaders; avoid CPU per-pixel loops at 4K.

⸻

**Download the full HTML explainer (Apple Notes/GitHub-ready)**

It includes everything above plus FFmpeg one-liners, CPU reference code, and notes on alpha, gamma, and UHD.

**[Download the HTML explainer](sandbox:/mnt/data/image_interpolation_explainer.html?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=c7bf75ba-3163-4b44-909a-2b3487edd45f)**

If you’d like, I can also package this as a tiny Processing project folder with data/ placeholders ready to drop your two images into. 



```
The code needs to be optimised for static image generation. The aim is to use it to create interpolations between a large series of images, which will then be stitched together to effectively create a slow motion video 

```


Perfect—let’s optimise this for **static frame generation at scale** (so you can stitch everything later into a slow-motion video) and keep it GPU-fast, low-memory, and resumable.

**What you’re getting**
	•	A **Processing batch interpolator** that:
	•	Loads only the current **pair** of images (low RAM).
	•	Generates INTER_FRAMES in-betweens per pair (plus optional **HOLD_START/HOLD_END**).
	•	Uses a **gamma-correct GLSL shader** (better tonality than naïve sRGB blends).
	•	Writes **sequentially numbered PNGs** for easy stitching and **resume**.
	•	Logs a compact **manifest.csv** (which frames came from which pair).
	•	A concise **HTML README** with usage and FFmpeg commands.

**Download**
	•	**Processing sketch folder**: /mnt/data/BatchImageInterpolator
	•	Main file: **BatchImageInterpolator.pde** — batch logic + config
	•	Shader: **data/crossfade.frag** — gamma-correct crossfade (premultiplied-alpha aware)
	•	Output folders you’ll create: input/ (your ordered images), out/ (frames)
	•	**[README (HTML)](sandbox:/mnt/data/BatchImageInterpolator/Batch_Image_Interpolator_README.html?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=e0f4f787-0916-4ab5-b3f9-72d0c8acb104)** — setup, tuning, FFmpeg examples

**One-time setup (super short)**
	1.	Open the sketch in Processing.
	2.	Create input/ inside the sketch folder and drop your ordered images there (e.g., img_0001.jpg, img_0002.jpg, …).
	3.	In BatchImageInterpolator.pde, edit the **Quick Config** block:
	•	INTER_FRAMES → how many in-betweens per pair (e.g., 30).
	•	HOLD_START / HOLD_END → duplicate still frames around each transition.
	•	CANVAS_W/H → output resolution (e.g., UHD 3840×2160).
	•	FIT_MODE → FIT (letterbox), FILL (crop), or STRETCH.
	•	EASING → linear, smoothstep, easeInOutCubic.
	•	OVERWRITE=false to **resume** safely.
	4.	Run. Frames appear in out/ as frame_000000.png, frame_000001.png, …

**Why this is optimised for static output**
	•	**Streaming pairs**: only two PImages in RAM at any time.
	•	**GPU path**: no CPU per-pixel loops; a single quad with a shader.
	•	**Gamma-correct**: blends in linear light; avoids muddy mid-tones.
	•	**Resumable**: scans out/ to pick the next frame index; set OVERWRITE=false.
	•	**Deterministic**: strict filename ordering → easy FFmpeg stitching.

**Stitch to slow-mo video later (examples)**


```
*# 25 fps H.264 (good delivery quality)*
```


```

ffmpeg -r 25 -i out/frame%06d.png -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p slow_interpolation_25fps.mp4


```


```
*# 25 fps ProRes 422 HQ (archival / NLE-friendly)*
```


```

ffmpeg -r 25 -i out/frame%06d.png -c:v prores_ks -profile:v 3 slow_interpolation_25fps_prores.mov

```


**Tips for very large runs**
	•	Set SHOW_PREVIEW=false to reduce draw overhead.
	•	Keep OVERWRITE=false so you can stop/restart anytime without losing work.
	•	Use HOLD_* to slow the feel without exploding the number of pairs.
	•	Keep inputs consistently sized and ordered; the sorter is by filename.

⸻

Need me to add:
	•	**Homography alignment** (auto-register per pair) before blending,
	•	**Triangle-mesh morph** (feature points → Delaunay → affine per triangle), or
	•	**Optical-flow morph** (flow-based warp + blend)

…so your in-betweens feel more “morph-like” than “crossfade-like”? I can drop in optional modules next. 



```
Download BatchImageInterpolator

```


Got it — here’s your full Processing sketch, shader, and README bundled together.

 <span style="font-family: .AppleColorEmojiUI;">
     [⬇️](sandbox:/mnt/data/BatchImageInterpolator.zip?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=d9a0ee9f-1c57-4005-84e2-8509c3d07839)
 </span>**[ Download BatchImageInterpolator (ZIP)](sandbox:/mnt/data/BatchImageInterpolator.zip?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=d9a0ee9f-1c57-4005-84e2-8509c3d07839)**

The ZIP contains:
	•	BatchImageInterpolator.pde — main Processing code (batch static frame interpolator).
	•	data/crossfade.frag — GLSL shader for gamma-correct blending.
	•	Batch_Image_Interpolator_README.html — usage guide with config, FFmpeg tips, and workflow notes.
	•	(create input/ for your source images, out/ will be generated automatically).

Would you like me to also include a **ready-made “input/” folder with two placeholder images** so the sketch runs immediately for testing?


```
Explain: 

Homography alignment (auto-register per pair) before blending,
	•	Triangle-mesh morph (feature points → Delaunay → affine per triangle), or
	•	Optical-flow morph (flow-based warp + blend)

```


Great question — these three techniques are ways of **going beyond simple crossfades**, so your interpolations look like natural morphs instead of just double-exposed blends. I’ll break each down clearly, with an HTML-ready explanation you can reuse in your notes or project docs.

⸻

**Image Alignment & Morphing Methods**

**1. Homography alignment (auto-register per pair before blending)**

**What it is:**
A *homography* is a 3×3 matrix that maps one plane in an image onto another. If your two images are of the same flat scene (e.g., a poster, painting, or building façade) but taken from slightly different viewpoints, a homography can align them.

**Workflow:**
	1.	Detect keypoints in both images (e.g., SIFT, ORB).
	2.	Match keypoints (nearest-neighbor search).
	3.	Estimate the homography matrix H using RANSAC (robust to outliers).
	4.	Warp image B using H to align it with image A.
	5.	Crossfade between A and the warped B.

**Effect:**
Reduces ghosting — instead of “double eyes” or “double letters,” features align and fade smoothly.
Best for planar surfaces or when the camera motion is a rotation/translation around a single scene.

⸻

**2. Triangle-mesh morph (feature points → Delaunay → affine per triangle)**

**What it is:**
A *feature-based morph* that uses manually (or automatically) chosen control points, then warps both images toward an intermediate shape before blending.

**Workflow:**
	1.	Choose corresponding points (e.g., left eye corner in A ↔ left eye corner in B).
	•	This can be manual (GUI) or automatic (face landmark detectors).
	2.	Compute the *average* positions of these points for a given interpolation time t.
	3.	Triangulate the point set (usually with *Delaunay triangulation*).
	4.	For each triangle:
	•	Compute the affine transform from A’s triangle → intermediate triangle.
	•	Compute the affine transform from B’s triangle → intermediate triangle.
	•	Warp pixels from A and B into that triangle and blend by factor t.
	5.	Assemble warped triangles into the full frame.

**Effect:**
Produces “true morphs” where shapes (faces, objects) gradually *shift and transform* instead of just fading.
Classic method in film VFX (Beier–Neely morphs).

⸻

**3. Optical-flow morph (flow-based warp + blend)**

**What it is:**
Optical flow estimates a dense pixel-wise motion field between two frames: for each pixel in A, a vector tells you where it moves to in B.

**Workflow:**
	1.	Compute dense optical flow A→B (e.g., Farnebäck, TV-L1, or deep learning models like RAFT).
	2.	For a time t:
	•	Warp A forward by t \cdot \text{flow}.
	•	Warp B backward by (1−t) \cdot \text{flow}.
	3.	Blend the warped images.
	4.	Repeat for intermediate timesteps.

**Effect:**
Produces the smoothest “liquid morphs” — objects bend, stretch, and flow from one to another.
But: optical flow is heavy to compute and can create artefacts (tearing, “melting”) if the flow is wrong or occlusions exist.

⸻

**Comparison Table**

| Method                                            | Data Needed                                       | Complexity                                        | Best For                                          | Artefacts / Limitations                           |
|---------------------------------------------------|---------------------------------------------------|---------------------------------------------------|---------------------------------------------------|---------------------------------------------------|
| Homography                                        | Keypoints (auto)                                  | Low                                               | Flat/planar scenes, small camera motion           | Only works if scene ≈ planar; 3D objects misalign |
| Triangle-mesh                                     | Feature points (manual/auto)                      | Medium                                            | Faces, structured objects                         | Needs good correspondences; triangles may fold    |
| Optical-flow                                      | Dense motion (auto)                               | High                                              | Arbitrary scenes, smooth morphs                   | Flow estimation errors → warping artefacts        |



⸻

**Visual Metaphor**
	•	**Homography** = “lining up two transparencies” on a light table.
	•	**Triangle-mesh** = “cutting images into puzzle pieces and reshaping them.”
	•	**Optical-flow** = “melting one image into the other like wax.”

⸻

 <span style="font-family: .AppleColorEmojiUI;">
     👉
 </span> Would you like me to **integrate one of these methods into your BatchImageInterpolator sketch** (e.g., auto-homography alignment using OpenCV before blending), or just keep them as conceptual notes for now?


```
Download html as conceptual notes

```


All set. Here are your conceptual notes as a clean HTML file:

 <span style="font-family: .AppleColorEmojiUI;">
     [⬇️](sandbox:/mnt/data/alignment_and_morphing_concepts.html?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=fccc00a6-13ce-440c-baa2-fc7d976c1eed)
 </span>**[ Download: Alignment & Morphing Concepts (HTML)](sandbox:/mnt/data/alignment_and_morphing_concepts.html?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=fccc00a6-13ce-440c-baa2-fc7d976c1eed)**

Contents:
	•	Homography alignment (auto-register per pair) — workflow, best use, limits
	•	Triangle-mesh morph (feature points → Delaunay → affine per triangle)
	•	Optical-flow morph (flow-based warp + blend)
	•	Comparison table + practical notes on blending (gamma-correct, premultiplied alpha) and multi-band seams

If you want, I can extend this with lightweight pseudocode blocks for OpenCV/Processing integrations next. 


```
Explain Optical-flow morph in more detail. Implementation needs to be pure Processing. Suggest any additional libraries 

```


**Optical-flow morph (Processing-only): how it works + code you can drop in**

Below is a practical, **Processing-native** approach for generating in-between frames using **dense optical flow**. I’ll show:
	1.	What optical flow is + the morph equation
	2.	A production-ish pipeline (multi-scale, masks, hole-fill)
	3.	A **pure Processing** reference implementation (Horn–Schunck dense flow + CPU bilinear warping) suitable for offline static frame generation
	4.	Suggested Java libraries you can add to Processing for higher quality/robustness (still “Processing” because it’s Java on the JVM)

⸻

**1) Concept in one minute**
	•	**Dense optical flow** gives you a 2-D motion vector **F(x,y) = (u,v)** for (almost) every pixel, mapping where pixels in A are expected to move to in B.
	•	For an in-between time **t**  <span style="font-family: AppleSymbols;">
     ∈
 </span> **[0,1]**, you warp **A** forward by **t·F** and **B** backward by **(1−t)·F**, then blend:

I_t(x,y) \;=\; (1-w)\;A\big(x - t\cdot u(x,y),\,y - t\cdot v(x,y)\big) \;+\; w\;B\big(x + (1-t)\cdot u(x,y),\,y + (1-t)\cdot v(x,y)\big)

where w is typically t (or use gamma-correct, premultiplied blending for better tonality/alpha handling).

⸻

**2) Pipeline you can trust for static (offline) rendering**
	1.	**Preprocess**
	•	Convert to linear-light working space if you care about tonality (or keep sRGB and do gamma-correct blending later).
	•	Mild denoise / Gaussian blur σ≈0.5–1.0 can stabilise flow.
	2.	**Multi-scale (image pyramid)**
	•	Build L levels (coarsest → finest).
	•	Estimate flow at the coarsest level (easy motion), then **upsample & refine** at each finer level.
	3.	**Flow estimation** (Horn–Schunck here; Farnebäck/TV-L1 if you add OpenCV)
	•	Iteratively minimise a data term (brightness constancy) + smoothness term (regularisation).
	•	50–150 iterations per scale is common for offline frames.
	4.	**Forward–backward consistency (optional)**
	•	Compute flow A→B **and** B→A; flag pixels where they disagree → likely occlusions.
	•	Use these flags to down-weight the unreliable side during blending.
	5.	**Warp & blend**
	•	**Bilinear sampling** from A and B at sub-pixel coordinates.
	•	Prefer **premultiplied** + **gamma-correct** blending to avoid muddy mids and dark fringes.
	6.	**Hole-filling**
	•	Small holes (due to disocclusions) can be filled with edge-aware interpolation (quick fallback: repeated bilateral/median where mask = hole).

⸻

**3) Pure Processing reference: Dense Horn–Schunck + CPU warper**

This is designed for **offline static frame generation** (not real-time). It’s compact and readable rather than hyper-optimised; for UHD you’ll want to (a) reduce iteration counts, (b) run multi-scale, and (c) consider tiling or using a library.

Files assume two same-size images A.jpg, B.jpg inside data/. You can integrate this into your BatchImageInterpolator by replacing the crossfade with morphFrame(...).

**3.1 Sketch shell**

```


```


```
*// OpticalFlowMorphHS.pde*
```


```

PImage imgA, imgB;
int W = 1280, H = 720;      
```


```
*// set to your working resolution*
```


```

int LEVELS = 3;             
```


```
*// pyramid levels (coarsest to finest)*
```


```

int HS_ITERS = 80;          
```


```
*// iterations per level*
```


```

float HS_ALPHA = 40.0;      
```


```
*// smoothness (bigger = smoother flow)*
```


```


void settings() { size(W, H, P2D); }
void setup() {
  imgA = loadImage("A.jpg");
  imgB = loadImage("B.jpg");
  imgA.resize(W, H);
  imgB.resize(W, H);

  
```


```
*// Build Gaussian pyramids*
```


```

  PImage[] pyrA = buildPyr(imgA, LEVELS);
  PImage[] pyrB = buildPyr(imgB, LEVELS);

  
```


```
*// Compute dense flow u,v from A->B (start at coarsest)*
```


```

  float[][] u = zeros(W, H);
  float[][] v = zeros(W, H);

  for (int lvl = LEVELS-1; lvl >= 0; lvl--) {
    int w = pyrA[lvl].width, h = pyrA[lvl].height;

    
```


```
*// Upscale flow to current level (skip for coarsest)*
```


```

    if (lvl < LEVELS-1) {
      u = upscale(u, w, h);
      v = upscale(v, w, h);
    } else {
      u = zeros(w, h);
      v = zeros(w, h);
    }

    
```


```
*// Convert images to grayscale float arrays*
```


```

    float[][] a = toGrayArray(pyrA[lvl]);
    float[][] b = toGrayArray(pyrB[lvl]);

    
```


```
*// Horn–Schunck refinement at this scale*
```


```

    hornSchunck(a, b, u, v, HS_ALPHA, HS_ITERS);
  }

  
```


```
*// Generate a few in-between frames*
```


```

  background(0);
  for (int i = 0; i <= 30; i++) {
    float t = i/30.0;
    PImage frame = morphFrame(imgA, imgB, u, v, t, true 
```


```
*/*gammaCorrect*/*
```


```
, true 
```


```
*/*premult*/*
```


```
);
    image(frame, 0, 0);
    saveFrame("out/morph_##.png");
  }
  println("done");
  exit();
}

```


**3.2 Utility: pyramids, arrays, filtering**

```

PImage[] buildPyr(PImage img, int levels) {
  PImage[] pyr = new PImage[levels];
  pyr[0] = img.get();
  for (int i=1; i<levels; i++) {
    PImage prev = pyr[i-1];
    PImage g = prev.copy();
    g.filter(BLUR, 1); 
```


```
*// mild blur before downsample*
```


```

    PImage d = createImage(max(1, prev.width/2), max(1, prev.height/2), ALPHA);
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
      
```


```
*// sRGB luma approximation*
```


```

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

```


**3.3 Horn–Schunck dense flow (single-scale iteration)**

```

void hornSchunck(float[][] A, float[][] B, float[][] u, float[][] v, float alpha, int iters) {
  int h = A.length, w = A[0].length;

  
```


```
*// Gradients (Ix, Iy) via simple Sobel; It = B - A*
```


```

  float[][] Ix = sobelX(A);
  float[][] Iy = sobelY(A);
  float[][] It = new float[h][w];
  for (int y=0; y<h; y++) for (int x=0; x<w; x++) It[y][x] = B[y][x] - A[y][x];

  
```


```
*// Iterative refinement*
```


```

  float a2 = alpha*alpha;
  float[][] uAvg = new float[h][w];
  float[][] vAvg = new float[h][w];

  for (int k=0; k<iters; k++) {
    boxAverage(u, uAvg);  
```


```
*// local smoothness (4/8-neighbourhood)*
```


```

    boxAverage(v, vAvg);

    for (int y=1; y<h-1; y++) {
      for (int x=1; x<w-1; x++) {
        float ix = Ix[y][x], iy = Iy[y][x], it = It[y][x];
        float denom = a2 + ix*ix + iy*iy;
        
```


```
*// brightness constancy term*
```


```

        float P = ix*uAvg[y][x] + iy*vAvg[y][x] + it;
        
```


```
*// update*
```


```

        u[y][x] = uAvg[y][x] - (ix * P) / denom;
        v[y][x] = vAvg[y][x] - (iy * P) / denom;
      }
    }
  }
}


```


```
*// Simple 3x3 box average*
```


```

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
  
```


```
*// copy edges*
```


```

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

```


**3.4 Warping + gamma-correct, premultiplied blending**

```

PImage morphFrame(PImage A, PImage B, float[][] u, float[][] v, float t,
                  boolean gammaCorrect, boolean premult) {
  int w = A.width, h = A.height;
  PImage out = createImage(w, h, ARGB);
  A.loadPixels(); B.loadPixels(); out.loadPixels();

  for (int y=0; y<h; y++) {
    for (int x=0; x<w; x++) {
      float uf = u[y][x], vf = v[y][x];

      
```


```
*// sample coords*
```


```

      float ax = x - t*uf, ay = y - t*vf;
      float bx = x + (1.0 - t)*uf, by = y + (1.0 - t)*vf;

      int ca = bilinear(A, ax, ay);
      int cb = bilinear(B, bx, by);

      
```


```
*// unpack*
```


```

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

      float wB = t;            
```


```
*// can use confidence mask here; default: t*
```


```

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

```


**Performance note:** For UHD, consider:
	•	Reducing HS_ITERS and increasing LEVELS (e.g., 4–5 levels, 30–50 iters/level).
	•	Doing the warping in a **shader** (upload flow as a 2-channel float texture encoded in RG).
	•	Running in **headless** (no preview) and saving frames to disk (your BatchImageInterpolator pattern).

⸻

**4) “Still Processing” but stronger: add a Java CV library**

If you want higher quality, robustness, and speed without leaving Processing (still Java):
	•	**BoofCV** (pure Java, easy to add as a Processing library):
	•	Pros: No native binaries, good documentation, has optical-flow algorithms (e.g., Horn–Schunck variants, KLT tracking, dense/discrete flow).
	•	How: Download BoofCV jars, put in code/ folder of your sketch, import classes and call the dense flow.
	•	Use case: dependable pure-Java baseline with multi-scale flow and decent speed.
	•	**OpenCV for Processing** (wrapper) or **JavaCV** (OpenCV bindings):
	•	Pros: Access to **Farnebäck**, **TV-L1**, **DIS** optical flow, pyramidal LK, feature detection, homography, etc.
	•	Cons: Native binaries (platform-specific), slightly more setup.
	•	How: Install the Processing OpenCV library (or include JavaCV/Bytedeco jars + natives in code/), then call calcOpticalFlowFarneback(...) / DualTVL1OpticalFlow_create() equivalents.

**Recommended path:**
	•	Start with the **pure Processing** Horn–Schunck above to prove the pipeline + warping/blending.
	•	If you like the results but want cleaner motion on tougher content, switch the hornSchunck(...) step to **BoofCV** dense flow (small code changes) or **OpenCV Farnebäck/TV-L1** for more robustness.

⸻

**5) Where this slots into your BatchImageInterpolator**
	1.	For each image pair (A, B):
	•	Compute (or load cached) flow (u,v) once.
	2.	For each intermediate frame t:
	•	Call morphFrame(A,B,u,v,t, gammaCorrect=true, premult=true).
	3.	Save frames to out/frame%06d.png, stitch with FFmpeg as you already do.

If you want, I can deliver a **drop-in variant** of your BatchImageInterpolator.pde that:
	•	Computes/caches a per-pair flow_XXXX.bin (so you don’t recompute on resume), and
	•	Replaces the crossfade shader with the **CPU morphFrame** path above (or a GLSL warper if you’d like to go GPU for the warp step).


```
Download html explanation and all pde code

```


All set. You can download both the HTML explanation and the full Processing sketch here:
	•	 <span style="font-family: .AppleColorEmojiUI;">
     [⬇️](sandbox:/mnt/data/optical_flow_morph_explainer.html?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=5a1074ca-1038-4e4a-8253-c9b04d57a8ba)
 </span>**[ Optical-flow Morph — HTML explainer](sandbox:/mnt/data/optical_flow_morph_explainer.html?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=5a1074ca-1038-4e4a-8253-c9b04d57a8ba)**
	•	 <span style="font-family: .AppleColorEmojiUI;">
     [⬇️](sandbox:/mnt/data/OpticalFlowMorph_Processing.zip?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=5a1074ca-1038-4e4a-8253-c9b04d57a8ba)
 </span>**[ OpticalFlowMorph_Processing.zip](sandbox:/mnt/data/OpticalFlowMorph_Processing.zip?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=5a1074ca-1038-4e4a-8253-c9b04d57a8ba)**
(contains OpticalFlowMorphHS.pde — single-file pure Processing implementation)

If you want, I can also provide a **drop-in variant** that plugs this flow-based morph directly into your BatchImageInterpolator (with caching of per-pair flow fields). 

Done! Here’s the drop-in **optical-flow** version of your batch interpolator with **per-pair flow caching**:
	•	 <span style="font-family: .AppleColorEmojiUI;">
     [⬇️](sandbox:/mnt/data/BatchImageInterpolator_Flow.zip?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=c870a1e9-30cb-4dec-aeae-e12c9f3310e2)
 </span>**[ Download: BatchImageInterpolator_Flow.zip](sandbox:/mnt/data/BatchImageInterpolator_Flow.zip?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=c870a1e9-30cb-4dec-aeae-e12c9f3310e2)**
Contains:
	•	BatchImageInterpolator_Flow.pde — batch generator using Horn–Schunck multi-scale flow, cached per pair (out/flows/flow_XXXXXX.bin)
	•	README_Flow.html — quick setup + FFmpeg tips

How to use:
	1.	Unzip into your Processing sketches folder.
	2.	Create input/ and drop your ordered images.
	3.	Open BatchImageInterpolator_Flow.pde and tweak the **QUICK CONFIG** (canvas size, INTER_FRAMES, HOLDs, FIT_MODE).
	4.	Run. Frames are saved to out/, and per-pair flows are cached in out/flows/.

Want me to also make a **GPU warper** variant (uploading the flow to a shader) for faster UHD runs? 

Here you go — a **GPU warper** variant that keeps the heavy per-frame work on the GPU while caching per-pair flow on disk:
	•	 <span style="font-family: .AppleColorEmojiUI;">
     [⬇️](sandbox:/mnt/data/BatchImageInterpolator_FlowGPU.zip?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=4c592b54-7d57-4659-8f16-1f8a09414d36)
 </span>**[ Download: BatchImageInterpolator_FlowGPU.zip](sandbox:/mnt/data/BatchImageInterpolator_FlowGPU.zip?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=4c592b54-7d57-4659-8f16-1f8a09414d36)**
Contents:
	•	BatchImageInterpolator_FlowGPU.pde — batch driver, computes/loads flow (CPU), builds RG flow texture, renders frames via shader
	•	data/morph_flow.frag — GLSL shader (decodes flow, warps A/B, gamma-correct premult blend)
	•	README_FlowGPU.html — quick setup + FFmpeg command

**How it works (quick recap)**
	•	For each pair, we compute Horn–Schunck flow (CPU, once), cache it as out/flows/flow_XXXXXX.bin.
	•	We pack (u,v) into an 8-bit **RG** texture with a per-pair flowScale (max |u| or |v| in pixels).
	•	The shader decodes flow to **UV offsets**, samples A at uv − t*d and B at uv + (1−t)*d, and blends in **linear light** with premultiplied alpha.
	•	Result: UHD-friendly, super fast per-frame generation.

If you want a version that uses **float textures** (GL-only, more precision) or swaps HS for **BoofCV/OpenCV** flow while keeping the same GPU warp, say the word and I’ll package that too. 


```
Starting from a simple processing code to layer images together, provide a route map to using optical flow to generate interpolation 

```


Here’s a clean HTML “route map” you can keep alongside your project:

 <span style="font-family: .AppleColorEmojiUI;">
     [⬇️](sandbox:/mnt/data/route_map_optical_flow.html?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=69fea0a0-44b7-4a80-8692-0e3c57eb6dc3)
 </span>**[ Download: Route Map — Layering → Optical-Flow Interpolation (HTML)](sandbox:/mnt/data/route_map_optical_flow.html?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=69fea0a0-44b7-4a80-8692-0e3c57eb6dc3)**

It walks you step-by-step from:
	•	simple image layering → eased crossfades,
	•	gamma-correct shader blending,
	•	canvas normalization (FIT/FILL/STRETCH),
	•	optional homography alignment,
	•	pure-Processing Horn–Schunck optical flow (multi-scale),
	•	bilinear warping with gamma-correct premult blending,
	•	per-pair flow caching,
	•	GPU warper (flow texture + GLSL),
	•	and batch stitching with FFmpeg.

If you want this turned into a **checklist** with tick-boxes or a **project Kanban** (HTML/CSV), say the word and I’ll generate it. 


```
Checklist and kanban

```


All set! Here are your project trackers:
	•	 <span style="font-family: .AppleColorEmojiUI;">
     [✅](sandbox:/mnt/data/checklist_optical_flow.html?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=9593c76b-7631-4fdc-b7dd-b77df48a6ad1)
 </span>**[ Checklist (HTML)](sandbox:/mnt/data/checklist_optical_flow.html?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=9593c76b-7631-4fdc-b7dd-b77df48a6ad1)** – tick items as you complete them (printable; in-page state only).
	•	 <span style="font-family: .AppleColorEmojiUI;">
     [🗂️](sandbox:/mnt/data/kanban_optical_flow.html?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=9593c76b-7631-4fdc-b7dd-b77df48a6ad1)
 </span>**[ Kanban Board (HTML, drag-and-drop)](sandbox:/mnt/data/kanban_optical_flow.html?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=9593c76b-7631-4fdc-b7dd-b77df48a6ad1)** – move cards between Backlog, Doing, Done right in the browser.
	•	 <span style="font-family: .AppleColorEmojiUI;">
     [📄](sandbox:/mnt/data/kanban_optical_flow.csv?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=9593c76b-7631-4fdc-b7dd-b77df48a6ad1)
 </span>**[ Kanban CSV](sandbox:/mnt/data/kanban_optical_flow.csv?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=9593c76b-7631-4fdc-b7dd-b77df48a6ad1)** – import into Trello/Notion/Sheets if you want.

If you’d like persistence (saving the board/checklist state to a JSON file), I can generate a version that stores to localStorage or writes/reads a JSON next to the HTML when run from a local server. 


```
the processing code is static, so the draw function is not to create frames. It is purely a batch image generator 

```


Perfect—that matches your workflow. I’ve packaged a **static, no-draw-loop** batch generator that does everything inside setup() and exits when done.
	•	 <span style="font-family: .AppleColorEmojiUI;">
     [⬇️](sandbox:/mnt/data/StaticBatchGenerator.zip?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=07f061c3-6aee-44a9-953b-098e443f3283)
 </span>**[ StaticBatchGenerator.zip](sandbox:/mnt/data/StaticBatchGenerator.zip?_chatgptios_conversationID=68b58a7b-a69c-8321-8a64-240da57a969c&_chatgptios_messageID=07f061c3-6aee-44a9-953b-098e443f3283)**
Contents:
	•	StaticBatchGenerator.pde — runs the entire batch in setup() (no draw()), then exit()
	•	data/crossfade.frag — gamma-correct crossfade shader (for MODE="CROSSFADE")
	•	data/morph_flow.frag — GPU flow warper shader (for MODE="FLOW_GPU")
	•	README_Static.html — quick usage notes

**How it behaves**
	•	Processes all adjacent image pairs from input/, normalises them to your canvas (FIT/FILL/STRETCH), and writes sequential PNGs to out/.
	•	Modes:
	•	CROSSFADE — gamma-correct fades via shader.
	•	FLOW_CPU — **pure Processing** Horn–Schunck multi-scale flow + CPU warp/blend.
	•	FLOW_GPU — compute flow once (CPU), pack to RG texture, warp on GPU per frame.
	•	Per-pair **flow caching** in out/flows/flow_XXXXXX.bin, so re-runs skip recomputation.
	•	**Resume-safe**: it scans out/ to continue numbering unless OVERWRITE=true.

**Set up quickly**
	1.	Put ordered source images in input/.
	2.	Open StaticBatchGenerator.pde; set:
	•	MODE = "FLOW_CPU" (or "FLOW_GPU" / "CROSSFADE")
	•	CANVAS_W/H, INTER_FRAMES, HOLD_START/END, FIT_MODE.
	3.	Run. Files land in out/. Stitch with:


```
ffmpeg -r 25 -i out/frame%06d.png -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p static_batch_25fps.mp4

```


Want me to add a **headless launcher** script (macOS/Linux .sh, Windows .bat) with memory flags and an option to run multiple worker processes on different subranges?
