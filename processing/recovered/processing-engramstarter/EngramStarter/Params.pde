/**
 * Params.pde — parameter structs with safe defaults.
 */

class SubstrateParams {
  float depositionGain = 0.08;
  int   kernelSize     = 3;
  String depositionMode = "ADD"; // ADD|MULTIPLY|SCREEN (you implement)
  long  rngSeed        = 12345L;
  
  String sourceDir     = "";
  String maskDir       = "";
  String outDir        = "";
  boolean use16BitPNG  = false;
}

class EmergenceParams {
  String glyphType     = "spiral"; // e.g., circle|cross|spiral|tree
  int    symmetry      = 4;
  int    recursionDepth= 2;
  float  noiseScale    = 0.015;
  String groupRulesPath = "group_rules.json"; // in data/
}

class ExperienceParams {
  String strategy = "SEQUENTIAL"; // or AVERAGE, SJT, STRIDE, etc.
  String manifestCsvPath  = "manifest_rules.csv";
  String manifestJsonPath = "manifest_rules.json";
  
  int targetWidth  = 1920;
  int targetHeight = 1080;
  
  String[] maskSubset = {}; // e.g., {"edges","interestPoints"}
  float threshold   = 0.55;
  float ghostDecay  = 0.92;
}
