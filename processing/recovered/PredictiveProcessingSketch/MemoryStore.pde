// MemoryStore.pde
import java.util.ArrayDeque;

class MemoryStore{
  // Parameters (theta) and precision (lambda) act as memory
  float theta_a = 0.9;   // learnable analogue of a
  float theta_c = 1.0;   // learnable analogue of c
  float lambda = 100.0;  // precision (1/variance) on prediction errors

  // Simple replay buffer of (x, zhat) pairs
  ArrayDeque<float[]> replay = new ArrayDeque<float[]>();
  int maxReplay = 256;

  void push(float x, float zhat){
    if (replay.size() >= maxReplay) replay.removeFirst();
    replay.addLast(new float[]{x, zhat});
  }
}
