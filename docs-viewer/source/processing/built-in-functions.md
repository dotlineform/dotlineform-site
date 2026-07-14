---
doc_id: built-in-functions
title: built in functions
added_date: "2026-07-14 17:35"
last_updated: "2026-07-14 17:35"
parent_id: layer-blending2
---
# built in functions



```
What is better, to use built in functions like tint or to layer images pixel by pixel?

```

Short answer: **use built-ins when you can; drop to pixels only when you must.**
Here’s the trade-off for Processing (Java mode):

**When to use built-ins (tint(), image(), blend(), blendMode())**
	•	**Speed:** With the **P2D/P3D renderer**, these run on the GPU (textures), so UHD (3840×2160) blends are fast and avoid the cost of loadPixels()/updatePixels().
	•	**Simplicity:** Fewer bugs, fewer edge-cases (bounds, indexing).
	•	**Good fit for:** Normal alpha compositing, constant opacity stacking, and supported blend modes (e.g., MULTIPLY, SCREEN via blendMode()).

**When to do per-pixel loops**
	•	**Custom math:** If you need Photoshop-like modes not provided, weighted averages, per-channel logic, percentile auto-levels, etc.
	•	**Determinism/precision:** Exact control over order, math, and alpha handling.
	•	**Trade-off:** Slower (you touch ~8.3M pixels per UHD layer). loadPixels()/updatePixels() adds overhead; multiple passes scale linearly.

**Practical guidance for your UHD 3-image composite**
	•	If you’re just stacking with 50% opacity: **use built-ins** with P2D.
	•	If you later add custom auto-levels or bespoke modes: keep a **hybrid**—use built-ins for simple steps, switch to per-pixel only for the special step (or consider a shader).

⸻

**Example A — Fast, simple (GPU) using P2D + tint**

```


```


```
*// Renderer uses GPU; fast for UHD*
```


```

void settings() { size(3840, 2160, P2D); }
void setup() {
  PImage a = loadImage("image1.png");
  PImage b = loadImage("image2.jpg");
  PImage c = loadImage("image3.png");
  a.resize(width, height);
  b.resize(width, height);
  c.resize(width, height);

  
```


```
*// draw to an offscreen buffer if you like*
```


```

  PGraphics pg = createGraphics(width, height, P2D);
  pg.beginDraw();
  pg.imageMode(CORNER);

  
```


```
*// base*
```


```

  pg.tint(255, 255);       
```


```
*// 100% opaque*
```


```

  pg.image(a, 0, 0);

  
```


```
*// 50% over*
```


```

  pg.tint(255, 127);       
```


```
*// 127/255 ≈ 0.5*
```


```

  pg.image(b, 0, 0);

  
```


```
*// another 50% over*
```


```

  pg.tint(255, 127);
  pg.image(c, 0, 0);

  pg.endDraw();
  pg.save("composite.png");
  exit();
}

```


**Example B — Custom math (CPU) per-pixel**


```
PImage blendTwoAlpha(PImage base, PImage top, float opacity) {
  PImage out = createImage(base.width, base.height, ARGB);
  base.loadPixels(); top.loadPixels(); out.loadPixels();
  for (int i = 0; i < base.pixels.length; i++) {
    int cb = base.pixels[i], ct = top.pixels[i];
    float br = red(cb), bg = green(cb), bb = blue(cb);
    float tr = red(ct), tg = green(ct), tb = blue(ct);
    float ta = alpha(ct) / 255.0;          
```


```
*// PNG respects alpha; JPEG ≈ 1.0*
```


```

    float a  = constrain(ta * opacity, 0, 1);
    out.pixels[i] = color(
      br * (1 - a) + tr * a,
      bg * (1 - a) + tg * a,
      bb * (1 - a) + tb * a
    );
  }
  out.updatePixels();
  return out;
}

```


**Extra tips**
	•	**Switch renderer:** use size(…, P2D) for built-in speedups.
	•	**Reuse buffers:** if looping, reuse PGraphics/PImage to avoid allocations.
	•	**Shaders later:** if you need both speed and custom math, a small **GLSL shader** (via PShader) gives GPU performance with your exact blend formula.

Bottom line: for your current 3-image, 50% layering job, the **tint() + image() route with P2D** is the cleanest and fastest.
