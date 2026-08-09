// data/morph_flow.frag
#ifdef GL_ES
precision mediump float;
precision mediump int;
#endif

uniform sampler2D texA;
uniform sampler2D texB;
uniform sampler2D texFlow;   // RG packed flow: R->u, G->v, in [-1,1] mapped to [0,1]
uniform float t;             // 0..1
uniform float flowScale;     // pixels
uniform vec2 imgSize;        // canvas size (pixels)

varying vec4 vertTexCoord;

// sRGB <-> linear (approx)
vec3 srgb_to_linear(vec3 c) { return pow(c, vec3(2.2)); }
vec3 linear_to_srgb(vec3 c) { return pow(c, vec3(1.0/2.2)); }

vec2 decodeFlow(vec2 uv) {
  vec2 rg = texture2D(texFlow, uv).rg;     // 0..1
  vec2 f  = (rg * 2.0 - 1.0) * flowScale;  // pixels in image space
  // convert to normalized UV offsets
  vec2 px = f / imgSize;
  return px;
}

void main() {
  vec2 uv = vertTexCoord.st;

  // read packed flow (normalized in UV)
  vec2 d = decodeFlow(uv);

  // sample A and B at warped coords
  vec4 a = texture2D(texA, uv - t * d);
  vec4 b = texture2D(texB, uv + (1.0 - t) * d);

  // premultiplied + gamma-correct blend
  vec3 a_rgb = srgb_to_linear(a.rgb) * a.a;
  vec3 b_rgb = srgb_to_linear(b.rgb) * b.a;
  float a_a  = a.a;
  float b_a  = b.a;

  vec3 mix_rgb = mix(a_rgb, b_rgb, t);
  float mix_a  = mix(a_a,  b_a,  t);

  vec3 out_rgb = (mix_a > 0.0) ? (mix_rgb / mix_a) : vec3(0.0);
  out_rgb = linear_to_srgb(out_rgb);
  gl_FragColor = vec4(out_rgb, mix_a);
}
