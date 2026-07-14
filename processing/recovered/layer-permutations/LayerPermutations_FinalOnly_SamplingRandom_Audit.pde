// LayerPermutations_FinalOnly_SamplingRandom_Audit.pde
// Final-only build with sampling (Stride or Seeded Random), plus audit tools:
//   • PREPARE SELECTION — computes selected permutation indices without rendering
//   • On-canvas preview of first K selected (index + order)
//   • EXPORT SELECTED CSV — saves selected indices & orders for audit/repro
//
// Kept: UHD/strict/greyscale, blend strategies, Auto Levels/Contrast, CSV rules,
// manifest, First‑N cap (Final only), progress bar, final-only estimator.
//
// -----------------------------------------------------------------------------

import java.io.*;
import java.util.Arrays;
import java.util.Locale;
import java.util.Random;
import java.util.Collections;
import java.util.ArrayList;
import java.math.BigInteger;

// Canvas ---------------------------------------------------------------------
int CANVAS_W = 1160;
int CANVAS_H = 860;

void settings(){ size(CANVAS_W, CANVAS_H); pixelDensity(displayDensity()); }
void setup(){
  surface.setTitle("Permutation Composites — Final Only (Stride / Seeded Random) + Audit");
  textFont(createFont("Arial", 14));
  setupUI();
  recomputeEstimator();
}
void draw(){
  background(252);
  drawUI();
}

// --------------------------- State ------------------------------------------
ArrayList<PImage> images = new ArrayList<PImage>();
ArrayList<String> names  = new ArrayList<String>();
ArrayList<int[]> perms   = new ArrayList<int[]>();

// Folders & phase
String sourceDirPath = null;
String outputDirPath = null;
File   sourceDir = null;
File   outputDir = null;

enum Phase { CONFIG, RUNNING, DONE, ERROR }
Phase phase = Phase.CONFIG;
String statusMsg = "Pick SOURCE & OUTPUT, set options, PREPARE SELECTION if you want a CSV, then EXPORT FINAL.";

// Options (edited via UI)
boolean UHD_MODE = true;
final int UHD_W = 3840, UHD_H = 2160;
boolean UHD_STRICT = false;
boolean UHD_FORCE_GREYSCALE = true;

String BLEND_STRATEGY = "SEQUENTIAL"; // or "AVERAGE"
float  LAYER_OPACITY = 1.0;
boolean CYCLE_MODES = true;

boolean AUTO_LEVELS = true;
boolean AUTO_LEVELS_PER_CHANNEL = false; // false≈AutoContrast, true≈AutoLevels
float  AUTO_CLIP_PERCENT = 0.5f;         // 0..5%

// Final-only controls
int FINAL_FIRST_N   = -1;                // 0 or -1 = all

// Sampling controls
String SAMPLING_MODE = "STRIDE";         // STRIDE or RANDOM
int STRIDE_N        = 1;                 // 1..10 (when STRIDE)
float RANDOM_KEEP_PCT = 0.10;            // 1%..100% as 0.01..1.00 (when RANDOM)
int RANDOM_SEED = 12345;                 // reproducible (when RANDOM)

// Estimator settings
float THROUGHPUT_MPIXPS = 150; // adjustable slider (mega‑pixels per second)
int   EST_W = UHD_W;           // estimated base width
int   EST_H = UHD_H;           // estimated base height
int   EST_N = 0;               // estimated number of images in source
boolean EST_DIM_KNOWN = true;  // if false, show "unknown res" and assume UHD

// Manifest
File manifestFile; boolean manifestInitialized=false;

// CSV rules
class LayerRule { String mode; float opacity=Float.NaN; float weight=Float.NaN; }
HashMap<Integer,LayerRule> rules = new HashMap<Integer,LayerRule>();

// Progress state
boolean workerActive = false;
int workerTotal = 0;        // total permutations
int workerConsidered = 0;   // permutations considered after sampling
int workerLimit = 0;        // min(considered, firstN or all)
int workerDone = 0;

// Audit/preview of selected permutations
ArrayList<Integer> selectedIdxCache = new ArrayList<Integer>(); // selected indices (ordered)
int PREVIEW_FIRST_K = 50; // show first K rows in the table
boolean selectionPrepared = false;

// ------------------------------ UI ------------------------------------------
class Btn {
  String label; int x,y,w,h; boolean enabled=true;
  Btn(String label,int x,int y,int w,int h){ this.label=label; this.x=x; this.y=y; this.w=w; this.h=h; }
  void draw(){
    stroke(200);
    if (!enabled) fill(220);
    else if (isOver()) fill(240); else fill(250);
    rect(x,y,w,h,8);
    fill(30); textAlign(CENTER,CENTER);
    text(label, x+w/2, y+h/2);
  }
  boolean isOver(){ return mouseX>=x && mouseX<=x+w && mouseY>=y && mouseY<=y+h; }
}
class Checkbox {
  String label; int x,y; boolean value;
  Checkbox(String label,int x,int y,boolean v){ this.label=label; this.x=x; this.y=y; this.value=v; }
  void draw(){
    stroke(160); fill(255); rect(x,y,18,18,4);
    if (value){ line(x+4,y+10,x+8,y+14); line(x+8,y+14,x+14,y+4); }
    fill(30); textAlign(LEFT,CENTER); text(label, x+24, y+9);
  }
  boolean isOver(){ return mouseX>=x && mouseX<=x+18 && mouseY>=y && mouseY<=y+18; }
}
class Cycle {
  String label; String[] options; int idx; int x,y,w,h; boolean enabled=true;
  Cycle(String label,String[] options,int idx,int x,int y,int w,int h){
    this.label=label; this.options=options; this.idx=idx; this.x=x; this.y=y; this.w=w; this.h=h;
  }
  String val(){ return options[idx]; }
  void next(){ idx = (idx+1)%options.length; }
  void draw(){
    fill(30); textAlign(LEFT,CENTER); text(label, x, y-12);
    stroke(200); if (!enabled) fill(220); else if (isOver()) fill(240); else fill(250);
    rect(x,y,w,h,6);
    fill(20); textAlign(CENTER,CENTER); text(val(), x+w/2, y+h/2);
  }
  boolean isOver(){ return mouseX>=x && mouseX<=x+w && mouseY>=y && mouseY<=y+h; }
}
class Slider {
  String label; float minV,maxV; float v; int x,y,w,h; boolean dragging=false; int knobR=7; boolean percent=false; boolean integer=false;
  Slider(String label,float minV,float maxV,float v,int x,int y,int w,int h){
    this.label=label; this.minV=minV; this.maxV=maxV; this.v=v; this.x=x; this.y=y; this.w=w; this.h=h;
  }
  Slider asPercent(){ percent=true; return this; }
  Slider asInteger(){ integer=true; return this; }
  void draw(){
    fill(30); textAlign(LEFT,CENTER);
    String valStr;
    if (integer) valStr = str(int(round(v)));
    else if (percent) valStr = nf(v*100,0,0)+"%";
    else valStr = nf(v,0,2);
    text(label+"  "+valStr, x, y-12);
    stroke(200); line(x, y+h/2, x+w, y+h/2);
    float t = (v - minV) / (maxV - minV);
    int kx = x + int(t*w);
    noStroke(); fill(60); ellipse(kx, y+h/2, knobR*2, knobR*2);
  }
  boolean overKnob(){
    float t = (v - minV) / (maxV - minV);
    int kx = x + int(t*w);
    return dist(mouseX, mouseY, kx, y+h/2) <= knobR+2;
  }
  void startDrag(){ if (overKnob()) dragging=true; }
  void stopDrag(){ dragging=false; }
  void drag(){
    if (!dragging) return;
    float t = constrain((mouseX - x) / float(w), 0, 1);
    v = minV + t * (maxV - minV);
    if (integer) v = round(v);
  }
}

// Integer stepper
class Stepper {
  String label; int x,y,w,h; int value; int minV, maxV; boolean enabled=true;
  Btn minus, plus;
  Stepper(String label,int x,int y,int w,int h,int value,int minV,int maxV){
    this.label=label; this.x=x; this.y=y; this.w=w; this.h=h; this.value=value; this.minV=minV; this.maxV=maxV;
    minus = new Btn("-", x, y, h, h);
    plus  = new Btn("+", x+w-h, y, h, h);
  }
  void draw(){
    fill(30); textAlign(LEFT,CENTER); text(label, x, y-12);
    minus.enabled = enabled; plus.enabled = enabled;
    minus.draw(); plus.draw();
    stroke(200); fill(255);
    rect(x+minus.w+4, y, w-2*minus.w-8, h, 6);
    fill(20); textAlign(CENTER,CENTER);
    text(value, x+minus.w+4 + (w-2*minus.w-8)/2, y+h/2);
  }
  void click(){
    if (!enabled) return;
    if (minus.isOver()) value = max(minV, value-1);
    else if (plus.isOver()) value = min(maxV, value+1);
  }
}

// Controls
Btn btnSource, btnOutput, btnExport, btnPrepare, btnExportSelCSV;
Checkbox cbUHD, cbStrict, cbGray, cbAuto, cbPerChannel;
Cycle cyStrategy, cySampling;
Slider slOpacity, slClip, slThroughput, slRandPct, slSeed, slShowK;
Stepper stFinalN, stStrideN;

void setupUI(){
  btnSource  = new Btn("Select SOURCE…", 40, 80, 260, 42);
  btnOutput  = new Btn("Select OUTPUT…", 40, 130, 260, 42);
  btnPrepare = new Btn("PREPARE SELECTION", 40, 185, 260, 40);
  btnExportSelCSV = new Btn("EXPORT SELECTED CSV", 40, 230, 260, 40);
  btnExport  = new Btn("EXPORT FINAL",     40, 275, 260, 50);

  cbUHD       = new Checkbox("UHD MODE (3840×2160)", 40, 345, true);
  cbStrict    = new Checkbox("UHD STRICT (fail if not UHD)", 40, 375, false);
  cbGray      = new Checkbox("FORCE GREYSCALE", 40, 405, true);
  cbAuto      = new Checkbox("AUTO LEVELS", 40, 435, true);
  cbPerChannel= new Checkbox("PER-CHANNEL (Auto Levels)", 40, 465, false);

  cyStrategy = new Cycle("BLEND STRATEGY", new String[]{ "SEQUENTIAL","AVERAGE" }, 0, 40, 505, 260, 36);
  slOpacity  = new Slider("LAYER OPACITY", 0.00, 1.00, 1.00, 40, 555, 260, 20);
  slClip     = new Slider("CLIP PERCENT",  0.00, 0.05, 0.005, 40, 595, 260, 20);
  slThroughput = new Slider("THROUGHPUT (MPix/s)", 50, 500, 150, 40, 635, 260, 20).asInteger();

  // Sampling controls
  cySampling = new Cycle("SAMPLING MODE", new String[]{ "STRIDE", "RANDOM" }, 340, 84, 260, 32);
  stStrideN  = new Stepper("1‑in‑n (stride)",   340, 124, 200, 32, STRIDE_N, 1, 10);
  slRandPct  = new Slider("Random keep %", 0.01, 1.00, 0.10, 560, 124, 260, 20).asPercent();
  slSeed     = new Slider("Random SEED",   0, 999999, 12345, 560, 154, 260, 20).asInteger();

  stFinalN   = new Stepper("FIRST N (Final)",   340, 184, 200, 32, FINAL_FIRST_N<0?0:FINAL_FIRST_N,   0, 1000000);
  slShowK    = new Slider("Show first K in table", 5, 200, 50, 560, 184, 260, 20).asInteger();
}

void drawUI(){
  // header
  fill(20); textAlign(LEFT,TOP); textSize(22);
  text("Permutation Composites — Final Only (Stride / Seeded Random) + Audit", 40, 20);
  textSize(14); fill(60);
  text("Prepare & export selection CSV for audit/repro. Then EXPORT FINAL when ready.", 40, 44);

  // left column
  btnSource.draw(); btnOutput.draw();
  boolean canRun = (sourceDirPath!=null && outputDirPath!=null && phase!=Phase.RUNNING);
  btnPrepare.enabled = canRun;
  btnExportSelCSV.enabled = canRun && selectionPrepared;
  btnExport.enabled = canRun;
  btnPrepare.draw(); btnExportSelCSV.draw(); btnExport.draw();

  cbUHD.draw(); cbStrict.draw(); cbGray.draw(); cbAuto.draw(); cbPerChannel.draw();
  cyStrategy.draw(); slOpacity.draw(); slClip.draw(); slThroughput.draw();

  // right: paths
  fill(50); textAlign(LEFT,TOP); text("Source:", 340, 54); fill(0); text(safePath(sourceDirPath), 400, 54, width-440, 24);
  fill(50); text("Output:", 340, 74); fill(0); text(safePath(outputDirPath), 400, 74, width-440, 24);

  // Sampling controls
  cySampling.draw();
  boolean isStride = cySampling.val().equals("STRIDE");
  stStrideN.enabled = (phase!=Phase.RUNNING) && isStride;
  stFinalN.enabled  = (phase!=Phase.RUNNING);
  stStrideN.draw();
  slRandPct.draw();
  slSeed.draw();
  slShowK.draw();
  fill(80);
  text("Tips: PREPARE SELECTION computes the chosen permutations (no images). Export CSV for audit or review below.", 340, 214);

  // Status
  fill(30);
  String pfx = (phase==Phase.RUNNING)?"Working…":(phase==Phase.DONE?"Done:":(phase==Phase.ERROR?"Error:":"Status:"));
  text(pfx+" "+statusMsg, 340, 240, width-380, 40);

  // Progress bar
  if (phase==Phase.RUNNING && workerConsidered>0){
    int barX = 340, barY = 290, barW = width-380, barH = 24;
    stroke(200); fill(245); rect(barX, barY, barW, barH, 6);
    float t = constrain(workerDone / float(workerLimit>0?workerLimit:workerConsidered), 0, 1);
    noStroke(); fill(60); rect(barX, barY, int(barW*t), barH, 6);
    fill(30);
    text("FINAL  " + workerDone + " / " + (workerLimit>0?min(workerLimit, workerConsidered):workerConsidered) + " composites ("+SAMPLING_MODE+")", barX, barY+barH+8);
  }

  // Estimator Panel
  drawEstimatorPanel(340, 330, width-380, 160);

  // Selection Table
  drawSelectionTable(340, 500, width-380, 320);
}

String safePath(String p){ return (p==null ? "—" : p); }

void mousePressed(){
  if (phase==Phase.RUNNING) return;
  if (btnSource.isOver()) selectFolder("Select the SOURCE folder (images)", "sourceSelected");
  else if (btnOutput.isOver()) selectFolder("Select the OUTPUT folder (save here)", "outputSelected");
  else if (btnPrepare.enabled && btnPrepare.isOver()) { thread("prepareSelection"); }
  else if (btnExportSelCSV.enabled && btnExportSelCSV.isOver()) { exportSelectionCSV(); }
  else if (btnExport.enabled  && btnExport.isOver())  { thread("runGeneration"); }
  else {
    if (cbUHD.isOver()) { cbUHD.value=!cbUHD.value; UHD_MODE=cbUHD.value; recomputeEstimator(); }
    else if (cbStrict.isOver()) { cbStrict.value=!cbStrict.value; UHD_STRICT=cbStrict.value; }
    else if (cbGray.isOver()) { cbGray.value=!cbGray.value; UHD_FORCE_GREYSCALE=cbGray.value; }
    else if (cbAuto.isOver()) { cbAuto.value=!cbAuto.value; }
    else if (cbPerChannel.isOver()) { cbPerChannel.value=!cbPerChannel.value; }
    else if (cyStrategy.isOver()) { cyStrategy.next(); BLEND_STRATEGY=cyStrategy.val(); }
    else if (cySampling.isOver()) { cySampling.next(); SAMPLING_MODE=cySampling.val(); recomputeEstimator(); }
    slOpacity.startDrag(); slClip.startDrag(); slThroughput.startDrag(); slRandPct.startDrag(); slSeed.startDrag(); slShowK.startDrag();
    stFinalN.minus.click();   stFinalN.plus.click();
    stStrideN.minus.click();  stStrideN.plus.click();
  }
}
void mouseDragged(){
  if (phase==Phase.RUNNING) return;
  slOpacity.drag(); slClip.drag(); slThroughput.drag(); slRandPct.drag(); slSeed.drag(); slShowK.drag();
  LAYER_OPACITY = slOpacity.v;
  AUTO_CLIP_PERCENT = slClip.v; // fraction
  THROUGHPUT_MPIXPS = slThroughput.v;
  RANDOM_KEEP_PCT = slRandPct.v;
  RANDOM_SEED = int(slSeed.v);
  PREVIEW_FIRST_K = int(slShowK.v);
}
void mouseReleased(){
  slOpacity.stopDrag(); slClip.stopDrag(); slThroughput.stopDrag(); slRandPct.stopDrag(); slSeed.stopDrag(); slShowK.stopDrag();
  FINAL_FIRST_N   = (stFinalN.value<=0)   ? -1 : stFinalN.value;
  STRIDE_N        = max(1, min(10, stStrideN.value));
}

void sourceSelected(File sel){
  if (sel==null) return;
  sourceDir = sel; sourceDirPath = sel.getAbsolutePath();
  statusMsg = "Source: "+sourceDirPath;
  selectionPrepared = false;
  selectedIdxCache.clear();
  perms.clear();
  recomputeEstimator();
}
void outputSelected(File sel){ if (sel==null) return; outputDir=sel; outputDirPath=sel.getAbsolutePath(); statusMsg="Output: "+outputDirPath; }

// ------------------------------ Estimator (Final only) -----------------------
void recomputeEstimator(){
  EST_W = UHD_W; EST_H = UHD_H; EST_DIM_KNOWN = true;
  EST_N = 0;
  if (sourceDir==null || !sourceDir.isDirectory()){
    EST_DIM_KNOWN = UHD_MODE; // if UHD on, dimensions known; else unknown
    return;
  }
  File[] files = sourceDir.listFiles();
  if (files==null) return;
  Arrays.sort(files);
  String[] exts = {".png",".jpg",".jpeg"};
  String firstPath = null;
  for (File f: files){
    String nm = f.getName().toLowerCase(Locale.ROOT);
    if (endsWithAny(nm, exts)){
      EST_N++;
      if (firstPath==null) firstPath = f.getAbsolutePath();
    }
  }
  if (EST_N>0){
    if (UHD_MODE){
      EST_W = UHD_W; EST_H = UHD_H; EST_DIM_KNOWN = true;
    } else {
      PImage tmp = loadImage(firstPath);
      if (tmp!=null){ EST_W = tmp.width; EST_H = tmp.height; EST_DIM_KNOWN = true; }
      else { EST_W = UHD_W; EST_H = UHD_H; EST_DIM_KNOWN = false; }
    }
  }
}

void drawEstimatorPanel(int x,int y,int w,int h){
  // Frame
  stroke(210); fill(248); rect(x, y, w, h, 8);
  fill(20); textAlign(LEFT,TOP); textSize(16);
  text("Estimator — Final Output Only (tweak MPix/s to your machine)", x+12, y+10);
  textSize(14); fill(40);

  // n and permutations
  text("Images found (n): "+EST_N, x+12, y+40);
  String factStr = (EST_N<=12) ? factorialString(EST_N) : (EST_N+"!");
  text("Total permutations (n!): "+factStr, x+12, y+60);

  // Dimensions
  String dimStr = (EST_DIM_KNOWN? (EST_W+"×"+EST_H) : "unknown (assuming UHD)");
  text("Final size: "+dimStr, x+12, y+80);

  // Sampling
  int totalPerms = safeFactorialInt(EST_N, 2000000000); // clamp display
  int considered = 0;
  if (SAMPLING_MODE.equals("STRIDE")){
    considered = (STRIDE_N<=1 ? totalPerms : (totalPerms + (STRIDE_N-1))/STRIDE_N); // ceil
  } else {
    float pct = constrain(RANDOM_KEEP_PCT, 0.01, 1.0);
    considered = max(1, int(round(totalPerms * pct)));
  }
  int firstN = (FINAL_FIRST_N<0? considered : min(FINAL_FIRST_N, considered));
  text("Sampling: "+SAMPLING_MODE+(SAMPLING_MODE.equals("STRIDE")? "  n="+STRIDE_N : "  keep="+int(RANDOM_KEEP_PCT*100)+"%  seed="+RANDOM_SEED), x+12, y+100);
  text("After sampling: ~"+considered+" permutations  |  To render (First N): "+firstN, x+12, y+120);

  // Time model
  float mpixps = max(1, THROUGHPUT_MPIXPS);
  float autoMultiplier = AUTO_LEVELS ? 1.2 : 1.0;
  int L = max(1, EST_N);
  double pixelsPerImage = (double)EST_W*(double)EST_H;
  double secondsPerComposite = ((double)L * pixelsPerImage) / (mpixps*1e6) * autoMultiplier;
  double totalSeconds = secondsPerComposite * firstN;

  text("Throughput: "+int(mpixps)+" MPix/s   |   Auto‑Levels: "+(AUTO_LEVELS?"on (+20%)":"off"), x+12, y+140);
  text("Est. seconds/composite: "+nf((float)secondsPerComposite,1,2), x+12, y+160);
  text("Est. total time: "+fmtHMS(totalSeconds), x+12, y+180);
}

// ------------------------------ Selection Prepare & Table --------------------
void prepareSelection(){
  try{
    if (sourceDir==null) return;
    phase=Phase.RUNNING; statusMsg="Preparing selection (building permutations)…";
    selectedIdxCache.clear(); perms.clear();

    // Load only file names to count images/order; we don't need image pixels
    File[] files = sourceDir.listFiles();
    Arrays.sort(files);
    ArrayList<String> localNames = new ArrayList<String>();
    String[] exts = {".png",".jpg",".jpeg"};
    for (File f : files){
      String nm = f.getName().toLowerCase(Locale.ROOT);
      if (endsWithAny(nm, exts)) localNames.add(f.getName());
    }
    int n = localNames.size();
    if (n<2) throw new RuntimeException("Need at least 2 images.");
    // Build perms of indices 0..n-1
    int[] baseIdx = new int[n];
    for (int i=0;i<n;i++) baseIdx[i]=i;
    permute(baseIdx, 0);
    workerTotal = perms.size();

    // Sampling
    if (SAMPLING_MODE.equals("STRIDE")){
      for (int i=0; i<workerTotal; i++){ if (i % STRIDE_N == 0) selectedIdxCache.add(i); }
    } else {
      float pct = constrain(RANDOM_KEEP_PCT, 0.01, 1.0);
      int want = max(1, int(round(workerTotal * pct)));
      ArrayList<Integer> all = new ArrayList<Integer>();
      for (int i=0; i<workerTotal; i++) all.add(i);
      java.util.Random rng = new java.util.Random((long)RANDOM_SEED);
      Collections.shuffle(all, rng);
      for (int i=0; i<want; i++) selectedIdxCache.add(all.get(i));
      Collections.sort(selectedIdxCache);
    }

    // First N cap for table/export preview
    int considered = selectedIdxCache.size();
    workerConsidered = considered;
    workerLimit = (FINAL_FIRST_N<0 ? considered : min(FINAL_FIRST_N, considered));
    if (FINAL_FIRST_N>=0 && FINAL_FIRST_N<considered){
      // Trim cache to the firstN for clarity (CSV/export will also use FirstN)
      ArrayList<Integer> trimmed = new ArrayList<Integer>();
      for (int i=0;i<workerLimit;i++) trimmed.add(selectedIdxCache.get(i));
      selectedIdxCache = trimmed;
      workerConsidered = workerLimit;
    }

    selectionPrepared = true;
    phase=Phase.DONE;
    statusMsg = "Prepared "+workerConsidered+" selected permutations ("+SAMPLING_MODE+"). You can export CSV or run Final.";
  } catch(Exception e){
    phase=Phase.ERROR;
    statusMsg = "Prepare failed: "+e.getMessage();
    e.printStackTrace();
  }
}

void drawSelectionTable(int x,int y,int w,int h){
  stroke(210); fill(248); rect(x, y, w, h, 8);
  fill(20); textAlign(LEFT,TOP); textSize(16);
  text("Selection Preview (first "+min(PREVIEW_FIRST_K, max(0, selectedIdxCache.size()))+" rows)", x+12, y+10);
  textSize(13); fill(40);
  if (!selectionPrepared){
    fill(80); text("No selection prepared. Click PREPARE SELECTION to compute indices (no images rendered).", x+12, y+40);
    return;
  }
  int rows = min(PREVIEW_FIRST_K, selectedIdxCache.size());
  int rowY = y+40;
  fill(50); text("perm_index", x+12, rowY); text("order (indices into sorted source files)", x+120, rowY);
  rowY += 18;
  for (int i=0; i<rows; i++){
    int permIndex = selectedIdxCache.get(i);
    int[] order = perms.get(permIndex);
    fill(20); text(nf(permIndex, 1), x+12, rowY);
    text(joinInt(order, "-"), x+120, rowY);
    rowY += 16;
    if (rowY > y+h-20) break;
  }
}

void exportSelectionCSV(){
  try{
    if (!selectionPrepared || outputDir==null) { statusMsg="Prepare selection first and set OUTPUT."; return; }
    outputDir.mkdirs();
    File out = new File(outputDir, "selection_indices.csv");
    PrintWriter pw = new PrintWriter(new FileWriter(out, false));
    // header
    pw.println("perm_index,order,sampling_mode,stride_n,random_keep_pct,random_seed,first_n_applied");
    // rows
    for (int i=0; i<selectedIdxCache.size(); i++){
      int permIndex = selectedIdxCache.get(i);
      int[] order = perms.get(permIndex);
      String orderStr = joinInt(order, "-");
      String mode = SAMPLING_MODE;
      String strideStr = (SAMPLING_MODE.equals("STRIDE") ? str(STRIDE_N) : "");
      String pctStr = (SAMPLING_MODE.equals("RANDOM") ? nf(RANDOM_KEEP_PCT*100,0,0) : "");
      String seedStr = (SAMPLING_MODE.equals("RANDOM") ? str(RANDOM_SEED) : "");
      String firstNStr = (FINAL_FIRST_N<0 ? "all" : str(FINAL_FIRST_N));
      pw.println(permIndex+","+orderStr+","+mode+","+strideStr+","+pctStr+","+seedStr+","+firstNStr);
    }
    pw.flush(); pw.close();
    statusMsg = "Exported selection CSV: "+out.getAbsolutePath();
  } catch(Exception e){
    statusMsg = "CSV export failed: "+e.getMessage();
    e.printStackTrace();
  }
}

// ------------------------------ Worker Thread (Final Rendering) --------------
void runGeneration(){
  try{
    if (sourceDir==null || outputDir==null) return;
    phase=Phase.RUNNING; workerDone=0;
    statusMsg = "FINAL: loading images…";

    // Load images
    images.clear(); names.clear(); perms.clear(); rules.clear(); manifestInitialized=false;
    File[] files = sourceDir.listFiles();
    Arrays.sort(files);
    String[] exts = {".png",".jpg",".jpeg"};
    for (File f : files){
      String nm = f.getName().toLowerCase(Locale.ROOT);
      if (endsWithAny(nm, exts)){
        PImage im = loadImage(f.getAbsolutePath());
        if (im==null) continue;

        if (UHD_MODE){
          if (UHD_STRICT){
            if (im.width!=UHD_W || im.height!=UHD_H) throw new RuntimeException("Non-UHD input: "+f.getName());
          } else {
            if (im.width!=UHD_W || im.height!=UHD_H){
              PImage scaled = createImage(UHD_W, UHD_H, ARGB);
              scaled.copy(im,0,0,im.width,im.height,0,0,UHD_W,UHD_H);
              im = scaled;
            }
          }
          if (UHD_FORCE_GREYSCALE) im.filter(GRAY);
        }
        images.add(im);
        names.add(f.getName());
      }
    }
    if (images.size()<2) throw new RuntimeException("Need at least 2 images.");

    // Base size
    int BASE_W = UHD_MODE ? UHD_W : images.get(0).width;
    int BASE_H = UHD_MODE ? UHD_H : images.get(0).height;

    // Normalize (if not UHD strict)
    if (!UHD_MODE){
      for (int i=0;i<images.size();i++){
        PImage src = images.get(i);
        if (src.width!=BASE_W || src.height!=BASE_H){
          PImage scaled = createImage(BASE_W, BASE_H, ARGB);
          scaled.copy(src,0,0,src.width,src.height,0,0,BASE_W,BASE_H);
          images.set(i, scaled);
        }
      }
    }

    statusMsg="Loading CSV rules (optional)…";
    File csvRules = new File(sourceDir, "layer_rules.csv");
    rules.clear();
    if (csvRules.exists()){
      Table t = loadTable(csvRules.getAbsolutePath(), "header,csv");
      if (t!=null){
        for (TableRow row : t.rows()){
          int layer = row.getInt("layer"); if (layer<=0) continue;
          LayerRule r = new LayerRule();
          String m = row.getString("mode"); if (m!=null) r.mode = m.trim().toUpperCase(Locale.ROOT);
          String op = row.getString("opacity"); if (op!=null && op.length()>0) r.opacity = row.getFloat("opacity");
          String wt = row.getString("weight"); if (wt!=null && wt.length()>0) r.weight = row.getFloat("weight");
          rules.put(layer, r);
        }
      }
    }

    statusMsg="Building permutations…";
    int n = images.size();
    int[] baseIdx = new int[n];
    for (int i=0;i<n;i++) baseIdx[i]=i;
    permute(baseIdx, 0);
    workerTotal = perms.size();

    // Sampling (reuse prepared selection if available and matches current settings)
    ArrayList<Integer> selectedIdx = new ArrayList<Integer>();
    if (selectionPrepared){
      // Use cached selection that already has First N applied
      for (int v : selectedIdxCache) selectedIdx.add(v);
    } else {
      if (SAMPLING_MODE.equals("STRIDE")){
        for (int i=0; i<workerTotal; i++){ if (i % STRIDE_N == 0) selectedIdx.add(i); }
      } else {
        float pct = constrain(RANDOM_KEEP_PCT, 0.01, 1.0);
        int want = max(1, int(round(workerTotal * pct)));
        ArrayList<Integer> all = new ArrayList<Integer>();
        for (int i=0; i<workerTotal; i++) all.add(i);
        java.util.Random rng = new java.util.Random((long)RANDOM_SEED);
        Collections.shuffle(all, rng);
        for (int i=0; i<want; i++) selectedIdx.add(all.get(i));
        Collections.sort(selectedIdx);
      }
      // First N
      int considered = selectedIdx.size();
      workerConsidered = considered;
      workerLimit = (FINAL_FIRST_N<0 ? considered : min(FINAL_FIRST_N, considered));
      if (FINAL_FIRST_N>=0 && FINAL_FIRST_N<considered){
        ArrayList<Integer> trimmed = new ArrayList<Integer>();
        for (int i=0;i<workerLimit;i++) trimmed.add(selectedIdx.get(i));
        selectedIdx = trimmed;
      }
    }
    workerConsidered = selectedIdx.size();
    workerLimit = workerConsidered;

    // Prepare output
    outputDir.mkdirs();
    manifestFile = new File(outputDir, "manifest.csv");
    initManifest();

    statusMsg = "FINAL: processing "+workerLimit+" of "+workerTotal+" permutations ("+SAMPLING_MODE+")…";
    int produced = 0;
    for (int p=0; p<workerLimit; p++){
      int permIndex = selectedIdx.get(p);
      int[] order = perms.get(permIndex);
      PImage out;
      String modesStrForManifest = "N/A";

      if (BLEND_STRATEGY.equals("AVERAGE")){
        out = averageComposite(order);
      } else {
        StringList usedModes = new StringList();
        out = sequentialComposite(order, usedModes);
        modesStrForManifest = usedModes.join("-");
      }

      if (AUTO_LEVELS){
        out = autoLevelsPercentile(out, AUTO_LEVELS_PER_CHANNEL, AUTO_CLIP_PERCENT*100.0);
      }

      String ordStr = joinInt(order, "-");
      String autoStr = AUTO_LEVELS ? (AUTO_LEVELS_PER_CHANNEL? "AutoLevels":"AutoContrast")+"_clip"+nf(AUTO_CLIP_PERCENT*100,0,2)+"pct" : "None";
      String samplingTag = (SAMPLING_MODE.equals("STRIDE"))
                           ? "__stride_"+STRIDE_N
                           : "__randpct_"+nf(RANDOM_KEEP_PCT*100,0,0)+"_seed_"+RANDOM_SEED;
      String fname = String.format("perm_%s__blend_%s__auto_%s%s.png", ordStr, BLEND_STRATEGY, autoStr, samplingTag);
      File outFile = new File(outputDir, fname);
      out.save(outFile.getAbsolutePath());
      produced++;

      // Manifest
      StringList srcFiles = new StringList();
      for (int idx : order) srcFiles.append(names.get(idx));
      appendManifestRow(fname, ordStr, BLEND_STRATEGY, modesStrForManifest, AUTO_LEVELS ? (AUTO_LEVELS_PER_CHANNEL?"AutoLevels":"AutoContrast") : "None", join(srcFiles.array(), ","));

      workerDone = produced;
    }

    phase=Phase.DONE;
    statusMsg = "FINAL: wrote "+workerDone+" composite(s). Manifest: "+manifestFile.getAbsolutePath();
  } catch(Exception e){
    phase=Phase.ERROR;
    statusMsg="Failed: "+e.getMessage();
    e.printStackTrace();
  }
}

// ------------------------------ Manifest ------------------------------------
void initManifest(){
  try{
    if (!manifestFile.exists()){
      PrintWriter pw = new PrintWriter(new FileWriter(manifestFile, true));
      pw.println("filename,order,strategy,modes,auto_levels,source_files");
      pw.flush(); pw.close();
    }
    manifestInitialized=true;
  } catch(IOException e){ println("Manifest init error: "+e.getMessage()); }
}
void appendManifestRow(String filename,String order,String strategy,String modes,String autoLevels,String sourceFiles){
  if (!manifestInitialized) return;
  try{
    PrintWriter pw = new PrintWriter(new FileWriter(manifestFile, true));
    pw.println(csvEscape(filename)+","+csvEscape(order)+","+csvEscape(strategy)+","+csvEscape(modes)+","+csvEscape(autoLevels)+","+csvEscape(sourceFiles));
    pw.flush(); pw.close();
  } catch(IOException e){ println("Manifest write error: "+e.getMessage()); }
}
String csvEscape(String s){
  if (s==null) return "";
  s = s.replace("\"","\"\"");
  if (s.indexOf(',')>=0 || s.indexOf('"')>=0 || s.indexOf('\n')>=0 || s.indexOf('\r')>=0) return "\""+s+"\"";
  return s;
}

// ------------------------------ Compositing ---------------------------------
PImage sequentialComposite(int[] order, StringList usedModesOut){
  PImage out = images.get(order[0]).copy();
  usedModesOut.append("BASE");
  for (int li=1; li<order.length; li++){
    int layerPos = li+1;
    PImage top = images.get(order[li]);
    String mode = null;
    float opacity = LAYER_OPACITY;
    if (rules.containsKey(layerPos)){
      LayerRule r = rules.get(layerPos);
      if (r.mode!=null && r.mode.length()>0) mode = r.mode;
      if (!Float.isNaN(r.opacity)) opacity = r.opacity;
    }
    if (mode==null) mode = CYCLE_MODES ? MODES[(li-1)%MODES.length] : MODES[0];
    usedModesOut.append(mode);
    out = blendTwo(out, top, mode, opacity);
  }
  return out;
}

PImage averageComposite(int[] order){
  int w = images.get(0).width, h = images.get(0).height;
  PImage out = createImage(w,h,RGB);
  out.loadPixels();
  int n = order.length;
  float[] weights = new float[n];
  for (int li=0; li<n; li++){
    int layerPos = li+1;
    float wv = 1.0;
    if (rules.containsKey(layerPos) && !Float.isNaN(rules.get(layerPos).weight)) wv = max(0, rules.get(layerPos).weight);
    weights[li] = wv;
  }
  float sumW=0; for (float wv: weights) sumW+=wv;
  if (sumW<=0){ for (int i=0;i<n;i++) weights[i]=1.0/n; } else { for (int i=0;i<n;i++) weights[i]/=sumW; }

  float[] ar = new float[w*h], ag = new float[w*h], ab = new float[w*h];
  for (int li=0; li<n; li++){
    PImage layer = images.get(order[li]);
    float wv = weights[li];
    layer.loadPixels();
    for (int i=0;i<layer.pixels.length;i++){
      int c=layer.pixels[i];
      ar[i]+=red(c)*wv; ag[i]+=green(c)*wv; ab[i]+=blue(c)*wv;
    }
  }
  for (int i=0;i<out.pixels.length;i++){
    out.pixels[i] = color(constrain(ar[i],0,255), constrain(ag[i],0,255), constrain(ab[i],0,255));
  }
  out.updatePixels();
  return out;
}

// Blending + Auto Levels
PImage blendTwo(PImage base, PImage top, String mode, float opacity){
  PImage out = createImage(base.width, base.height, ARGB);
  base.loadPixels(); top.loadPixels(); out.loadPixels();
  int len = base.pixels.length;
  for (int i=0;i<len;i++){
    int cb=base.pixels[i], ct=top.pixels[i];
    float br=red(cb), bg=green(cb), bb=blue(cb), ba=alpha(cb)/255.0;
    float tr=red(ct), tg=green(ct), tb=blue(ct), ta=alpha(ct)/255.0;
    float aTop = constrain(ta*opacity, 0,1);
    float rBlend = applyMode(br,tr,mode);
    float gBlend = applyMode(bg,tg,mode);
    float bBlend = applyMode(bb,tb,mode);
    float r = (1-aTop)*br + aTop*rBlend;
    float g = (1-aTop)*bg + aTop*gBlend;
    float b = (1-aTop)*bb + aTop*bBlend;
    float a = 255*(ba + aTop - ba*aTop);
    out.pixels[i] = color(constrain(r,0,255), constrain(g,0,255), constrain(b,0,255), constrain(a,0,255));
  }
  out.updatePixels();
  return out;
}
float applyMode(float b,float t,String mode){
  float r;
  if (mode.equals("NORMAL")) r=t;
  else if (mode.equals("MULTIPLY")) r=(b*t)/255.0;
  else if (mode.equals("SCREEN"))   r=255 - ((255-b)*(255-t))/255.0;
  else if (mode.equals("OVERLAY"))  r=(b<128)?(2*b*t/255.0):(255 - 2*(255-b)*(255-t)/255.0);
  else if (mode.equals("LIGHTEN"))  r=max(b,t);
  else if (mode.equals("DARKEN"))   r=min(b,t);
  else if (mode.equals("DIFFERENCE")) r=abs(b-t);
  else if (mode.equals("ADD"))      r=b+t;
  else if (mode.equals("SUBTRACT")) r=b-t;
  else if (mode.equals("SOFTLIGHT")){ float tN=t/255.0; r=(1-2*tN)*b*b/255.0 + 2*tN*b; }
  else r=t;
  return constrain(r,0,255);
}

PImage autoLevelsPercentile(PImage img, boolean perChannel, float clipPercent){
  clipPercent = max(0, min(clipPercent, 20)); // expects percent
  int[] histR=new int[256], histG=new int[256], histB=new int[256], histAll=new int[256];
  img.loadPixels();
  int N=img.pixels.length;
  for (int i=0;i<N;i++){
    int c=img.pixels[i];
    int r=int(red(c)), g=int(green(c)), b=int(blue(c));
    histR[r]++; histG[g]++; histB[b]++;
    int y=int(0.2126*r + 0.7152*g + 0.0722*b);
    histAll[y]++;
  }
  if (perChannel){
    int[] lo=new int[3], hi=new int[3];
    lo[0]=percentileLow(histR,N,clipPercent); hi[0]=percentileHigh(histR,N,clipPercent);
    lo[1]=percentileLow(histG,N,clipPercent); hi[1]=percentileHigh(histG,N,clipPercent);
    lo[2]=percentileLow(histB,N,clipPercent); hi[2]=percentileHigh(histB,N,clipPercent);
    return rescalePerChannel(img,lo,hi);
  } else {
    int lo=percentileLow(histAll,N,clipPercent);
    int hi=percentileHigh(histAll,N,clipPercent);
    return rescaleUnified(img,lo,hi);
  }
}
int percentileLow(int[] hist,int totalPixels,float clipPercent){
  int clip=int(totalPixels*(clipPercent/100.0)), cum=0;
  for (int v=0; v<256; v++){ cum+=hist[v]; if (cum>=clip) return v; }
  return 0;
}
int percentileHigh(int[] hist,int totalPixels,float clipPercent){
  int clip=int(totalPixels*(clipPercent/100.0)), cum=0;
  for (int v=255; v>=0; v--){ cum+=hist[v]; if (cum>=clip) return v; }
  return 255;
}
PImage rescalePerChannel(PImage img,int[] lo,int[] hi){
  PImage out=createImage(img.width,img.height,RGB);
  img.loadPixels(); out.loadPixels();
  for (int i=0;i<img.pixels.length;i++){
    int c=img.pixels[i];
    float r=mapClamp(red(c),  lo[0],hi[0],0,255);
    float g=mapClamp(green(c),lo[1],hi[1],0,255);
    float b=mapClamp(blue(c), lo[2],hi[2],0,255);
    out.pixels[i]=color(r,g,b);
  }
  out.updatePixels(); return out;
}
PImage rescaleUnified(PImage img,int lo,int hi){
  PImage out=createImage(img.width,img.height,RGB);
  img.loadPixels(); out.loadPixels();
  for (int i=0;i<img.pixels.length;i++){
    int c=img.pixels[i];
    float r=mapClamp(red(c),  lo,hi,0,255);
    float g=mapClamp(green(c),lo,hi,0,255);
    float b=mapClamp(blue(c), lo,hi,0,255);
    out.pixels[i]=color(r,g,b);
  }
  out.updatePixels(); return out;
}
float mapClamp(float v,float inMin,float inMax,float outMin,float outMax){
  if (inMax<=inMin+1e-6) return v;
  float t=(v-inMin)/(inMax-inMin); t=constrain(t,0,1);
  return outMin + t*(outMax-outMin);
}

// ------------------------------ Permutations --------------------------------
void permute(int[] arr,int l){
  if (l==arr.length-1){ perms.add(arr.clone()); return; }
  for (int i=l;i<arr.length;i++){ swap(arr,l,i); permute(arr,l+1); swap(arr,l,i); }
}
void swap(int[] a,int i,int j){ int t=a[i]; a[i]=a[j]; a[j]=t; }

boolean endsWithAny(String s,String[] suffixes){ for (String suf:suffixes) if (s.endsWith(suf)) return true; return false; }
String joinInt(int[] arr,String sep){ String[] ss=new String[arr.length]; for (int i=0;i<arr.length;i++) ss[i]=str(arr[i]); return join(ss, sep); }

// Pretty format time
String fmtHMS(double seconds){
  long s = (long)seconds;
  long h = s/3600; s%=3600;
  long m = s/60; s%=60;
  return String.format(java.util.Locale.UK, "%dh %dm %ds", h, m, s);
}