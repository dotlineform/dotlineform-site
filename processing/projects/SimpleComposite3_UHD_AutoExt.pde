// SimpleComposite3_UHD_AutoExt.pde
// Minimal example: 3 UHD images blended at 50% opacity each.
// Source/output folders are hard-coded. Each image can be PNG (with alpha) or JPEG.
// If PNG has transparency, it's respected (alpha * opacity).

String sourceDir = "/Users/yourname/Pictures/source_uHD/";   // <-- change to your folder
String outputDir = "/Users/yourname/Pictures/output_uHD/";   // <-- change to your folder

PImage img1, img2, img3;

void setup() {
  size(3840, 2160);  // UHD canvas
  surface.setVisible(false);  // run headless

  // Load 3 images by base name, accepting .png/.jpg/.jpeg
  img1 = loadEither(sourceDir, "image1");
  img2 = loadEither(sourceDir, "image2");
  img3 = loadEither(sourceDir, "image3");

  // Ensure UHD and matching dimensions
  img1.resize(width, height);
  img2.resize(width, height);
  img3.resize(width, height);

  // Start with first image as base
  PImage composite = img1.copy();

  // Blend second at 50% (respect top-image alpha if present)
  composite = blendTwoAlpha(composite, img2, 0.5);

  // Blend third at 50% (respect top-image alpha if present)
  composite = blendTwoAlpha(composite, img3, 0.5);

  // Save result
  String outPath = outputDir + "composite.png";
  composite.save(outPath);
  println("Saved composite to: " + outPath);

  exit();
}

// Try loading basename with .png, .jpg, .jpeg (in that order). Error if not found.
PImage loadEither(String dir, String base) {
  String[] exts = {".png", ".jpg", ".jpeg"};
  for (int i = 0; i < exts.length; i++) {
    String path = dir + base + exts[i];
    PImage im = loadImage(path);
    if (im != null) {
      println("Loaded: " + path);
      return im;
    }
  }
  throw new RuntimeException("Could not find " + base + " as .png/.jpg/.jpeg in " + dir);
}

// Alpha-aware normal blend:
// topContribution = (topAlpha * userOpacity), then lerp base->top by that factor.
PImage blendTwoAlpha(PImage base, PImage top, float userOpacity) {
  PImage out = createImage(base.width, base.height, ARGB);
  base.loadPixels();
  top.loadPixels();
  out.loadPixels();

  for (int i = 0; i < base.pixels.length; i++) {
    int cb = base.pixels[i];
    int ct = top.pixels[i];

    float br = red(cb),   bg = green(cb),  bb = blue(cb);
    float tr = red(ct),   tg = green(ct),  tb = blue(ct);
    float ta = alpha(ct) / 255.0; // 0..1 for PNGs; 1.0 for JPEGs (Processing loads as opaque)

    float a = constrain(ta * userOpacity, 0, 1);

    float r = br * (1 - a) + tr * a;
    float g = bg * (1 - a) + tg * a;
    float b = bb * (1 - a) + tb * a;

    out.pixels[i] = color(r, g, b);
  }

  out.updatePixels();
  return out;
}