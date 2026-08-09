Loose Ends — Memory: Predictive Processing / Free-Energy Principle
Processing mini-app scaffold

Files:
- PredictiveProcessingSketch.pde: entry point, batch-style loop
- GenerativeModel.pde: latent state + predictions + errors
- MemoryStore.pde: parameters/priors, precision, replay buffer
- ActiveInferenceAgent.pde: inference (descend free energy), learning, simple action policy

How to run:
1) Open the folder in the Processing IDE.
2) Set size() as needed; this sketch runs headless-style, saving logs/images.
3) Press Run. It will iterate a fixed number of steps and write outputs to the sketch folder.

Notes:
- This is a conceptual scaffold. Replace TODOs with your model specifics.
- Memory is represented by parameters (theta), precision (lambda), and a simple replay buffer.
- Policy minimizes a toy 'expected free energy' (uncertainty + prediction error proxy).
