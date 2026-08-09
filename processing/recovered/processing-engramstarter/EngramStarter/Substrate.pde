/**
 * Substrate.pde — material layer (buffers, masks, palettes).
 * Linkage to Semon's engram idea: imprint/ecphory via stateful buffers.
 */

class Substrate {
  PApplet p;
  SubstrateParams params;
  
  // State (skeleton)
  PGraphics traceBuffer;
  ArrayList<PImage> sources = new ArrayList<PImage>();
  ArrayList<PImage> masks   = new ArrayList<PImage>();
  
  Substrate(PApplet parent, SubstrateParams params) {
    this.p = parent;
    this.params = params;
    p.randomSeed(params.rngSeed);
  }
  
  void loadAssets() {
    // TODO: load images from params.sourceDir and params.maskDir
    // Example:
    // File dir = new File(params.sourceDir);
    // for (File f : dir.listFiles()) { if (f.getName().toLowerCase().endsWith(".png") || f.getName().toLowerCase().endsWith(".jpg")) { sources.add(p.loadImage(f.getAbsolutePath())); } }
    
    // Init buffers
    traceBuffer = p.createGraphics(p.width, p.height, P2D);
  }
  
  void deposit() {
    // TODO: accumulate “imprints” into traceBuffer
    // Example approach:
    // - draw selected source image with low alpha onto traceBuffer
    // - apply kernel-based blur/erode/dilate if desired
  }
  
  void erodeDilate() {
    // TODO: morphological operations on traceBuffer
  }
  
  void persist() {
    // TODO: save traceBuffer as an intermediate (ecphory support)
  }
  
  void restore() {
    // TODO: restore previous trace state
  }
}
