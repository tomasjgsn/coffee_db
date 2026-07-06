/**
 * The HARD LIGHT engine: a minimal WebGL2 runtime for the brand's light
 * behaviors (docs/BRAND.md, section 5). One fragment shader per surface,
 * a fixed sun, and the pointer as a hand near the instrument.
 *
 * Disciplines built in: devicePixelRatio cap, pause when the tab is hidden
 * or the canvas is offscreen, a single static frame under
 * prefers-reduced-motion, and silent no-op when WebGL is unavailable
 * (the CSS stills underneath remain the truth).
 */

const VERT = `#version 300 es
void main() {
	vec2 p = vec2(float((gl_VertexID << 1) & 2), float(gl_VertexID & 2));
	gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0);
}`;

export interface LightHandle {
	dispose: () => void;
}

export function mountShader(
	canvas: HTMLCanvasElement,
	fragSrc: string,
	getIntensity: () => number = () => 1
): LightHandle | null {
	const glMaybe = canvas.getContext('webgl2', {
		alpha: true,
		antialias: false,
		premultipliedAlpha: true
	});
	if (!glMaybe) return null;
	const gl: WebGL2RenderingContext = glMaybe;

	const program = gl.createProgram();
	const vs = compile(gl, gl.VERTEX_SHADER, VERT);
	const fs = compile(gl, gl.FRAGMENT_SHADER, fragSrc);
	if (!program || !vs || !fs) return null;
	gl.attachShader(program, vs);
	gl.attachShader(program, fs);
	gl.linkProgram(program);
	if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
		console.warn('hard-light shader failed to link:', gl.getProgramInfoLog(program));
		return null;
	}
	gl.useProgram(program);

	const uTime = gl.getUniformLocation(program, 'u_time');
	const uRes = gl.getUniformLocation(program, 'u_res');
	const uPointer = gl.getUniformLocation(program, 'u_pointer');
	const uIntensity = gl.getUniformLocation(program, 'u_intensity');

	gl.enable(gl.BLEND);
	gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);

	const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
	const dpr = Math.min(window.devicePixelRatio || 1, 1.5);

	let raf = 0;
	let running = false;
	let visible = true;
	let disposed = false;
	const start = performance.now();

	// The hand near the instrument: tracked on the window, smoothed toward
	// the target so reflections glide rather than twitch.
	const target = { x: 0.5, y: 0.5 };
	const pointer = { x: 0.5, y: 0.5 };
	function onPointerMove(e: PointerEvent) {
		const rect = canvas.getBoundingClientRect();
		if (rect.width === 0 || rect.height === 0) return;
		target.x = (e.clientX - rect.left) / rect.width;
		target.y = (e.clientY - rect.top) / rect.height;
	}

	function resize() {
		const rect = canvas.getBoundingClientRect();
		const w = Math.max(1, Math.round(rect.width * dpr));
		const h = Math.max(1, Math.round(rect.height * dpr));
		if (canvas.width !== w || canvas.height !== h) {
			canvas.width = w;
			canvas.height = h;
			gl.viewport(0, 0, w, h);
		}
	}

	function frame() {
		if (disposed) return;
		resize();
		pointer.x += (target.x - pointer.x) * 0.06;
		pointer.y += (target.y - pointer.y) * 0.06;
		gl.clearColor(0, 0, 0, 0);
		gl.clear(gl.COLOR_BUFFER_BIT);
		gl.uniform1f(uTime, (performance.now() - start) / 1000);
		gl.uniform2f(uRes, canvas.width, canvas.height);
		gl.uniform2f(uPointer, pointer.x, 1 - pointer.y);
		gl.uniform1f(uIntensity, getIntensity());
		gl.drawArrays(gl.TRIANGLES, 0, 3);
		if (running) raf = requestAnimationFrame(frame);
	}

	function play() {
		if (running || disposed || reduced) return;
		running = true;
		raf = requestAnimationFrame(frame);
	}
	function pause() {
		running = false;
		cancelAnimationFrame(raf);
	}

	const io = new IntersectionObserver((entries) => {
		visible = entries[0]?.isIntersecting ?? true;
		if (visible && !document.hidden) play();
		else pause();
	});
	io.observe(canvas);

	function onVisibility() {
		if (!document.hidden && visible) play();
		else pause();
	}
	document.addEventListener('visibilitychange', onVisibility);

	const ro = new ResizeObserver(() => {
		if (reduced) frame();
	});
	ro.observe(canvas);

	if (reduced) {
		// One correct still, no loop, no pointer.
		frame();
	} else {
		window.addEventListener('pointermove', onPointerMove, { passive: true });
		play();
	}

	return {
		dispose() {
			disposed = true;
			pause();
			io.disconnect();
			ro.disconnect();
			document.removeEventListener('visibilitychange', onVisibility);
			window.removeEventListener('pointermove', onPointerMove);
			gl.deleteProgram(program);
		}
	};
}

function compile(gl: WebGL2RenderingContext, type: number, src: string): WebGLShader | null {
	const shader = gl.createShader(type);
	if (!shader) return null;
	gl.shaderSource(shader, src);
	gl.compileShader(shader);
	if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
		console.warn('hard-light shader failed to compile:', gl.getShaderInfoLog(shader));
		gl.deleteShader(shader);
		return null;
	}
	return shader;
}
