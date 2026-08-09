/**
 * Experience.pde — rendered output (compose, toggles, export, manifest logging).
 * Links to modern engram neuroscience: selective reactivation via mask toggles.
 */

class Experience {
  PApplet p;
  ExperienceParams params;
  
  // State (skeleton)
  Table manifestCSV;
  JSONObject manifestJSON;
  ArrayList<String> log = new ArrayList<String>();
  
  Experience(PApplet parent, ExperienceParams params) {
    this.p = parent;
    this.params = params;
  }
  
  void readManifests() {
    // CSV (optional)
    // manifestCSV = loadTable(params.manifestCsvPath, "header,csv");
    
    // JSON (optional)
    // manifestJSON = loadJSONObject(params.manifestJsonPath);
  }
  
  void compose(Substrate sub, Emergence em) {
    // TODO: composite sub.traceBuffer + sources/masks into p.g
    // e.g., draw sub.traceBuffer → apply em.perlinDisplace() → overlay sources
  }
  
  void toggleMasks(String[] subset) {
    // TODO: apply a subset of masks for “recall” variations
  }
  
  void thresholdReveal(float t) {
    // TODO: adaptive threshold reveal
  }
  
  void exportPNG(String filename) {
    // Ensure output folder exists
    File out = new File(substituteNull(params != null ? params.manifestCsvPath : "out"), "ignore"); // placeholder to get sketch folder
    // Simpler: use explicit outDir from Substrate if desired
    String outDir = sketchPath("../out");
    File od = new File(outDir);
    od.mkdirs();
    
    // Save current frame buffer
    save(outDir + "/" + filename);
    
    log.add("Exported: " + filename + " @ " + new java.util.Date());
  }
  
  void writeManifest() {
    // TODO: write a simple run log (CSV or JSON) into /out
    // Example: saveStrings
    String outDir = sketchPath("../out");
    String[] lines = log.toArray(new String[0]);
    saveStrings(outDir + "/run_log.txt", lines);
  }
  
  // Helper to get sketchPath from within class
  String sketchPath(String rel) {
    return p.sketchPath(rel);
  }
  
  // Helper for null
  String substituteNull(String s, String def) {
    return s == null ? def : s;
  }
}
