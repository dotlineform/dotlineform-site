/**
 * EngramStarter.pde
 * Processing starter sketch with Substrate · Emergence · Experience classes.
 * Batch-oriented (static) renderer: draw() runs once by default.
 *
 * Usage:
 *  - Place CSV/JSON manifests in the data/ folder.
 *  - Adjust params and paths below.
 *  - Run to produce a single composite image into /out.
 */

Substrate substrate;
Emergence emergence;
Experience experience;

SubstrateParams substrateParams;
EmergenceParams emergenceParams;
ExperienceParams experienceParams;

void settings() {
  // Use settings() if you want variable-driven size(). See Processing reference.
  size(1920, 1080, P2D);
}

void setup() {
  smooth(4);
  surface.setTitle("Engram Starter");
  
  // --- Default parameters (edit as needed) ---
  substrateParams = new SubstrateParams();
  emergenceParams = new EmergenceParams();
  experienceParams = new ExperienceParams();
  
  // Example paths (relative to sketch folder)
  substrateParams.sourceDir = sketchPath("source");
  substrateParams.maskDir   = sketchPath("masks");
  substrateParams.outDir    = sketchPath("out");
  experienceParams.manifestCsvPath  = "manifest_rules.csv";   // in data/
  experienceParams.manifestJsonPath = "manifest_rules.json";  // in data/
  
  // Init classes
  substrate  = new Substrate(this, substrateParams);
  emergence  = new Emergence(this, emergenceParams);
  experience = new Experience(this, experienceParams);
  
  // Load assets/rules (no-ops until you implement)
  substrate.loadAssets();
  emergence.applyGroupRules();
  experience.readManifests();
  
  // We only want a single static render by default
  noLoop();
}

void draw() {
  background(10);
  // Example pipeline (stubs)
  substrate.deposit();
  emergence.morphLatent();
  experience.compose(substrate, emergence);
  
  // Export one composite to disk (implement inside Experience)
  experience.exportPNG("engrams_output.png");
  
  // Optional: write manifest/log after export
  experience.writeManifest();
}
