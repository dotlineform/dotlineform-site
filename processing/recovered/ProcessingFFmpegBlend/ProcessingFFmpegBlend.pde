// Processing 4.x sketch
// Title: Processing FFmpeg Blender
// Purpose: GUI wrapper to select two videos and blend them with adjustable opacity via FFmpeg
// Platform: macOS/Win/Linux (requires ffmpeg in PATH or set absolute path)
// Author: ChatGPT
// License: MIT

// --------- UI State ---------
String ffmpegPath = "ffmpeg"; // change if ffmpeg not in PATH
String video1Path = "";
String video2Path = "";
String outputPath = "";
float opacity = 0.50;         // 0.0..1.0
boolean reverseSecond = false;
boolean normalizeAudio = true;
boolean isRunning = false;
StringBuilder logBuf = new StringBuilder();
Process ffProc;

// Slider geometry
int sliderX = 40, sliderY = 200, sliderW = 360, sliderH = 12;

// Buttons
class Btn {
  int x, y, w, h;
  String label;
  Btn(int x,int y,int w,int h,String label){this.x=x;this.y=y;this.w=w;this.h=h;this.label=label;}
  boolean over(){ return mouseX>=x && mouseX<=x+w && mouseY>=y && mouseY<=y+h; }
  void drawBtn(boolean enabled){
    stroke(80); fill(enabled ? (over()? color(230) : color(245)) : color(220));
    rect(x,y,w,h,6);
    fill(20); textAlign(CENTER,CENTER); text(label, x+w/2, y+h/2);
  }
}

Btn pickV1 = new Btn(420, 80, 160, 28, "Choose Video 1");
Btn pickV2 = new Btn(420, 120, 160, 28, "Choose Video 2");
Btn pickOut= new Btn(420, 160, 160, 28, "Save As…");
Btn toggleRev = new Btn(420, 210, 160, 28, "Toggle Reverse 2");
Btn toggleNorm = new Btn(420, 250, 160, 28, "Toggle Normalize");
Btn runBtn = new Btn(420, 300, 160, 36, "Render");
Btn cancelBtn = new Btn(420, 346, 160, 28, "Cancel");

// File chooser callbacks
void fileChosen1(File f){ if (f != null) video1Path = f.getAbsolutePath(); }
void fileChosen2(File f){ if (f != null) video2Path = f.getAbsolutePath(); }
void fileChosenOut(File f){ if (f != null) outputPath = f.getAbsolutePath(); }

void setup(){
  size(800, 640);
  surface.setTitle("Processing ↔ FFmpeg: Video Blender");
  textFont(createFont("Menlo", 14));
}

void draw(){
  background(252);
  fill(0);
  textAlign(LEFT, TOP);
  text("Processing FFmpeg Blender", 40, 28);
  fill(60);
  text("1) Choose two source videos\n2) Drag the opacity slider or type a value\n3) Click Render to create the blended output", 40, 54);

  // Paths
  fill(0);
  text("FFmpeg:", 40, 100);
  text(ffmpegPath, 120, 100);
  text("Video 1:", 40, 124);
  text(video1Path.isEmpty() ? "(not selected)" : video1Path, 120, 124);
  text("Video 2:", 40, 148);
  text(video2Path.isEmpty() ? "(not selected)" : video2Path, 120, 148);
  text("Output:", 40, 172);
  text(outputPath.isEmpty() ? "(auto next to Video 1)" : outputPath, 120, 172);

  // Slider
  drawSlider();
  fill(0);
  text(String.format("Opacity: %.2f", opacity), sliderX, sliderY - 24);
  text("Reverse 2: " + (reverseSecond ? "ON" : "OFF"), sliderX, sliderY + 28);
  text("Normalize audio mix: " + (normalizeAudio ? "ON" : "OFF"), sliderX, sliderY + 48);

  // Buttons
  pickV1.drawBtn(!isRunning);
  pickV2.drawBtn(!isRunning);
  pickOut.drawBtn(!isRunning);
  toggleRev.drawBtn(!isRunning);
  toggleNorm.drawBtn(!isRunning);
  runBtn.drawBtn(!isRunning);
  cancelBtn.drawBtn(isRunning);

  // Log area
  int logTop = 420;
  stroke(200); noFill(); rect(40, logTop, width-80, height-logTop-40);
  fill(0);
  textAlign(LEFT, TOP);
  String logTxt = logBuf.toString();
  drawWrappedText(logTxt, 52, logTop+12, width-104);

  // Footer
  fill(120);
  textAlign(LEFT, BOTTOM);
  text(isRunning ? "Encoding… check the log for FFmpeg output. Click Cancel to stop." : "Ready.", 40, height-20);
}

void mousePressed(){
  if (isRunning) {
    if (cancelBtn.over()) stopFFmpeg();
    return;
  }
  if (pickV1.over()) selectInput("Select Video 1", "fileChosen1");
  else if (pickV2.over()) selectInput("Select Video 2", "fileChosen2");
  else if (pickOut.over()) selectOutput("Select output file", "fileChosenOut");
  else if (toggleRev.over()) reverseSecond = !reverseSecond;
  else if (toggleNorm.over()) normalizeAudio = !normalizeAudio;
  else if (runBtn.over()) startFFmpeg();
  else if (overSlider(mouseX, mouseY)) updateSlider(mouseX);
}

void mouseDragged(){
  if (isRunning) return;
  if (overSlider(mouseX, mouseY)) updateSlider(mouseX);
}

void keyPressed(){
  if (key == 'c' || key == 'C') stopFFmpeg();
  if (key == 'r' || key == 'R') startFFmpeg();
}

void drawSlider(){
  // track
  stroke(150); fill(235);
  rect(sliderX, sliderY, sliderW, sliderH, 6);
  // knob at opacity position
  float kx = sliderX + constrain(opacity, 0, 1) * sliderW;
  noStroke(); fill(70, 120, 255);
  ellipse(kx, sliderY + sliderH/2, 16, 16);
}

boolean overSlider(int mx, int my){
  return mx >= sliderX && mx <= sliderX+sliderW && my >= sliderY-10 && my <= sliderY+sliderH+10;
}
void updateSlider(int mx){
  float t = map(mx, sliderX, sliderX+sliderW, 0, 1);
  opacity = constrain(t, 0, 1);
}

// ---- FFmpeg integration ----
void startFFmpeg(){
  if (video1Path.isEmpty() || video2Path.isEmpty()){
    appendLog("❌ Select both input videos first.");
    return;
  }
  String out = outputPath;
  if (out.isEmpty()){
    File v1 = new File(video1Path);
    out = new File(v1.getParentFile(), "blend_" + timeStamp() + ".mp4").getAbsolutePath();
  }
  outputPath = out;

  String revV = reverseSecond ? "reverse," : "";
  String revA = reverseSecond ? "areverse," : "";
  String alpha = String.format(java.util.Locale.US, "%.6f", opacity);
  String filter = String.format("[1:v]%sscale=iw:ih[rev];[0:v][rev]blend=all_mode=overlay:all_opacity=%s[v];" +
                                "[0:a]%svolume=%s[a0];[1:a]%svolume=%s[a1];[a0][a1]amix=inputs=2:normalize=%d[a]",
                                revV, alpha, "", alpha, revA, alpha, normalizeAudio ? 1 : 0);

  String[] cmd = {
    ffmpegPath,
    "-hide_banner", "-y",
    "-i", video1Path,
    "-i", video2Path,
    "-filter_complex", filter,
    "-map", "[v]",
    "-map", "[a]",
    "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k",
    "-movflags", "+faststart",
    out
  };

  appendLog("▶️ Running FFmpeg:");
  appendLog(join(cmd, " "));
  runAsync(cmd);
}

void stopFFmpeg(){
  if (ffProc != null){
    try{
      ffProc.destroy();
      appendLog("⏹️ Cancel requested.");
    }catch(Exception e){
      appendLog("Error stopping process: " + e.getMessage());
    }
  }
}

void runAsync(String[] cmd){
  isRunning = true;
  new Thread(() -> {
    try{
      ProcessBuilder pb = new ProcessBuilder(cmd);
      pb.redirectErrorStream(true);
      ffProc = pb.start();
      // Read output
      java.io.BufferedReader r = new java.io.BufferedReader(new java.io.InputStreamReader(ffProc.getInputStream()));
      String line;
      while ((line = r.readLine()) != null){
        appendLog(line);
      }
      int code = ffProc.waitFor();
      appendLog(code == 0 ? "✅ Done: " + outputPath : "❌ FFmpeg exit code: " + code);
    }catch(Exception e){
      appendLog("Exception: " + e.toString());
    }finally{
      isRunning = false;
      ffProc = null;
    }
  }).start();
}

synchronized void appendLog(String s){
  logBuf.append(s).append('\n');
  // keep buffer reasonable
  if (logBuf.length() > 200000){
    logBuf.delete(0, logBuf.length()-150000);
  }
}

String timeStamp(){
  java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("yyyyMMdd-HHmmss");
  return sdf.format(new java.util.Date());
}

// Basic wrapped text rendering in a rectangle width
void drawWrappedText(String txt, float x, float y, float w){
  float cx = x, cy = y;
  String[] lines = txt.split("\n");
  for (String line : lines){
    String[] words = splitTokens(line, " ");
    String curr = "";
    for (String word : words){
      String test = curr.isEmpty()? word : curr + " " + word;
      if (textWidth(test) > w){
        text(curr, cx, cy);
        cy += 16;
        curr = word;
      }else{
        curr = test;
      }
    }
    text(curr, cx, cy);
    cy += 16;
  }
}
