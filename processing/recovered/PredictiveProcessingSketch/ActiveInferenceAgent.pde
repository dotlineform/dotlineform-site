// ActiveInferenceAgent.pde
class ActiveInferenceAgent{
  GenerativeModel gm;
  MemoryStore mem;

  // Belief about latent
  float z_hat = 0;
  float lastErr = 0;
  int lastAct = 0; // -1, 0, +1

  // Hyperparameters
  float eta_z = 0.5f;    // step for inference (on z)
  float eta_th = 0.001f; // step for parameter learning
  float eta_lam = 0.001f;// step for precision learning (toy)

  ActiveInferenceAgent(GenerativeModel gm, MemoryStore mem){
    this.gm = gm;
    this.mem = mem;
  }

  void infer(float x){
    // Predict observation from current belief
    float x_pred = mem.theta_c * z_hat;
    float e = x - x_pred;
    lastErr = e;
    // Gradient descent on free-energy ~ precision-weighted prediction error
    z_hat += eta_z * mem.lambda * e * mem.theta_c;
  }

  void learn(float x){
    // Simple LMS-style updates as proxy for descending F wrt parameters
    float x_pred = mem.theta_c * z_hat;
    float e = x - x_pred;
    mem.theta_c += eta_th * mem.lambda * e * z_hat;
    // Precision update: larger residuals -> increase precision slowly (toy)
    mem.lambda = max(1.0, mem.lambda + eta_lam * (abs(e) - 1.0));
    // Cache for replay
    mem.push(x, z_hat);
  }

  void maybeReplay(){
    // Occasionally rehearse from memory to refine theta_c
    if (frameCount % 25 == 0 && mem.replay.size() > 0){
      int n = min(8, mem.replay.size());
      for (int i=0; i<n; i++){
        float[] pair = mem.replay.removeLast();
        float x = pair[0];
        float z = pair[1];
        float x_pred = mem.theta_c * z;
        float e = x - x_pred;
        mem.theta_c += eta_th * mem.lambda * e * z * 0.5; // smaller step on replay
      }
    }
  }

  void act(){
    // Choose action to minimize expected error next step (toy heuristic)
    // Try {-1,0,1} and pick the one with smallest predicted error magnitude
    int bestA = 0;
    float bestScore = 1e9;
    for (int a = -1; a <= 1; a++){
      float z_next = 0.9*z_hat + 0.05*(a); // crude forward model
      float x_pred_next = mem.theta_c * z_next;
      float score = abs(x_pred_next); // aim for small magnitude (proxy)
      if (score < bestScore){ bestScore = score; bestA = a; }
    }
    lastAct = bestA;
  }

  int lastAction(){ return lastAct; }

  float lastError(){ return lastErr; }
}
