
// Processing I Ching with real-time QRNG (ANU) — Java mode
// UI: SPACE = new reading; 'R' = toggle auto-refresh; 'S' = save PNG
// Requires Internet to hit the ANU QRNG JSON API; falls back to PRNG if network fails.

import processing.data.*;
import java.util.*;
import java.net.*;

String API_URL = "https://qrng.anu.edu.au/API/jsonIid?length=64&type=uint8"; // returns JSON with 'data' array
int[] bytesPool = new int[0];
int poolIdx = 0;

int[] lineVals = new int[6]; // each: 6,7,8,9
boolean[] yang = new boolean[6]; // current hexagram lines (bottom->top)
boolean[] change = new boolean[6]; // which lines change
boolean[] yangResult = new boolean[6]; // resulting hexagram lines
int hexIndex = 0;
int hexIndexResult = -1;
String[] hexNames;

boolean autoRefresh = false;
int refreshIntervalMs = 10000;
int lastRefresh = 0;
String statusMsg = "Ready";
String sourceMsg = "Source: QRNG (ANU)";
boolean usedQRNG = false;

void setup(){
  size(720, 720);
  surface.setTitle("I Ching × QRNG — Processing");
  textAlign(LEFT, TOP);
  textFont(createFont("Inter, Helvetica, Arial, Sans-Serif", 14));
  hexNames = loadHexNames();
  newReading();
}

void draw(){
  background(247);
  drawHeader();
  drawHexagram(100, 160, yang, change, "Primary", hexIndex);
  if(hexIndexResult >= 0){
    drawHexagram(410, 160, yangResult, new boolean[6], "Resulting", hexIndexResult);
  }
  drawFooter();
  if(autoRefresh && millis() - lastRefresh > refreshIntervalMs){
    newReading();
    lastRefresh = millis();
  }
}

void drawHeader(){
  fill(15);
  textSize(20);
  text("I Ching — QRNG (ANU) powered casting", 24, 24);
  textSize(14);
  fill(70);
  text("SPACE: new cast    R: auto-refresh    S: save PNG", 24, 54);
  fill(50);
  text(statusMsg, 24, 80);
  text(sourceMsg, 24, 100);
}

void drawHexagram(float x, float y, boolean[] lines, boolean[] changing, String label, int idx){
  fill(30);
  textSize(16);
  text(label + (idx>=0? " — #"+(idx+1)+"  "+shortName(idx):""), x, y-32);
  // draw 6 lines from bottom to top
  float w = 180;
  float h = 16;
  float gap = 18;
  stroke(0,0);
  for(int i=0;i<6;i++){
    int lineIdx = i;
    float yy = y + (5-i)*(h+gap);
    boolean yangLine = lines[lineIdx];
    boolean isChanging = changing[lineIdx];
    if(yangLine){
      fill(20);
      noStroke();
      rect(x, yy, w, h, 3);
      if(isChanging){ // indicate old yang (9): draw small hollow
        noFill(); stroke(255); strokeWeight(2);
        rect(x+4, yy+4, w-8, h-8, 2);
        strokeWeight(1); noStroke();
      }
    } else {
      // yin: draw broken
      fill(20);
      noStroke();
      float seg = (w - 20)/2;
      rect(x, yy, seg, h, 3);
      rect(x + seg + 20, yy, seg, h, 3);
      if(isChanging){ // indicate old yin (6): small dots at split
        fill(255);
        rect(x + seg + 8, yy+4, 4, h-8);
        rect(x + seg + 8 + 4, yy+4, 4, h-8);
      }
    }
  }
}

void drawFooter(){
  float y = height - 150;
  fill(30);
  textSize(16);
  text("Reading", 24, y);
  textSize(14);
  String prim = formatLines(lineVals);
  text("Lines (bottom→top): " + prim, 24, y+24);
  if(hexIndexResult>=0){
    text("Resulting hexagram: #" + (hexIndexResult+1) + "  " + shortName(hexIndexResult), 24, y+44);
  }
  textSize(12);
  fill(80);
  text("Note: Names are short labels only. For text/judgments consult a translation.", 24, y+70);
}

String formatLines(int[] vals){
  String s = "";
  for(int i=0;i<6;i++){
    s += vals[i];
    if(i<5) s+="-";
  }
  return s;
}

String[] loadHexNames(){
  try{
    JSONArray arr = loadJSONArray("hex_names.json");
    String[] out = new String[arr.size()];
    for(int i=0;i<arr.size();i++){
      out[i] = arr.getString(i);
    }
    return out;
  } catch(Exception e){
    return new String[64];
  }
}

String shortName(int idx){
  if(hexNames==null || idx<0 || idx>=hexNames.length) return "";
  String full = hexNames[idx];
  // after " · " keep right side
  int p = full.indexOf("·");
  return p>0 ? full.substring(p+1).trim() : full;
}

void keyPressed(){
  if(key==' '){
    newReading();
  } else if(key=='r' || key=='R'){
    autoRefresh = !autoRefresh;
    statusMsg = autoRefresh ? "Auto-refresh: ON" : "Auto-refresh: OFF";
  } else if(key=='s' || key=='S'){
    String ts = year()+"-"+nf(month(),2)+"-"+nf(day(),2)+"_"+nf(hour(),2)+""+nf(minute(),2)+""+nf(second(),2);
    saveFrame("iching_qrng_"+ts+".png");
    statusMsg = "Saved screenshot.";
  }
}

void newReading(){
  usedQRNG = false;
  ensurePool(32); // at least 32 bytes available
  // Build 6 lines using 3 bits each: 000->6, 111->9, other triples equally to 7 or 8
  for(int i=0;i<6;i++){
    int b0 = nextBit();
    int b1 = nextBit();
    int b2 = nextBit();
    int sum = b0 + b1 + b2; // 0..3
    int val;
    if(sum==0){ val = 6; }          // old yin (changing broken)
    else if(sum==3){ val = 9; }     // old yang (changing solid)
    else if(sum==1){ val = 7; }     // young yang (solid)
    else { val = 8; }               // young yin (broken)
    lineVals[i] = val;
    yang[i] = (val==7 || val==9);
    change[i] = (val==6 || val==9);
  }
  hexIndex = computeHexIndex(yang);
  yangResult = Arrays.copyOf(yang, 6);
  for(int i=0;i<6;i++){
    if(change[i]) yangResult[i] = !yangResult[i];
  }
  hexIndexResult = any(change)? computeHexIndex(yangResult) : -1;
  statusMsg = usedQRNG ? "New cast from QRNG." : "New cast (PRNG fallback).";
  sourceMsg = usedQRNG ? "Source: QRNG (ANU)" : "Source: PRNG fallback";
  lastRefresh = millis();
}

boolean any(boolean[] a){
  for(boolean b : a) if(b) return true;
  return false;
}

int computeHexIndex(boolean[] lines){
  // bottom line is bit 0. yang=1, yin=0
  int idx = 0;
  for(int i=0;i<6;i++){
    if(lines[i]) idx |= (1<<i);
  }
  return idx;
}

int nextBit(){
  if(poolIdx>=bytesPool.length*8){
    ensurePool(32);
  }
  int byteIdx = poolIdx/8;
  int bitIdx = poolIdx%8;
  int bit = (bytesPool[byteIdx] >> bitIdx) & 1;
  poolIdx++;
  return bit;
}

void ensurePool(int minBytes){
  // Guarantee at least minBytes unread bytes available
  int unreadBits = bytesPool.length*8 - poolIdx;
  if(unreadBits >= minBytes*8) return;
  int[] more = fetchQRNGu8(64);
  if(more != null && more.length>0){
    usedQRNG = true;
    // Append unread remainder + new bytes
    int[] remainder;
    if(poolIdx < bytesPool.length*8){
      int bytesLeft = (bytesPool.length*8 - poolIdx + 7)/8;
      remainder = new int[bytesLeft];
      for(int i=0;i<bytesLeft;i++){
        int src = poolIdx/8 + i;
        remainder[i] = (src < bytesPool.length) ? bytesPool[src] : 0;
      }
    } else {
      remainder = new int[0];
    }
    int[] merged = new int[remainder.length + more.length];
    int p=0;
    for(int v : remainder) merged[p++] = v;
    for(int v : more) merged[p++] = v;
    bytesPool = merged;
    poolIdx = 0;
  } else {
    // fallback: PRNG
    usedQRNG = false;
    bytesPool = new int[minBytes];
    poolIdx = 0;
    Random r = new Random();
    for(int i=0;i<bytesPool.length;i++){
      bytesPool[i] = r.nextInt(256);
    }
  }
}

int[] fetchQRNGu8(int length){
  try{
    String url = API_URL.replace("length=64", "length="+length);
    JSONObject obj = loadJSONObject(url);
    if(obj==null) return null;
    JSONArray arr = obj.getJSONArray("data");
    int[] out = new int[arr.size()];
    for(int i=0;i<arr.size();i++){
      out[i] = arr.getInt(i);
    }
    return out;
  }catch(Exception e){
    return null;
  }
}
