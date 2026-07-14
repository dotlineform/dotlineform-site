---
doc_id: image-interpolation-explainer
title: "Image Interpolation Between Two Images — Explainer & Starter Code"
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# Interpolation between Two Images

> Original prompt — 2025-09-01 12:04:05 (Europe/London) Interpolation between 2 images

This page explains practical ways to interpolate between two still images for creative coding and video output. It includes minimal **Processing** sketches, a **gamma‑correct shader** for better blends, and **FFmpeg** tips to export video frames. UHD‑scale notes and PNG transparency handling are covered.

## What do we mean by “interpolation”?

Given two images A and B, we want a sequence of intermediate frames that transition smoothly from A to B. Common strategies:

1. **Linear Crossfade (alpha blend):** For a factor `t ∈ [0,1]`, the result is `(1−t)*A + t*B`. Fast, simple, great baseline.
2. **Dissolve:** Like crossfade, but randomized per‑pixel/patch mixing to hide ghosting. Stylised look.
3. **Warp + Crossfade:** Geometrically align B towards A (homography or feature landmarks), then crossfade. Reduces double‑exposure artefacts.
4. **Morph (Feature‑based):** Define corresponding keypoints/triangles; warp both images toward an intermediate shape and blend. Classic Beier–Neely / Delaunay‑triangle morph.
5. **Optical‑Flow Warp:** Estimate dense flow from A→B; warp A forward (or B backward) by `t*flow`, then blend. Most “liquid” but heavier.
6. **Multi‑band (Pyramid) Blend:** Blend low vs high frequencies at different rates to reduce seams.

Gamma matters.

Naïve alpha blends in sRGB can look muddy. For most realistic fades, convert to linear light, interpolate, then convert back to sRGB (

see the shader version below

).

## Fast baseline: Processing crossfade (GPU tint)

This sketch draws A, then B with varying alpha using `tint()`. Works well up to UHD on modern GPUs.

```
// File: CrossfadeTwoImages/CrossfadeTwoImages.pde
PImage imgA, imgB;
int frames = 150;     // total frames in the transition
int w = 3840, h = 2160; // set to your output resolution

void settings() {{ size(w, h, P2D); }}
void setup() {{ 
  surface.setTitle("Two-Image Crossfade");
  imgA = loadImage("A.jpg"); // PNG/JPG; PNG alpha is respected
  imgB = loadImage("B.jpg");
  imageMode(CORNER);
  frameRate(30);
}}

void draw() {{
  float t = constrain((float)frameCount / frames, 0, 1);
  // Draw A full
  pushStyle();
  tint(255, 255);
  image(imgA, 0, 0, width, height);
  // Draw B with alpha
  int alpha = int(255 * t);
  tint(255, alpha);
  image(imgB, 0, 0, width, height);
  popStyle();

  // save frames; stop when done
  saveFrame("out/frame####.png");
  if (frameCount >= frames) exit();
}}
```

**Notes**

- Place `A.jpg` and `B.jpg` in the sketch’s `data/` folder.
- PNG transparency in either image is preserved.
- For UHD sources, ensure the renderer is `P2D` (OpenGL). Close other GPU‑heavy apps.

## Better tonality: Gamma‑correct crossfade (GLSL)

For natural fades, interpolate in linear light. Below: a minimal fragment shader that converts sRGB → linear, mixes, then linear → sRGB.

```
// File: GammaCorrectCrossfade/GammaCorrectCrossfade.pde
PImage imgA, imgB;
PShader crossfade;
int frames = 150;
int w = 3840, h = 2160;

void settings() {{ size(w, h, P2D); }}
void setup() {{
  surface.setTitle("Gamma-Correct Crossfade");
  imgA = loadImage("A.jpg");
  imgB = loadImage("B.jpg");
  crossfade = loadShader("crossfade.frag");
  frameRate(30);
}}

void draw() {{
  float t = constrain((float)frameCount / frames, 0, 1);
  crossfade.set("t", t);
  crossfade.set("texA", imgA);
  crossfade.set("texB", imgB);
  shader(crossfade);
  image(imgA, 0, 0, width, height); // any quad; shader will sample both
  resetShader();
  saveFrame("out/frame####.png");
  if (frameCount >= frames) exit();
}}
```

```
// File: data/crossfade.frag
#ifdef GL_ES
precision mediump float;
precision mediump int;
#endif

uniform sampler2D texA;
uniform sampler2D texB;
uniform float t;
varying vec4 vertTexCoord;

// approximate sRGB <-> linear
vec3 srgb_to_linear(vec3 c) {{
  return pow(c, vec3(2.2));
}}
vec3 linear_to_srgb(vec3 c) {{
  return pow(c, vec3(1.0/2.2));
}}

void main() {{
  vec2 uv = vertTexCoord.st;
  vec4 a = texture2D(texA, uv);
  vec4 b = texture2D(texB, uv);

  // premultiply alpha to respect PNG transparency
  vec3 a_rgb = srgb_to_linear(a.rgb) * a.a;
  vec3 b_rgb = srgb_to_linear(b.rgb) * b.a;
  float a_a = a.a;
  float b_a = b.a;

  // interpolate premultiplied components
  vec3 mix_rgb = mix(a_rgb, b_rgb, t);
  float mix_a  = mix(a_a,  b_a,  t);

  // un-premultiply (avoid divide by zero)
  vec3 out_rgb = mix_a > 0.0 ? mix_rgb / mix_a : vec3(0.0);
  out_rgb = linear_to_srgb(out_rgb);
  gl_FragColor = vec4(out_rgb, mix_a);
}}
```

**Why this helps:** sRGB is non‑linear; blending there darkens mid‑tones. Linear‑light mixing preserves perceived brightness.

## Export to video with FFmpeg

```
# From the sketch's folder:
ffmpeg -r 30 -i out/frame%04d.png -s 3840x2160 -pix_fmt yuv420p -crf 18 -preset medium -c:v libx264 crossfade_uhd_30fps.mp4
```

| Option | What it does |
| --- | --- |
| `-r 30` | Assumes 30 fps for reading PNGs. |
| `-crf 18` | Quality target (lower = higher quality). 18–20 is visually good. |
| `-pix_fmt yuv420p` | Max compatibility. For ProRes/HQ masters, use `-c:v prores_ks -profile:v 3` and keep 10‑bit sources. |

## Going beyond a straight crossfade

### 1) Align first (Homography or landmarks)

If A and B share a planar subject (e.g., poster on wall), detect features (ORB/SIFT), match, solve homography, warp B → A, then crossfade. This reduces “double eyes”/ghosting.

### 2) Feature‑based morph (triangle mesh)

1. Pick corresponding points (eyes, nose, contour...); compute Delaunay triangulation on the mean of A & B points.
2. For each triangle, compute affine maps A→M<sub>t</sub> and B→M<sub>t</sub> (intermediate shape at `t`).
3. Warp both into M<sub>t</sub>, then alpha‑blend.

Implementation options: do triangle warps in Processing with `texture()` on three‑vertex meshes, or offload to a shader.

### 3) Optical‑flow morph (dense)

Use OpenCV (Farnebäck or RAFT) to estimate flow F from A→B. For frame `t`, sample A at `p − t*F(p)` (forward warp) or B at `p + (1−t)*F(p)`, then blend. Produces fluid “melting” transitions but needs robust flow and edge handling (holes, occlusions).

## Handling PNG alpha & UHD

- **Alpha:** Prefer premultiplied‑alpha math (as in the shader) to avoid dark fringes. Processing’s `tint()` path is premultiplied internally for PNGs.
- **UHD performance:** Keep everything on the GPU (`P2D` + shader). Avoid per‑pixel CPU loops at 4K if possible.
- **Color management:** If inputs carry profiles, aim to convert them to sRGB before ingestion to avoid surprises.

## Minimal per‑pixel version (CPU, illustrative)

Use only for learning or small images; for UHD, prefer the shader or `tint()` path.

```
// File: CPU_Lerp/CPU_Lerp.pde
PImage a,b,outImg;
int frames=150; int w=1920,h=1080;

void settings(){{ size(w,h,P2D); }}
void setup(){{ 
  a=loadImage("A.jpg"); b=loadImage("B.png");
  a.resize(w,h); b.resize(w,h);
  outImg = createImage(w,h,ARGB);
  frameRate(30);
}}

void draw(){{ 
  float t = constrain((float)frameCount/frames,0,1);
  a.loadPixels(); b.loadPixels(); outImg.loadPixels();
  for (int i=0;i<outImg.pixels.length;i++) {{
    int ca = a.pixels[i], cb = b.pixels[i];
    float aa = alpha(ca)/255.0, ab = alpha(cb)/255.0;
    float ra = red(ca), ga=green(ca), ba=blue(ca);
    float rb = red(cb), gb=green(cb), bb=blue(cb);
    // simple sRGB mix (not gamma-correct); premultiplied-ish
    float r = (1-t)*(ra*aa) + t*(rb*ab);
    float g = (1-t)*(ga*aa) + t*(gb*ab);
    float bl= (1-t)*(ba*aa) + t*(bb*ab);
    float aout = (1-t)*aa + t*ab;
    if (aout > 0) {{ r/=aout; g/=aout; bl/=aout; }}
    outImg.pixels[i] = color(r,g,bl, 255*aout);
  }}
  outImg.updatePixels();
  image(outImg,0,0);
  saveFrame("out/frame####.png");
  if (frameCount>=frames) exit();
}}
```

## FFmpeg one‑liner crossfade (no Processing)

If you just want a 2‑second crossfade between `A.jpg` and `B.jpg` at 30 fps:

```
ffmpeg -loop 1 -t 2 -i A.jpg -loop 1 -t 2 -i B.jpg -filter_complex "[0][1]xfade=transition=fade:duration=2:offset=0,format=yuv420p" -r 30 -crf 18 out.mp4
```

## Where to go next

- Add an on‑canvas slider to scrub `t` interactively; export when happy.
- Add easing (e.g., smoothstep, cubic) so the fade starts/ends gently.
- Combine with homography alignment for portraits, product spins, etc.
- Try multi‑band blending (Gaussian/Laplacian pyramids) for better seams.

Prepared: 2025-09-01 12:04:05 (Europe/London). Default output format: HTML. Designed for easy copy/paste into Apple Notes or GitHub.
