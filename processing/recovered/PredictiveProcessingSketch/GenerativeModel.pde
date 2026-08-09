// GenerativeModel.pde
class GenerativeModel{
  // Latent dynamics: z_t = a*z_{t-1} + w, Observation: x_t = c*z_t + v
  float a = 0.98;
  float c = 1.0;
  float z = 0;
  float tphase = 0;

  float observe(int action){
    // toy world: latent follows slow drift + action bias
    tphase += 0.02;
    z = 0.8*z + 0.2*sin(tphase) + 0.05*(action-1); // action in {-1,0,1}
    float x = c*z + noise(0.05);
    return x;
  }

  float predict(float zhat){ return c*zhat; }

  float noise(float sd){
    return (float) (randomGaussian()*sd);
  }
}
