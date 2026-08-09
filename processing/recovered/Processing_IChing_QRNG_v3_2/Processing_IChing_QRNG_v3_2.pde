// QRNG Divination — v3.2
// Features:
// - Async QRNG prefetch ring buffer (low/high water, backoff)
// - Ritual-pause timer with breathing animation before reveal
// - Toggles: P cycles pause length (4/8/12s), R auto-refresh, M mode (I Ching/mo), L logging, Q question

import processing.data.*;
import java.util.*;
import java.net.*;
import java.io.*;
import java.text.SimpleDateFormat;

String API_URL = "https://qrng.anu.edu.au/API/jsonIid?length=1024&type=uint8";

enum Mode { ICHING, MO }
Mode mode = Mode.ICHING;

boolean autoRefresh = false;
boolean loggingOn = false;
String currentQuestion = "";

int refreshIntervalMs = 10000;
int lastRefresh = 0;

// Ritual pause
int[] pauseOptions = {4000, 8000, 12000};
int pauseIdx = 1; // default 8s
int revealAt = 0;
boolean revealArmed = false;

// Prefetch ring buffer
byte[] ring = new byte[8192]; // capacity
int head = 0, tail = 0; // head=read, tail=write
int lowWater = 256;
int highWater = 4096;
boolean fetching = false;
long nextFetchAllowedAt = 0;
int backoffMs = 2000; // exponential up to 60s
boolean usedQRNG = false;
String sourceMsg = "Source: QRNG (ANU)";
String statusMsg = "Ready";

// Iching state
int[] lineVals = new int[6];
boolean[] yang = new boolean[6];
boolean[] change = new boolean[6];
boolean[] yangResult = new boolean[6];
int hexIndex = 0;
int hexIndexResult = -1;

// mo state
int die1 = 0, die2 = 0, dieSum = 0;
String[] syllables = {"A","RA","PA","TSA","NA","DHI"};
class PairRow { String label, outcome, advice, remedy, notes; PairRow(String l,String o,String a,String r,String n){label=l; outcome=o; advice=a; remedy=r; notes=n;} }
HashMap<String, PairRow> manjushriPairs = new HashMap<String, PairRow>();

String[] hexNames;
PrintWriter logWriter;

void setup(){
  size(920, 860);
  surface.setTitle("QRNG Divination — I Ching & mo (v3.2)");
  textAlign(LEFT, TOP);
  textFont(createFont("Inter, Helvetica, Arial, Sans-Serif", 14));
  hexNames = loadHexNames();
  loadManjushriPairs();
  initLog();
  // kick off initial fetch
  backgroundFetch();
  newReading();
}

void draw(){
  background(247);
  maybeFetch();
  drawHeader();
  if(mode==Mode.ICHING){
    drawHexagram(130, 220, yang, change, "Primary", hexIndex);
    if(hexIndexResult >= 0) drawHexagram(560, 220, yangResult, new boolean[6], "Resulting", hexIndexResult);
    drawFooterIching();
  } else {
    drawMoPanel();
  }
  drawBottomBar();
  drawRitualOverlay();

  if(autoRefresh && millis() - lastRefresh > refreshIntervalMs){
    triggerCast();
  }
}

void drawHeader(){
  fill(15); textSize(22);
  text("QRNG Divination — I Ching × mo", 24, 24);
  textSize(14); fill(60);
  text("Mode: " + (mode==Mode.ICHING ? "I Ching (hexagrams)" : "Tibetan mo (dice)")
       + "  |  SPACE=new  R=auto  M=mode  L=logging  Q=question  S=screenshot  P=pause", 24, 56);
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
  float y = height - 220;
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
  float x = 120, y = 220;
  fill(30); textSize(18); text("Tibetan mo — two dice (2–12)", x, y-40);
  textSize(14); fill(40);
  String s1 = syllables[constrain(die1,1,6)-1];
  String s2 = syllables[constrain(die2,1,6)-1];
  text("Die 1: "+die1+" ("+s1+")    Die 2: "+die2+" ("+s2+")    Sum: "+dieSum+"    Pair: "+s1+"–"+s2, x, y);
  drawDie(x, y+30, die1);
  drawDie(x+120, y+30, die2);

  // guidance
  float gx = x + 240, gy = y+10, gw = 500, gh = 180;
  stroke(220); fill(255); rect(gx, gy, gw, gh, 12);
  fill(20); textSize(15);
  text("Lineage guidance (Manjushri mode)", gx+12, gy+10);
  PairRow row = manjushriPairs.get(s1+"-"+s2);
  textSize(13); fill(40);
  if(row!=null){
    text("Outcome: " + nz(row.outcome), gx+12, gy+34, gw-24, 24);
    text("Advice: " + nz(row.advice),  gx+12, gy+60, gw-24, 48);
    text("Remedy: " + nz(row.remedy),  gx+12, gy+112, gw-24, 48);
  } else {
    text("No pair entry found. Edit data/manjushri_mo_lineage_template.csv", gx+12, gy+34);
  }

  textSize(12); fill(60);
  text(manjushriPairs.size()>0 ? "Manjushri table loaded." : "Manjushri table not present.", x, y+160);
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
  text("Logging: " + (loggingOn? "ON":"OFF") + "  |  Auto: " + (autoRefresh? "ON":"OFF") + "  |  Pause: " + (pauseOptions[pauseIdx]/1000) + "s  |  Save: S  |  Mode: M  |  Question: Q", 24, y);
}

void drawRitualOverlay(){
  if(!revealArmed) return;
  int remaining = max(0, revealAt - millis());
  float alpha = map(remaining, 0, pauseOptions[pauseIdx], 0, 180);
  noStroke();
  fill(255, 255, 255, alpha);
  rect(0, 0, width, height);

  // breathing circle
  float t = millis() / 1000.0;
  float phase = (sin(TWO_PI * t / 4.0) + 1) * 0.5; // 4s breath
  float r = 40 + 20 * phase;
  float cx = width - 90, cy = 90;
  fill(0, 0, 0, 100);
  ellipse(cx, cy, r*2, r*2);
  fill(255);
  textAlign(CENTER, CENTER);
  textSize(12);
  text("pause " + nf(remaining/1000.0,1,1) + "s", cx, cy);
  textAlign(LEFT, TOP);
  if(remaining <= 0){
    revealArmed = false;
  }
}

void keyPressed(){
  if(key==' '){
    triggerCast();
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
    triggerCast();
  } else if(key=='l' || key=='L'){
    loggingOn = !loggingOn;
    statusMsg = loggingOn ? "Logging: ON" : "Logging: OFF";
  } else if(key=='q' || key=='Q'){
    String s = javax.swing.JOptionPane.showInputDialog("Enter question (optional):", currentQuestion);
    if(s!=null) currentQuestion = s;
  } else if(key=='p' || key=='P'){
    pauseIdx = (pauseIdx + 1) % pauseOptions.length;
    statusMsg = "Pause set to " + (pauseOptions[pauseIdx]/1000) + "s";
  }
}

void triggerCast(){
  newReading();
  revealArmed = true;
  revealAt = millis() + pauseOptions[pauseIdx];
  lastRefresh = millis();
}

void newReading(){
  usedQRNG = haveBytes();
  if(mode==Mode.ICHING){
    // 6 lines, each from 3 bits (000->6, 111->9, one-hot->7, two-hot->8)
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
  sourceMsg = usedQRNG ? "Source: QRNG (ANU)" : "Source: PRNG fallback";
  statusMsg = usedQRNG ? "Cast from prefetched QRNG pool." : "Cast from PRNG (buffer empty).";
  if(loggingOn) appendLog();
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

// Manjushri load
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
  }catch(Exception e){}
}

// Prefetch helpers
void maybeFetch(){
  if(fetching) return;
  int avail = bytesAvailable();
  if(avail < lowWater && millis() > nextFetchAllowedAt){
    backgroundFetch();
  }
}

int bytesAvailable(){
  int diff = tail - head;
  if(diff < 0) diff += ring.length;
  return diff;
}

boolean haveBytes(){
  return bytesAvailable() > 0;
}

int nextBit(){
  // If empty, fall back to PRNG
  if(bytesAvailable() <= 0){
    Random r = new Random();
    return r.nextBoolean() ? 1 : 0;
  }
  int b = nextByte() & 0x01; // consume bit-by-bit by consuming bytes; simple but adequate given plentiful pool
  return b;
}

int nextByte(){
  if(bytesAvailable() <= 0){
    Random r = new Random();
    return r.nextInt(256);
  }
  int val = ring[head] & 0xFF;
  head = (head + 1) % ring.length;
  return val;
}

int sampleDie(){
  int v=0;
  do{
    int b0 = nextBit(), b1 = nextBit(), b2 = nextBit();
    v = (b0<<2) | (b1<<1) | b2; // 0..7
  }while(v<1 || v>6);
  return v;
}

void backgroundFetch(){
  fetching = true;
  new Thread(new Runnable(){
    public void run(){
      try{
        JSONObject obj = loadJSONObject(API_URL);
        JSONArray arr = obj.getJSONArray("data");
        int n = arr.size();
        for(int i=0;i<n;i++){
          byte v = (byte)arr.getInt(i);
          ring[tail] = v;
          tail = (tail + 1) % ring.length;
          // avoid overwrite of unread data; if full, advance head
          if(tail == head){
            head = (head + 1) % ring.length;
          }
        }
        usedQRNG = true;
        fetching = false;
        backoffMs = 2000; // reset
      }catch(Exception e){
        fetching = false;
        usedQRNG = false;
        nextFetchAllowedAt = millis() + backoffMs;
        backoffMs = min(backoffMs * 2, 60000);
      }
    }
  }).start();
}

// Logging
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
