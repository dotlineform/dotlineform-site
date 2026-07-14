---
doc_id: route-map-optical-flow
title: "Route Map: From Layering Images in Processing → Optical-Flow Interpolation"
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# Route Map: From Simple Layering → Optical‑Flow Interpolation (Processing)

Prepared

—

2025-09-02 16:09:39 (Europe/London)

Starting from a simple Processing code to layer images together, provide a route map to using optical flow to generate interpolation.

This roadmap moves in tested increments. Each milestone is small, shippable, and adds exactly one new concept. Copy/paste-friendly snippets are included.

## Milestone 0 — Baseline: Layer two images

**Goal:** Draw A then B with adjustable alpha. Establish file paths, output folder, and sequential saves.

```
// M0_LayerTwo.pde
PImage a,b;
void settings() { size(1920,1080,P2D); }
void setup() {
  a=loadImage("A.jpg"); b=loadImage("B.jpg");
  imageMode(CORNER);
  saveFrame("out/m0_####.png"); // sanity: creates out/
}
void draw() {
  background(0);
  image(a,0,0,width,height);
  tint(255,128); image(b,0,0,width,height); noTint();
  saveFrame("out/m0_####.png"); exit();
}
```

Checks:

files load, output path exists, no scaling artefacts. If images differ in size, scale them consistently.

## Milestone 1 — True crossfade with easing

**Goal:** Animate alpha from 0→1 with easing and save frames. This already makes a simple “interpolation”.

```
// M1_Crossfade.pde
PImage a,b; int frames=60;
void settings() { size(1920,1080,P2D); }
void setup() { a=loadImage("A.jpg"); b=loadImage("B.jpg"); frameRate(30); }
float ease(float t) { return t*t*(3-2*t); } // smoothstep
void draw() {
  float t = constrain((float)frameCount/frames,0,1);
  background(0);
  tint(255,255); image(a,0,0,width,height);
  tint(255,int(255*t)); image(b,0,0,width,height); noTint();
  saveFrame("out/m1_####.png"); if (frameCount>=frames) exit();
}
```

## Milestone 2 — Gamma‑correct crossfade (GLSL)

**Why:** Linear‑light blending preserves brightness; sRGB alpha lerp looks muddy.

```
// M2_GammaCrossfade.pde
PImage a,b; PShader sh; int frames=60;
void settings(){ size(1920,1080,P2D); }
void setup(){ a=loadImage("A.jpg"); b=loadImage("B.jpg"); sh=loadShader("crossfade.frag"); frameRate(30);}
void draw(){ float t=constrain((float)frameCount/frames,0,1); sh.set("t",t); sh.set("texA",a); sh.set("texB",b); shader(sh); image(a,0,0,width,height); resetShader(); saveFrame("out/m2_####.png"); if(frameCount>=frames) exit(); }
```

```
// data/crossfade.frag
#ifdef GL_ES
precision mediump float; precision mediump int;
#endif
uniform sampler2D texA, texB; uniform float t; varying vec4 vertTexCoord;
vec3 s2l(vec3 c){return pow(c,vec3(2.2));} vec3 l2s(vec3 c){return pow(c,vec3(1.0/2.2));}
void main(){ vec2 uv=vertTexCoord.st; vec4 a=texture2D(texA,uv), b=texture2D(texB,uv);
  vec3 ar=s2l(a.rgb)*a.a, br=s2l(b.rgb)*b.a; float aa=a.a, ba=b.a;
  vec3 mr=mix(ar,br,t); float ma=mix(aa,ba,t);
  vec3 out_rgb = ma>0.0 ? mr/ma : vec3(0.0); gl_FragColor=vec4(l2s(out_rgb),ma); }
```

## Milestone 3 — Consistent canvas sizing (FIT/FILL/STRETCH)

**Why:** Optical flow assumes consistent coordinates. Normalize image sizes once upfront.

```
// helper
PImage toCanvas(PImage src,int cw,int ch,String mode,int bg){
  PGraphics g=createGraphics(cw,ch,P2D); g.beginDraw(); g.background(bg);
  float cwH=cw/(float)ch, ar=src.width/(float)src.height; float x=0,y=0,w=cw,h=ch;
  if("FILL".equals(mode)){ if(ar>cwH){h=ch; w=h*ar; x=(cw-w)/2;} else {w=cw; h=w/ar; y=(ch-h)/2;} }
  else if("FIT".equals(mode)){ if(ar>cwH){w=cw; h=w/ar; y=(ch-h)/2;} else {h=ch; w=h*ar; x=(cw-w)/2;} }
  g.image(src,x,y,w,h); g.endDraw(); return g.get();
}
```

## Milestone 4 — Flow‑free “morph”: geometric alignment (optional)

Before flow, try **homography alignment** for near‑planar scenes to reduce ghosting. (This step benefits from OpenCV, but you can skip if you want pure Processing.)

## Milestone 5 — Dense optical flow (Horn–Schunck, pure Processing)

**Goal:** Compute A→B flow on a pyramid (coarse→fine). This is your first true motion field.

```
// Outline
float[][][] flow = computeHSFlowMultiScale(imgA,imgB, levels=3, alpha=40.0, iters=80);
float[][] u = flow[0], v = flow[1];
```

At each scale: compute gradients (Sobel), iterate HS update with a smoothness prior (box‑average neighbors). Upscale flow to the next finer level and refine.

## Milestone 6 — Warping with bilinear sampling + gamma‑correct premult blend

**Goal:** For time `t`, sample A at `(x−t·u, y−t·v)` and B at `(x+(1−t)·u, y+(1−t)·v)`; blend in linear light.

```
// Pseudocode
for each pixel (x,y):
  ax = x - t*u[y][x]; ay = y - t*v[y][x];
  bx = x + (1-t)*u[y][x]; by = y + (1-t)*v[y][x];
  Ca = bilinear(A, ax, ay); Cb = bilinear(B, bx, by);
  mix = gammaPremultBlend(Ca, Cb, t);
```

## Milestone 7 — Per‑pair caching

**Why:** Flow is expensive; compute once per pair, save as binary. Resume later without recomputing.

```
// binary layout: [int w][int h][w*h floats u][w*h floats v]
saveFlow(u,v,"out/flows/flow_000123.bin");
float[][][] uv = loadFlow(...);
```

## Milestone 8 — GPU warper (performance)

**Goal:** Keep warping on the GPU for UHD‑scale runs. Pack (u,v) into an RG texture with a per‑pair `flowScale`.

```
// CPU: pack [-max,max] -> [0,255] in RG
int R = int(((u/max)*0.5+0.5)*255); int G = int(((v/max)*0.5+0.5)*255);
// Shader decodes to pixel offsets, converts to UV using imgSize.
```

**Tip:** Disable mipmaps for the flow texture to avoid ringing. For maximum precision, use float textures (OpenGL only).

## Milestone 9 — Quality upgrades

- **Forward–backward consistency:** compute A→B and B→A; down‑weight mismatched regions (occlusions).
- **Hole filling:** inpaint small gaps with median/bilateral guided by edges.
- **Multi‑band compositing:** blend warped A/B across a Laplacian pyramid to hide seams.
- **Easing:** non‑linear time ramps (smoothstep, cubic) for more natural motion.

## Milestone 10 — Batch pipeline (many images → slow‑motion)

1. Normalize each source to the canvas (Milestone 3).
2. For each adjacent pair, *load cached flow* or *compute & cache* (Milestone 5/7).
3. Generate `INTER_FRAMES` using CPU or GPU warper (Milestones 6/8).
4. Write sequential PNGs; `manifest.csv` tracks pair→frames mapping.
5. Stitch with FFmpeg:

```
ffmpeg -r 25 -i out/frame%06d.png -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p slow_morph_25fps.mp4
```

## Minimal decision tree

| Constraint | Pick | Why |
| --- | --- | --- |
| Planar scene? | +homography align | Reduces ghosting before any morphing. |
| Need quick baseline? | Gamma crossfade | Zero flow; good tonality. |
| Pure Processing only? | Horn–Schunck | All‑Java, portable. |
| UHD or long sequences? | GPU warper | Fast per‑frame renders. |

## Grab‑and‑go building blocks

- **Crossfade shader:** see Milestone 2 (data/crossfade.frag).
- **Pure‑Processing HS flow:** use the *OpticalFlowMorphHS.pde* code you already downloaded.
- **Batch (CPU flow + cache):** *BatchImageInterpolator_Flow.pde*.
- **Batch (GPU warper):** *BatchImageInterpolator_FlowGPU.pde* + *data/morph_flow.frag*.

You can implement the entire stack incrementally without changing file formats: PNG frames in, PNG frames out, FFmpeg at the end.
