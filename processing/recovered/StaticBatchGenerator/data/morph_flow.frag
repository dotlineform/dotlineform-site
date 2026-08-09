// data/morph_flow.frag
#ifdef GL_ES
precision mediump float;
precision mediump int;
#endif
uniform sampler2D texA;
uniform sampler2D texB;
uniform sampler2D texFlow; // RG packed: R->u, G->v mapped from [-scale,+scale] to [0,1]
uniform float t;
uniform float flowScale;   // pixels
uniform vec2 imgSize;      // pixels
varying vec4 vertTexCoord;
vec3 s2l(vec3 c){ return pow(c, vec3(2.2)); }
vec3 l2s(vec3 c){ return pow(c, vec3(1.0/2.2)); }
vec2 decodeFlow(vec2 uv){
  vec2 rg = texture2D(texFlow, uv).rg;
  vec2 px = (rg*2.0 - 1.0) * flowScale / imgSize; // UV offset
  return px;
}
void main(){
  vec2 uv = vertTexCoord.st;
  vec2 d = decodeFlow(uv);
  vec4 a = texture2D(texA, uv - t * d);
  vec4 b = texture2D(texB, uv + (1.0 - t) * d);
  vec3 ar = s2l(a.rgb) * a.a;
  vec3 br = s2l(b.rgb) * b.a;
  float aa = a.a, ba = b.a;
  vec3 mr = mix(ar, br, t);
  float ma = mix(aa, ba, t);
  vec3 out_rgb = ma>0.0 ? mr/ma : vec3(0.0);
  gl_FragColor = vec4(l2s(out_rgb), ma);
}