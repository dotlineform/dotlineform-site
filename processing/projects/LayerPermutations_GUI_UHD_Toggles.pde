// LayerPermutations_GUI_UHD_Toggles.pde
// Folder-pick GUI + on-canvas toggles/sliders for UHD mode, strictness, greyscale,
// blend strategy, opacity, Auto Levels/Contrast, and clip percent.
// Includes CSV per-layer rules and manifest logging.
//
// Controls (left column):
// - SOURCE / OUTPUT selectors
// - START GENERATION
// - Checkboxes: UHD MODE, UHD STRICT, FORCE GREYSCALE, AUTO LEVELS, PER-CHANNEL (Auto Levels)
// - Cycle button: BLEND STRATEGY (SEQUENTIAL/AVERAGE)
// - Sliders: LAYER OPACITY (0..1), CLIP PERCENT (0..5%)
//
// Optional CSV: <SOURCE>/layer_rules.csv
// Manifest: <OUTPUT>/manifest.csv

import java.io.*;
import java.util.Arrays;
import java.util.Locale;

// Canvas ---------------------------------------------------------------------
int CANVAS_W = 1040;
int CANVAS_H = 660;

void settings(){ size(CANVAS_W, CANVAS_H); pixelDensity(displayDensity()); }
void setup(){
  surface.setTitle("Permutations — GUI Toggles");
  textFont(createFont("Arial", 14));
  setupUI();
}
void draw(){
  background(252);
  drawUI();
}

// State ----------------------------------------------------------------------
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
String statusMsg = "Pick SOURCE and OUTPUT, adjust options, then START.";

// Processing pipeline options (live-edited by UI)
boolean UHD_MODE = true;
final int UHD_W = 3840, UHD_H = 2160;
boolean UHD_STRICT = false;
boolean UHD_FORCE_GREYSCALE = true;

String BLEND_STRATEGY = "SEQUENTIAL"; // or "AVERAGE"
float  LAYER_OPACITY = 1.0;
boolean CYCLE_MODES = true;

boolean AUTO_LEVELS = true;
boolean AUTO_LEVELS_PER_CHANNEL = false; // false≈AutoContrast, true≈AutoLevels
float  AUTO_CLIP_PERCENT = 0.5;          // 0..5% (slider cap)

int MAX_PERMS = -1; // cap for testing; -1 = all
boolean RESIZE_TO_FIRST = false; // handled implicitly by UHD or normalization

String[] MODES = new String[]{ "MULTIPLY","SCREEN","OVERLAY","LIGHTEN","DARKEN" };

// CSV rules
class LayerRule { String mode; float opacity=Float.NaN; float weight=Float.NaN; }
HashMap<Integer,LayerRule> rules = new HashMap<Integer,LayerRule>();

// Manifest
File manifestFile; boolean manifestInitialized=false;

// Target size
int TARGET_W=-1, TARGET_H=-1;

// UI -------------------------------------------------------------------------
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
  String label; float minV,maxV; float v; int x,y,w,h; boolean dragging=false; int knobR=7;
  Slider(String label,float minV,float maxV,float v,int x,int y,int w,int h){
    this.label=label; this.minV=minV; this.maxV=maxV; this.v=v; this.x=x; this.y=y; this.w=w; this.h=h;
  }
  void draw(){
    fill(30); textAlign(LEFT,CENTER);
    String valStr = (maxV<=5.1 ? nf(v,0,2)+"%" : nf(v,0,2)); // for percent slider
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
  }
}

// UI instances
Btn btnSource, btnOutput, btnStart;
Checkbox cbUHD, cbStrict, cbGray, cbAuto, cbPerChannel;
Cycle cyStrategy;
Slider slOpacity, slClip;

void setupUI(){
  btnSource = new Btn("Select SOURCE…", 40, 80, 260, 42);
  btnOutput = new Btn("Select OUTPUT…", 40, 130, 260, 42);
  btnStart  = new Btn("START",          40, 185, 260, 50);

  cbUHD       = new Checkbox("UHD MODE (3840×2160)", 40, 260, UHD_MODE);
  cbStrict    = new Checkbox("UHD STRICT (fail if not UHD)", 40, 290, UHD_STRICT);
  cbGray      = new Checkbox("FORCE GREYSCALE", 40, 320, UHD_FORCE_GREYSCALE);
  cbAuto      = new Checkbox("AUTO LEVELS", 40, 350, AUTO_LEVELS);
  cbPerChannel= new Checkbox("PER-CHANNEL (Auto Levels)", 40, 380, AUTO_LEVELS_PER_CHANNEL);

  cyStrategy = new Cycle("BLEND STRATEGY", new String[]{ "SEQUENTIAL","AVERAGE" }, BLEND_STRATEGY.equals("SEQUENTIAL")?0:1, 40, 420, 260, 36);
  slOpacity  = new Slider("LAYER OPACITY", 0.00, 1.00, LAYER_OPACITY, 40, 470, 260, 20);
  slClip     = new Slider("CLIP PERCENT",  0.00, 5.00, AUTO_CLIP_PERCENT, 40, 520, 260, 20);
}

void drawUI(){
  // header
  fill(20); textAlign(LEFT,TOP); textSize(22);
  text("Permutation Composites — GUI Toggles", 40, 20);
  textSize(14); fill(60);
  text("Pick folders, set options, press START.", 40, 44);

  // left column controls
  btnSource.draw(); btnOutput.draw(); btnStart.enabled = (sourceDirPath!=null && outputDirPath!=null && phase==Phase.CONFIG); btnStart.draw();
  cbUHD.draw(); cbStrict.draw(); cbGray.draw(); cbAuto.draw(); cbPerChannel.draw();
  cyStrategy.draw(); slOpacity.draw(); slClip.draw();

  // right pane: paths + status
  fill(50); textAlign(LEFT,TOP); text("Source:", 340, 84); fill(0); text(safePath(sourceDirPath), 400, 84, width-440, 60);
  fill(50); text("Output:", 340, 134); fill(0); text(safePath(outputDirPath), 400, 134, width-440, 60);

  fill(30); String pfx = (phase==Phase.RUNNING)?"Working…":(phase==Phase.DONE?"Done:":(phase==Phase.ERROR?"Error:":"Status:"));
  text(pfx+" "+statusMsg, 340, 190, width-380, height-210);

  // live preview of current settings (textual)
  fill(50);
  text("Current settings:", 340, 340);
  String s = "";
  s += "UHD="+(UHD_MODE?"on":"off")+"  STRICT="+(UHD_STRICT?"on":"off")+"  GREY="+(UHD_FORCE_GREYSCALE?"on":"off")+"\n";
  s += "STRATEGY="+BLEND_STRATEGY+"  AL="+(AUTO_LEVELS?"on":"off")+"  PER-CH="+(AUTO_LEVELS_PER_CHANNEL?"on":"off")+"\n";
  s += "OPACITY="+nf(LAYER_OPACITY,0,2)+"  CLIP="+nf(AUTO_CLIP_PERCENT,0,2)+"%";
  text(s, 340, 360);
}

String safePath(String p){ return (p==null ? "—" : p); }

void mousePressed(){
  if (phase!=Phase.CONFIG) return;
  if (btnSource.isOver()) selectFolder("Select the SOURCE folder (images)", "sourceSelected");
  else if (btnOutput.isOver()) selectFolder("Select the OUTPUT folder (save here)", "outputSelected");
  else if (btnStart.enabled && btnStart.isOver()) startGeneration();
  else {
    if (cbUHD.isOver()) { cbUHD.value = !cbUHD.value; UHD_MODE = cbUHD.value; }
    else if (cbStrict.isOver()) { cbStrict.value = !cbStrict.value; UHD_STRICT = cbStrict.value; }
    else if (cbGray.isOver()) { cbGray.value = !cbGray.value; UHD_FORCE_GREYSCALE = cbGray.value; }
    else if (cbAuto.isOver()) { cbAuto.value = !cbAuto.value; AUTO_LEVELS = cbAuto.value; }
    else if (cbPerChannel.isOver()) { cbPerChannel.value = !cbPerChannel.value; AUTO_LEVELS_PER_CHANNEL = cbPerChannel.value; }
    else if (cyStrategy.isOver()) { cyStrategy.next(); BLEND_STRATEGY = cyStrategy.val(); }
    slOpacity.startDrag();
    slClip.startDrag();
  }
}
void mouseDragged(){
  if (phase!=Phase.CONFIG) return;
  slOpacity.drag();
  slClip.drag();
  LAYER_OPACITY = slOpacity.v;
  AUTO_CLIP_PERCENT = slClip.v;
}
void mouseReleased(){
  slOpacity.stopDrag();
  slClip.stopDrag();
}

void sourceSelected(File sel){ if (sel==null) return; sourceDir=sel; sourceDirPath=sel.getAbsolutePath(); statusMsg="Source: "+sourceDirPath; }
void outputSelected(File sel){ if (sel==null) return; outputDir=sel; outputDirPath=sel.getAbsolutePath(); statusMsg="Output: "+outputDirPath; }

// Pipeline -------------------------------------------------------------------
void startGeneration(){
  try{
    phase=Phase.RUNNING;
    statusMsg="Loading images…";
    images.clear(); names.clear(); perms.clear(); rules.clear(); manifestInitialized=false;
    int produced = 0;

    if (sourceDir==null || !sourceDir.isDirectory()) throw new RuntimeException("Invalid source folder.");
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
          TARGET_W = UHD_W; TARGET_H = UHD_H;
        }
        images.add(im);
        names.add(f.getName());
      }
    }
    if (images.size()<2) throw new RuntimeException("Need at least 2 images.");

    // If not UHD mode, normalize to first image
    if (!UHD_MODE){
      TARGET_W = images.get(0).width; TARGET_H = images.get(0).height;
      for (int i=0;i<images.size();i++){
        PImage src = images.get(i);
        if (src.width!=TARGET_W || src.height!=TARGET_H){
          PImage scaled = createImage(TARGET_W, TARGET_H, ARGB);
          scaled.copy(src,0,0,src.width,src.height,0,0,TARGET_W,TARGET_H);
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

    if (outputDir==null) throw new RuntimeException("Invalid output folder.");
    outputDir.mkdirs();
    manifestFile = new File(outputDir, "manifest.csv");
    initManifest();

    statusMsg="Processing "+perms.size()+" permutations…";
    for (int p=0;p<perms.size();p++){
      if (MAX_PERMS>0 && produced>=MAX_PERMS) break;

      int[] order = perms.get(p);
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
        out = autoLevelsPercentile(out, AUTO_LEVELS_PER_CHANNEL, AUTO_CLIP_PERCENT);
      }

      String ordStr = joinInt(order, "-");
      String autoStr = AUTO_LEVELS ? (AUTO_LEVELS_PER_CHANNEL? "AutoLevels":"AutoContrast")+"_clip"+nf(AUTO_CLIP_PERCENT,0,2) : "None";
      String fname = String.format("perm_%s__blend_%s__auto_%s.png", ordStr, BLEND_STRATEGY, autoStr);
      File outFile = new File(outputDir, fname);
      out.save(outFile.getAbsolutePath());
      produced++;

      // Manifest
      StringList srcFiles = new StringList();
      for (int idx : order) srcFiles.append(names.get(idx));
      appendManifestRow(fname, ordStr, BLEND_STRATEGY, modesStrForManifest, AUTO_LEVELS ? (AUTO_LEVELS_PER_CHANNEL?"AutoLevels":"AutoContrast") : "None", join(srcFiles.array(), ","));

      if (p % 25 == 0) statusMsg="Saved "+produced+" / "+perms.size()+"…";
    }

    phase=Phase.DONE;
    statusMsg="Wrote "+produced+" composite(s). Manifest: "+manifestFile.getAbsolutePath();
  } catch(Exception e){
    phase=Phase.ERROR;
    statusMsg="Failed: "+e.getMessage();
    e.printStackTrace();
  }
}

// Manifest helpers -----------------------------------------------------------
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

// Compositing ----------------------------------------------------------------
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

// Blending + Auto Levels -----------------------------------------------------
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
  clipPercent = constrain(clipPercent, 0, 5);
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

// Permutations + helpers -----------------------------------------------------
void permute(int[] arr,int l){
  if (l==arr.length-1){ perms.add(arr.clone()); return; }
  for (int i=l;i<arr.length;i++){ swap(arr,l,i); permute(arr,l+1); swap(arr,l,i); }
}
void swap(int[] a,int i,int j){ int t=a[i]; a[i]=a[j]; a[j]=t; }

boolean endsWithAny(String s,String[] suffixes){ for (String suf:suffixes) if (s.endsWith(suf)) return true; return false; }
String joinInt(int[] arr,String sep){ String[] ss=new String[arr.length]; for (int i=0;i<arr.length;i++) ss[i]=str(arr[i]); return join(ss, sep); }