// data/crossfade.frag
#ifdef GL_ES
precision mediump float;
precision mediump int;
#endif

uniform sampler2D texA;
uniform sampler2D texB;
uniform float t;
varying vec4 vertTexCoord;

// approximate sRGB <-> linear
vec3 srgb_to_linear(vec3 c) { return pow(c, vec3(2.2)); }
vec3 linear_to_srgb(vec3 c) { return pow(c, vec3(1.0/2.2)); }

void main() {
  vec2 uv = vertTexCoord.st;
  vec4 a = texture2D(texA, uv);
  vec4 b = texture2D(texB, uv);

  // premultiply to handle PNG alpha cleanly
  vec3 a_rgb = srgb_to_linear(a.rgb) * a.a;
  vec3 b_rgb = srgb_to_linear(b.rgb) * b.a;
  float a_a = a.a;
  float b_a = b.a;

  vec3 mix_rgb = mix(a_rgb, b_rgb, t);
  float mix_a  = mix(a_a,  b_a,  t);

  vec3 out_rgb = mix_a > 0.0 ? mix_rgb / mix_a : vec3(0.0);
  out_rgb = linear_to_srgb(out_rgb);
  gl_FragColor = vec4(out_rgb, mix_a);
}
