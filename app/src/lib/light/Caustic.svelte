<script lang="ts">
	import { onMount } from 'svelte';
	import { mountShader } from './engine';

	/**
	 * Sunlight through the sample: wandering caustic filaments with a
	 * dispersive fringe, pooled by a soft mask, biased by the fixed sun,
	 * bending faintly toward the pointer. Renders over a static CSS
	 * fallback; disappears silently without WebGL.
	 */
	let { intensity = 1 }: { intensity?: number } = $props();

	let canvas: HTMLCanvasElement;
	// Plain mirror of the prop so the render loop reads it without
	// touching Svelte reactivity from inside requestAnimationFrame.
	let current = 1;
	$effect(() => {
		current = intensity;
	});

	const FRAG = `#version 300 es
precision highp float;
uniform float u_time;
uniform vec2 u_res;
uniform vec2 u_pointer;
uniform float u_intensity;
out vec4 outColor;

float caustic(vec2 uv, float t) {
	vec2 p = mod(uv * 6.28318, 6.28318) - 250.0;
	vec2 i = p;
	float c = 1.0;
	float inten = 0.005;
	for (int n = 0; n < 4; n++) {
		float ft = t * (1.0 - (3.5 / float(n + 1)));
		i = p + vec2(cos(ft - i.x) + sin(ft + i.y), sin(ft - i.y) + cos(ft + i.x));
		c += 1.0 / length(vec2(p.x / (sin(i.x + ft) / inten), p.y / (cos(i.y + ft) / inten)));
	}
	c /= 4.0;
	c = 1.17 - pow(c, 1.4);
	return pow(abs(c), 8.0);
}

void main() {
	vec2 uv = gl_FragCoord.xy / u_res;
	vec2 hand = u_pointer - 0.5;

	// Parallax: the liquid shifts faintly as the hand moves past.
	vec2 p = uv + hand * -0.05;
	float t = u_time * 0.35;

	// Dispersion: each channel reads the field at a slightly different angle.
	float r = caustic(p + vec2(0.006, 0.002), t);
	float g = caustic(p, t);
	float b = caustic(p - vec2(0.006, 0.002), t);

	// Soft pool mask, brightest just off-center toward the sun.
	vec2 d = (uv - vec2(0.44, 0.56)) * vec2(1.25, 1.9);
	float mask = smoothstep(1.0, 0.25, length(d));

	// One sun, 10 o'clock high.
	float sun = 0.75 + 0.5 * dot(normalize(vec2(-0.55, 0.84)), uv - 0.5);

	// The hand lifts the light a touch where it passes.
	float lift = 1.0 + 0.14 * smoothstep(0.5, 0.0, length(uv - u_pointer));

	vec3 core = vec3(1.0, 0.99, 0.955);
	vec3 warm = vec3(0.949, 0.886, 0.686);
	vec3 fringe = vec3(r, g, b);
	vec3 col = core * g + warm * 0.4 * fringe;

	float a = clamp(g * 0.62 + max(r - b, 0.0) * 0.25, 0.0, 1.0) * mask * sun * lift * u_intensity;
	outColor = vec4(col * a, a * 0.82);
}`;

	onMount(() => {
		const handle = mountShader(canvas, FRAG, () => current);
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
