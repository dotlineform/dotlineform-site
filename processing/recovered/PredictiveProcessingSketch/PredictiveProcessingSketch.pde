// PredictiveProcessingSketch.pde
// Entry point for the predictive processing mini-app
// Batch-style: draw() executes a finite loop and exits after saving outputs.

GenerativeModel gm;
MemoryStore mem;
ActiveInferenceAgent agent;

int T = 500; // total steps
int t = 0;
boolean done = false;

void settings(){
  size(800, 400); // for simple diagnostics
}

void setup(){
  surface.setTitle("Predictive Processing / FEP — Mini App");
  gm = new GenerativeModel();
  mem = new MemoryStore();
  agent = new ActiveInferenceAgent(gm, mem);

  background(255);
  stroke(0);
  noLoop(); // We'll run batch in one go
  runBatch();
}

void runBatch(){
  for (t = 0; t < T; t++){
    // 1) World emits an observation given previous action (toy sine + noise)
    float x = gm.observe(agent.lastAction());

    // 2) Inference: update latent belief z via descending free-energy gradient
    agent.infer(x);

    // 3) Learning: update parameters/precision (the "memory")
    agent.learn(x);

    // 4) Optional replay for planning
    agent.maybeReplay();

    // 5) Action: choose next action to reduce expected free energy
    agent.act();

    // 6) Log simple diagnostics to screen
    if (t % 10 == 0){
      println("t=" + t + " x=" + nf(x,1,3) + " z=" + nf(agent.z_hat,1,3) + " err=" + nf(agent.lastError(),1,3));
    }
  }
  saveFrame("diagnostic-####.png"); // final snapshot
  println("Done.");
  exit();
}
