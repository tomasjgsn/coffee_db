<script lang="ts">
	import { onMount } from 'svelte';
	import { mountShader } from './engine';

	/**
	 * Real chrome: a procedural environment (blown skylight, bone wall, red
	 * floor, a dark frame line) sampled by reflection vectors that track the
	 * pointer, plus one hard sun glint. Two shapes: a horizontal rule (tube
	 * cross-section) and a chronometer ring.
	 */
	let { shape = 'rule' }: { shape?: 'rule' | 'ring' } = $props();

	let canvas: HTMLCanvasElement;

	const ENV = `
vec3 env(float h, float x) {
	// The room, top to bottom: skylight glare, bone wall, frame line, red floor.
	vec3 bone = vec3(0.961, 0.937, 0.918);
	vec3 glare = vec3(1.25);
	vec3 frameLine = vec3(0.11, 0.11, 0.13);
	vec3 floorHi = vec3(0.871, 0.169, 0.106);
	vec3 floorLo = vec3(0.357, 0.055, 0.024);

	vec3 c = bone;
	c = mix(c, glare, smoothstep(0.45, 0.75, h) * smoothstep(1.05, 0.8, h));
	c = mix(c, frameLine, smoothstep(0.03, 0.0, abs(h + 0.18)) * 0.8);
	float fl = smoothstep(-0.18, -0.55, h);
	c = mix(c, mix(floorHi, floorLo, clamp(-h * 1.2 - 0.2, 0.0, 1.0)), fl);
	// Faint vertical cadence: other things in the room.
	c *= 0.96 + 0.04 * sin(x * 21.0);
	return c;
}`;

	const RULE_FRAG = `#version 300 es
precision highp float;
uniform float u_time;
uniform vec2 u_res;
uniform vec2 u_pointer;
uniform float u_intensity;
out vec4 outColor;
${ENV}
void main() {
	vec2 uv = gl_FragCoord.xy / u_res;
	// Tube cross-section: the normal sweeps top to bottom of the strip.
	float ny = (uv.y - 0.5) * 2.0;
	float h = clamp(ny * 1.5 + (u_pointer.y - 0.5) * 1.4, -1.0, 1.05);
	vec3 c = env(h, uv.x + (u_pointer.x - 0.5) * 0.35);
	// The sun streak: fixed left of center, sliding slightly with the hand.
	float sunX = 0.3 + (u_pointer.x - 0.5) * 0.18;
	c += vec3(1.0) * pow(max(1.0 - abs(uv.x - sunX) * 7.0, 0.0), 3.0) * 0.85;
	c += vec3(1.0) * pow(max(1.0 - abs(ny), 0.0), 6.0) * 0.22;
	outColor = vec4(c * u_intensity, u_intensity);
}`;

	const RING_FRAG = `#version 300 es
precision highp float;
uniform float u_time;
uniform vec2 u_res;
uniform vec2 u_pointer;
uniform float u_intensity;
out vec4 outColor;
${ENV}
void main() {
	vec2 uv = gl_FragCoord.xy / u_res;
	vec2 p = (uv - 0.5) * 2.0;
	p.x *= u_res.x / u_res.y;
	float rad = length(p);
	float ringMid = 0.92;
	float ringHalf = 0.055;
	float band = 1.0 - smoothstep(ringHalf - 0.012, ringHalf + 0.012, abs(rad - ringMid));
	if (band <= 0.0) { outColor = vec4(0.0); return; }

	vec2 n = p / max(rad, 0.0001);
	// Tube profile across the ring's width.
	float across = clamp((rad - ringMid) / ringHalf, -1.0, 1.0);
	float h = clamp(n.y * (0.75 + 0.25 * across) + (u_pointer.y - 0.5) * 0.9, -1.0, 1.05);
	vec3 c = env(h, atan(n.y, n.x) * 1.6 + (u_pointer.x - 0.5) * 0.8);

	// One sun, 10 o'clock high: a hard blown glint and a dim answer opposite.
	vec2 sunDir = normalize(vec2(-0.55, 0.84));
	c += vec3(1.0) * pow(max(dot(n, sunDir), 0.0), 60.0) * 1.5;
	c += vec3(1.0) * pow(max(dot(n, -sunDir), 0.0), 90.0) * 0.35;
	// Rim shading across the tube.
	c *= 0.82 + 0.35 * (1.0 - abs(across));

	float a = band * u_intensity;
	outColor = vec4(c * a, a);
}`;

	onMount(() => {
		const handle = mountShader(canvas, shape === 'ring' ? RING_FRAG : RULE_FRAG);
		return () => handle?.dispose();
	});
</script>

<canvas bind:this={canvas} aria-hidden="true"></canvas>

<style>
	canvas {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		display: block;
		pointer-events: none;
	}
</style>
