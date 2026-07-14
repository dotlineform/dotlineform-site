// SimpleComposite3_UHD.pde
// Minimal example: 3 UHD images, blended at 50% opacity each.
// Source and output folders are hard-coded.

String sourceDir = "/Users/yourname/Pictures/source_uHD/";   // <-- change to your folder
String outputDir = "/Users/yourname/Pictures/output_uHD/";   // <-- change to your folder

PImage img1, img2, img3;

void setup() {
  size(3840, 2160);  // UHD canvas
  surface.setVisible(false);  // no display window

  // Load 3 images
  img1 = loadImage(sourceDir + "image1.png");
  img2 = loadImage(sourceDir + "image2.png");
  img3 = loadImage(sourceDir + "image3.png");

  // Ensure UHD and matching dimensions
  img1.resize(width, height);
  img2.resize(width, height);
  img3.resize(width, height);

  // Base image
  PImage composite = img1.copy();

  // Blend in second at 50%
  composite = blendTwo(composite, img2, 0.5);

  // Blend in third at 50%
  composite = blendTwo(composite, img3, 0.5);

  // Save result
  String outPath = outputDir + "composite.png";
  composite.save(outPath);
  println("Saved composite to: " + outPath);

  exit();
}

// Simple alpha blend (normal mode, opacity 0..1)
PImage blendTwo(PImage base, PImage top, float opacity) {
  PImage out = createImage(base.width, base.height, ARGB);
  base.loadPixels();
  top.loadPixels();
  out.loadPixels();
  for (int i = 0; i < base.pixels.length; i++) {
    color cb = base.pixels[i];
    color ct = top.pixels[i];
    float r = red(cb)   * (1 - opacity) + red(ct)   * opacity;
    float g = green(cb) * (1 - opacity) + green(ct) * opacity;
    float b = blue(cb)  * (1 - opacity) + blue(ct)  * opacity;
    out.pixels[i] = color(r, g, b);
  }
  out.updatePixels();
  return out;
}