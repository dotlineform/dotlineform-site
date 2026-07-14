---
doc_id: self-mutating-variables
title: Self-Mutating Variables
added_date: "2026-07-14 17:27"
last_updated: "2026-07-14 17:27"
parent_id: unsorted
---
# Self-Mutating Variables


Self-mutating variables are dynamic parameters that modify themselves based on feedback, noise, or other evolving conditions. They are especially useful in generative art to simulate complexity, emergence, and instability.
 <span style="font-family: .AppleColorEmojiUI;">
     ## 

 </span>## [52FCEA6B-79C7-4CBE-884E-A3D24CB0A308](attachments/52FCEA6B-79C7-4CBE-884E-A3D24CB0A308.html)
 <span style="font-family: .AppleColorEmojiUI;">
     ## 

 </span> <span style="font-family: .AppleColorEmojiUI;">
     ## 

 </span> <span style="font-family: .AppleColorEmojiUI;">
     ## 🔁
 </span> **What Are Self-Mutating Variables?**

* Change their behavior or rate of change over time
* React to their own state (feedback)
* Use noise or time to evolve unpredictably
* Introduce non-linearity into drawing processes

They differ from standard variables because they do not follow a fixed update rule — instead, they evolve based on prior context or entropy.
 <span style="font-family: .AppleColorEmojiUI;">
     
🧪
 </span> **Basic Example in Processing**

```
float angle = 0;
float angleStep = 0.01;

void setup() {
  size(600, 600);
  stroke(0);
  background(255);
}

void draw() {
  float x = width/2 + cos(angle) * 200;
  float y = height/2 + sin(angle) * 200;

  point(x, y);

  // Self-mutation: the step changes as a function of angle
  angleStep += sin(angle * 3.14) * 0.001;
  angle += angleStep;
}

```

 <span style="font-family: .AppleColorEmojiUI;">
     ## 

 </span> <span style="font-family: .AppleColorEmojiUI;">
     ## 🌀
 </span> **What Does This Do?**

* The angleStep
* evolves non-linearly over time
* The drawing begins predictably, but becomes increasingly unstable
* The motion appears organic and hard to replicate
 <span style="font-family: .AppleColorEmojiUI;">
     ## 

 </span> <span style="font-family: .AppleColorEmojiUI;">
     ## ⚙️
 </span> **Applications in Generative Design**

* **Ink dispersion**: stroke width or angle shifts unpredictably as ink "runs out"
* **Noise evolution**: use Perlin or simplex noise as part of the feedback
* **Recursive geometry**: adjust recursion depth or control points dynamically
 <span style="font-family: .AppleColorEmojiUI;">
     ## 

 </span> <span style="font-family: .AppleColorEmojiUI;">
     ## 📚
 </span> **Related Concepts**

* Feedback systems
* Strange attractors / chaos theory
* Stochastic processes in procedural generation
* Recursive subdivision with mutation
