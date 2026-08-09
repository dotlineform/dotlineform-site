// QRNG Divination — v3.1
// Adds: Manjushri mode auto-load (36 pairs CSV) and pair label display in mo mode.

import processing.data.*;
import java.util.*;
import java.net.*;
import java.text.SimpleDateFormat;
import java.io.PrintWriter;

String API_URL = "https://qrng.anu.edu.au/API/jsonIid?length=64&type=uint8";

enum Mode { ICHING, MO }
Mode mode = Mode.ICHING;

boolean autoRefresh = false;
boolean loggingOn = false;
String currentQuestion = "";

int refreshIntervalMs = 10000;
int lastRefresh = 0;

int[] bytesPool = new int[0];
int poolIdx = 0;
boolean usedQRNG = false;
String sourceMsg = "Source: QRNG (ANU)";
String statusMsg = "Ready";

// Iching state
int[] lineVals = new int[6]; // 6,7,8,9
boolean[] yang = new boolean[6];
boolean[] change = new boolean[6];
boolean[] yangResult = new boolean[6];
int hexIndex = 0;
int hexIndexResult = -1;

// mo state
int die1 = 0, die2 = 0, dieSum = 0;

// Manjushri mapping and table
String[] syllables = {"A","RA","PA","TSA","NA","DHI"}; // 1..6
class PairRow {
  String label, outcome, advice, remedy, notes;
  PairRow(String l,String o,String a,String r,String n){label=l; outcome=o; advice=a; remedy=r; notes=n;}
}
HashMap<String, PairRow> manjushriPairs = new HashMap<String, PairRow>();
boolean manjushriLoaded = false;

String[] hexNames;
PrintWriter logWriter;

void setup(){
  size(900, 820);
  surface.setTitle("QRNG Divination — I Ching & mo (v3.1)");
  textAlign(LEFT, TOP);
  textFont(createFont("Inter, Helvetica, Arial, Sans-Serif", 14));
  hexNames = loadHexNames();
  loadManjushriPairs();
  initLog();
  newReading();
}

void draw(){
  background(247);
  drawHeader();
  if(mode==Mode.ICHING){
    drawHexagram(130, 210, yang, change, "Primary", hexIndex);
    if(hexIndexResult >= 0){
      drawHexagram(560, 210, yangResult, new boolean[6], "Resulting", hexIndexResult);
    }
    drawFooterIching();
  } else {
    drawMoPanel();
  }
  drawBottomBar();
  if(autoRefresh && millis() - lastRefresh > refreshIntervalMs){
    newReading();
    lastRefresh = millis();
  }
}

void drawHeader(){
  fill(15); textSize(22);
  text("QRNG Divination — I Ching × mo", 24, 24);
  textSize(14); fill(60);
  text("Mode: " + (mode==Mode.ICHING ? "I Ching (hexagrams)" : "Tibetan mo (dice)")
       + "   |   SPACE=new  R=auto  M=mode  L=logging  Q=question  S=screenshot", 24, 56);
  fill(40);
  text(statusMsg, 24, 78);
  text(sourceMsg, 24, 96);
  if(currentQuestion!=null && currentQuestion.length()>0){
    fill(0); text("Question: " + currentQuestion, 24, 118);
  }
}

void drawHexagram(float x, float y, boolean[] lines, boolean[] changing, String label, int idx){
  fill(30); textSize(16);
  text(label + (idx>=0? " — #"+(idx+1)+"  "+shortName(idx):""), x, y-32);
  float w = 250, h = 18, gap = 20;
  for(int i=0;i<6;i++){
    int lineIdx = i;
    float yy = y + (5-i)*(h+gap);
    boolean yangLine = lines[lineIdx];
    boolean isChanging = changing[lineIdx];
    if(yangLine){
      fill(20); noStroke();
      rect(x, yy, w, h, 3);
      if(isChanging){
        noFill(); stroke(255); strokeWeight(2);
        rect(x+4, yy+4, w-8, h-8, 2);
        strokeWeight(1); noStroke();
      }
    } else {
      fill(20); noStroke();
      float seg = (w - 24)/2;
      rect(x, yy, seg, h, 3);
      rect(x + seg + 24, yy, seg, h, 3);
      if(isChanging){
        fill(255);
        rect(x + seg + 10, yy+4, 4, h-8);
        rect(x + seg + 10 + 6, yy+4, 4, h-8);
      }
    }
  }
}

void drawFooterIching(){
  float y = height - 210;
  fill(30); textSize(16);
  text("Reading (I Ching)", 24, y);
  textSize(14);
  text("Lines (bottom→top): " + formatLines(lineVals), 24, y+24);
  if(hexIndexResult>=0){
    text("Result: #" + (hexIndexResult+1) + "  " + shortName(hexIndexResult), 24, y+44);
  }
  textSize(12); fill(80);
  text("Names are short labels only. Consult your translation for texts.", 24, y+72);
}

void drawMoPanel(){
  float x = 120, y = 210;
  fill(30); textSize(18); text("Tibetan mo — two dice (2–12)", x, y-40);
  textSize(14); fill(40);
  String s1 = syllables[constrain(die1,1,6)-1];
  String s2 = syllables[constrain(die2,1,6)-1];
  String key = s1 + "-" + s2;
  text("Die 1: "+die1+" ("+s1+")    Die 2: "+die2+" ("+s2+")    Sum: "+dieSum+"    Pair: "+s1+"–"+s2, x, y);
  drawDie(x, y+30, die1);
  drawDie(x+120, y+30, die2);

  // guidance box
  float gx = x + 240, gy = y+10, gw = 480, gh = 170;
  stroke(220); fill(255); rect(gx, gy, gw, gh, 12);
  fill(20); textSize(15);
  text("Lineage guidance (Manjushri mode)", gx+12, gy+10);
  textSize(13); fill(40);
  PairRow row = manjushriPairs.get(key);
  if(row!=null){
    text("Outcome: " + nz(row.outcome), gx+12, gy+34, gw-24, 22);
    text("Advice: " + nz(row.advice),  gx+12, gy+60, gw-24, 48);
    text("Remedy: " + nz(row.remedy),  gx+12, gy+112, gw-24, 48);
  } else {
    text("No pair entry found. Edit data/manjushri_mo_lineage_template.csv", gx+12, gy+34);
  }

  textSize(12); fill(60);
  String foot = manjushriLoaded ? "Loaded Manjushri CSV ("+manjushriPairs.size()+" pairs)." : "No Manjushri CSV found; only numeric sum shown.";
  text(foot, x, y+150);
}

String nz(String s){ return (s==null||s.length()==0) ? "—" : s; }

void drawDie(float x, float y, int value){
  float s = 90;
  fill(255); stroke(180);
  rect(x, y, s, s, 12);
  fill(20); noStroke();
  float[][] p = {{0.25,0.25},{0.5,0.25},{0.75,0.25},{0.25,0.5},{0.5,0.5},{0.75,0.5},{0.25,0.75},{0.5,0.75},{0.75,0.75}};
  int[][] mapping = {{4},{0,8},{0,4,8},{0,2,6,8},{0,2,4,6,8},{0,2,3,5,6,8}};
  int idx = constrain(value,1,6) - 1;
  for(int id : mapping[idx]){
    float cx = x + p[id][0]*s, cy = y + p[id][1]*s;
    ellipse(cx, cy, 12, 12);
  }
}

void drawBottomBar(){
  float y = height - 60;
  stroke(226); line(0, y-10, width, y-10);
  fill(40); textSize(12);
  text("Logging: " + (loggingOn? "ON":"OFF") + "  |  Auto: " + (autoRefresh? "ON":"OFF") + "  |  Save: S  |  Mode: M  |  Question: Q", 24, y);
}

void keyPressed(){
  if(key==' '){
    newReading();
  } else if(key=='r' || key=='R'){
    autoRefresh = !autoRefresh;
    statusMsg = autoRefresh ? "Auto-refresh: ON" : "Auto-refresh: OFF";
  } else if(key=='s' || key=='S'){
    String ts = timestamp("_");
    saveFrame("qrng_cast_"+ts+".png");
    statusMsg = "Saved screenshot.";
  } else if(key=='m' || key=='M'){
    mode = (mode==Mode.ICHING? Mode.MO : Mode.ICHING);
    statusMsg = "Mode: " + (mode==Mode.ICHING? "I Ching" : "mo");
    newReading();
  } else if(key=='l' || key=='L'){
    loggingOn = !loggingOn;
    statusMsg = loggingOn ? "Logging: ON" : "Logging: OFF";
  } else if(key=='q' || key=='Q'){
    String s = javax.swing.JOptionPane.showInputDialog("Enter question (optional):", currentQuestion);
    if(s!=null) currentQuestion = s;
  }
}

void newReading(){
  usedQRNG = false;
  if(mode==Mode.ICHING){
    ensurePool(32);
    for(int i=0;i<6;i++){
      int b0 = nextBit(), b1 = nextBit(), b2 = nextBit();
      int sum = b0 + b1 + b2;
      int val = (sum==0)?6 : (sum==3)?9 : (sum==1)?7 : 8;
      lineVals[i] = val;
      yang[i] = (val==7 || val==9);
      change[i] = (val==6 || val==9);
    }
    hexIndex = computeHexIndex(yang);
    yangResult = Arrays.copyOf(yang, 6);
    for(int i=0;i<6;i++) if(change[i]) yangResult[i] = !yangResult[i];
    hexIndexResult = any(change)? computeHexIndex(yangResult) : -1;
  } else {
    die1 = sampleDie();
    die2 = sampleDie();
    dieSum = die1 + die2;
  }
  statusMsg = usedQRNG ? "New cast from QRNG." : "New cast (PRNG fallback).";
  sourceMsg = usedQRNG ? "Source: QRNG (ANU)" : "Source: PRNG fallback";
  lastRefresh = millis();
  if(loggingOn) appendLog();
}

int sampleDie(){
  int v=0;
  do{
    ensurePool(1);
    v = (nextBit()<<2) | (nextBit()<<1) | nextBit(); // 0..7
  }while(v<1 || v>6);
  return v;
}

boolean any(boolean[] a){ for(boolean b : a) if(b) return true; return false; }

int computeHexIndex(boolean[] lines){
  int idx = 0;
  for(int i=0;i<6;i++) if(lines[i]) idx |= (1<<i);
  return idx;
}

String formatLines(int[] vals){
  String s = "";
  for(int i=0;i<6;i++){ s += vals[i]; if(i<5) s+="-"; }
  return s;
}

String[] loadHexNames(){
  try{
    JSONArray arr = loadJSONArray("hex_names.json");
    String[] out = new String[arr.size()];
    for(int i=0;i<arr.size();i++) out[i] = arr.getString(i);
    return out;
  } catch(Exception e){ return new String[64]; }
}

String shortName(int idx){
  if(hexNames==null || idx<0 || idx>=hexNames.length) return "";
  String full = hexNames[idx];
  int p = full.indexOf("·");
  return p>0 ? full.substring(p+1).trim() : full;
}

void loadManjushriPairs(){
  manjushriPairs.clear();
  try{
    Table t = loadTable("manjushri_mo_lineage_template.csv", "header");
    for(TableRow r : t.rows()){
      try{
        String fs = r.getString("first_syllable");
        String ss = r.getString("second_syllable");
        String key = fs + "-" + ss;
        String label = r.getString("label");
        String outcome = r.getString("outcome");
        String advice = r.getString("advice");
        String remedy = r.getString("remedy_note");
        String notes = r.getString("notes");
        manjushriPairs.put(key, new PairRow(label,outcome,advice,remedy,notes));
      }catch(Exception ex){}
    }
    manjushriLoaded = manjushriPairs.size()>0;
  }catch(Exception e){
    manjushriLoaded = false;
  }
}

void ensurePool(int minBytes){
  int unreadBits = bytesPool.length*8 - poolIdx;
  if(unreadBits >= minBytes*8) return;
  int[] more = fetchQRNGu8(64);
  if(more != null && more.length>0){
    usedQRNG = true;
    int[] remainder;
    if(poolIdx < bytesPool.length*8){
      int bytesLeft = (bytesPool.length*8 - poolIdx + 7)/8;
      remainder = new int[bytesLeft];
      for(int i=0;i<bytesLeft;i++){
        int src = poolIdx/8 + i;
        remainder[i] = (src < bytesPool.length) ? bytesPool[src] : 0;
      }
    } else remainder = new int[0];
    int[] merged = new int[remainder.length + more.length];
    int p=0; for(int v : remainder) merged[p++] = v;
    for(int v : more) merged[p++] = v;
    bytesPool = merged; poolIdx = 0;
  } else {
    usedQRNG = false;
    bytesPool = new int[Math.max(minBytes, 16)];
    poolIdx = 0;
    Random r = new Random();
    for(int i=0;i<bytesPool.length;i++) bytesPool[i] = r.nextInt(256);
  }
}

int nextBit(){
  if(poolIdx>=bytesPool.length*8) ensurePool(16);
  int byteIdx = poolIdx/8, bitIdx = poolIdx%8;
  int bit = (bytesPool[byteIdx] >> bitIdx) & 1;
  poolIdx++;
  return bit;
}

int[] fetchQRNGu8(int length){
  try{
    String url = API_URL.replace("length=64", "length="+length);
    JSONObject obj = loadJSONObject(url);
    if(obj==null) return null;
    JSONArray arr = obj.getJSONArray("data");
    int[] out = new int[arr.size()];
    for(int i=0;i<arr.size();i++) out[i] = arr.getInt(i);
    return out;
  }catch(Exception e){ return null; }
}

void initLog(){
  try{
    String path = sketchPath("data/log.csv");
    boolean exists = new java.io.File(path).exists();
    logWriter = new PrintWriter(new java.io.FileWriter(path, true));
    if(!exists){
      logWriter.println("timestamp,mode,question,hex_index,hex_index_result,lines,die1,die2,sum,source");
      logWriter.flush();
    }
  }catch(Exception e){
    println("Log init failed: "+e);
  }
}

void appendLog(){
  if(logWriter==null) return;
  String ts = timestamp("-");
  String src = usedQRNG ? "QRNG" : "PRNG";
  if(mode==Mode.ICHING){
    logWriter.println(ts+",ICHING,"+escapeCsv(currentQuestion)+","+(hexIndex+1)+","+(hexIndexResult>=0? (hexIndexResult+1):"")+","+formatLines(lineVals)+",,,,"+src);
  } else {
    logWriter.println(ts+",MO,"+escapeCsv(currentQuestion)+",,,,"+die1+","+die2+","+dieSum+","+src);
  }
  logWriter.flush();
}

String timestamp(String sep){
  Calendar c = Calendar.getInstance();
  return nf(c.get(Calendar.YEAR),4)+sep+nf(c.get(Calendar.MONTH)+1,2)+sep+nf(c.get(Calendar.DAY_OF_MONTH),2)+sep
         +nf(c.get(Calendar.HOUR_OF_DAY),2)+sep+nf(c.get(Calendar.MINUTE),2)+sep+nf(c.get(Calendar.SECOND),2);
}

String escapeCsv(String s){
  if(s==null) return "";
  if(s.indexOf(',')>=0 || s.indexOf('"')>=0){
    s = s.replace("\"","\"\"");
    return "\""+s+"\"";
  }
  return s;
}
