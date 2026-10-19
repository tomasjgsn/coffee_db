<script lang="ts">
	import { scaleLinear } from 'd3-scale';
	import { EXTRACTION_THRESHOLDS, STRENGTH_THRESHOLDS } from '$lib/brewing/calculations';
	import Caustic from '$lib/light/Caustic.svelte';

	export interface ChartPoint {
		id: number;
		ey: number;
		tds: number;
		score: number | null;
		latest?: boolean;
	}

	export interface GuideRay {
		/** TDS per EY point — the ray is TDS = slope × EY from the origin. */
		slope: number;
		label: string;
	}

	let {
		points,
		connect = false,
		width = 640,
		height = 380,
		highlightId = null,
		tintPercentOf = null,
		rays = [],
		hoverRaySlope = null,
		onhover = null,
		onselect = null
	}: {
		points: ChartPoint[];
		connect?: boolean;
		width?: number;
		height?: number;
		highlightId?: number | null;
		/** Ink percentage (0–100) for the tint ramp, or null for plain ink. */
		tintPercentOf?: ((point: ChartPoint) => number | null) | null;
		/** Iso-ratio guide rays, faint and labeled where they exit the plot. */
		rays?: GuideRay[];
		/** The hovered/pinned cup's own ray, drawn in clay. */
		hoverRaySlope?: number | null;
		onhover?: ((point: ChartPoint | null, clientX: number, clientY: number) => void) | null;
		onselect?: ((point: ChartPoint) => void) | null;
	} = $props();

	const pad = { top: 18, right: 18, bottom: 44, left: 52 };

	const x = $derived(
		scaleLinear()
			.domain([
				Math.min(14, ...points.map((p) => p.ey - 0.5)),
				Math.max(24, ...points.map((p) => p.ey + 0.5))
			])
			.range([pad.left, width - pad.right])
	);
	const y = $derived(
		scaleLinear()
			.domain([
				Math.min(0.8, ...points.map((p) => p.tds - 0.05)),
				Math.max(1.6, ...points.map((p) => p.tds + 0.05))
			])
			.range([height - pad.bottom, pad.top])
	);

	const ex = EXTRACTION_THRESHOLDS;
	const st = STRENGTH_THRESHOLDS;

	const xTicks = $derived(x.ticks(6));
	const yTicks = $derived([0.9, st.weakMax, st.idealMax, 1.5]);

	function r(score: number | null): number {
		if (score === null) return 4;
		return 3 + score * 0.6;
	}

	function fillOf(p: ChartPoint): string {
		if (p.latest) return 'var(--solar)';
		const pct = tintPercentOf?.(p);
		if (pct === null || pct === undefined) return 'var(--graphite)';
		return `color-mix(in srgb, var(--graphite) ${Math.round(pct)}%, var(--chrome-1))`;
	}

	const pathD = $derived.by(() => {
		if (!connect || points.length < 2) return null;
		return points.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(p.ey)},${y(p.tds)}`).join(' ');
	});

	interface RaySegment {
		x1: number;
		y1: number;
		x2: number;
		y2: number;
		label?: string;
		labelAnchor: 'end' | 'start';
	}

	/** Clip the ray TDS = slope × EY to the visible plot rectangle. */
	function clipRay(slope: number, label?: string): RaySegment | null {
		const [eyLo, eyHi] = x.domain();
		const [tdsLo, tdsHi] = y.domain();
		const enterEy = Math.max(eyLo, tdsLo / slope);
		const exitEy = Math.min(eyHi, tdsHi / slope);
		if (enterEy >= exitEy) return null;
		const exitsTop = tdsHi / slope < eyHi;
		return {
			x1: x(enterEy),
			y1: y(slope * enterEy),
			x2: x(exitEy),
			y2: y(slope * exitEy),
			label,
			labelAnchor: exitsTop ? 'start' : 'end'
		};
	}

	const raySegments = $derived(
		rays.map((ray) => clipRay(ray.slope, ray.label)).filter((s): s is RaySegment => s !== null)
	);
	const hoverRay = $derived(hoverRaySlope !== null ? clipRay(hoverRaySlope) : null);

	// Keyboard: the chart is one tab stop (the latest cup by default); the
	// arrows walk the cups in brewing order, Enter pins the card.
	let svgEl: SVGSVGElement;
	let rovingIndex = $state<number | null>(null);
	let focusedId = $state<number | null>(null);
	const interactive = $derived(onhover !== null || onselect !== null);
	const tabStop = $derived(Math.min(rovingIndex ?? points.length - 1, points.length - 1));

	function focusDot(index: number) {
		rovingIndex = index;
		svgEl.querySelector<SVGCircleElement>(`circle[data-index="${index}"]`)?.focus();
	}

	function onDotKeydown(e: KeyboardEvent, index: number, p: ChartPoint) {
		const last = points.length - 1;
		if (e.key === 'Enter' || e.key === ' ') {
			e.preventDefault();
			onselect?.(p);
			return;
		}
		const next =
			e.key === 'ArrowLeft' || e.key === 'ArrowDown'
				? Math.max(0, index - 1)
				: e.key === 'ArrowRight' || e.key === 'ArrowUp'
					? Math.min(last, index + 1)
					: e.key === 'Home'
						? 0
						: e.key === 'End'
							? last
							: null;
		if (next === null) return;
		e.preventDefault();
		focusDot(next);
	}

	function onDotFocus(e: FocusEvent, index: number, p: ChartPoint) {
		rovingIndex = index;
		focusedId = p.id;
		const rect = (e.currentTarget as SVGCircleElement).getBoundingClientRect();
		onhover?.(p, rect.right, rect.top);
	}

	function onDotBlur() {
		focusedId = null;
		onhover?.(null, 0, 0);
	}
</script>

<svg
	bind:this={svgEl}
	viewBox="0 0 {width} {height}"
	role="img"
	aria-label="Brewing control chart: extraction yield against TDS with the ideal zone shaded"
	onmouseleave={(e) => onhover?.(null, e.clientX, e.clientY)}
>
	<defs>
		<radialGradient id="ideal-pool" cx="46%" cy="42%" r="65%">
			<stop offset="0%" stop-color="#fffdf4" stop-opacity="0.55" />
			<stop offset="45%" stop-color="#f8eec8" stop-opacity="0.28" />
			<stop offset="75%" stop-color="#e8a33d" stop-opacity="0.07" />
			<stop offset="100%" stop-color="#6b7c3f" stop-opacity="0" />
		</radialGradient>
	</defs>
	<rect
		x={pad.left}
		y={pad.top}
		width={width - pad.left - pad.right}
		height={height - pad.top - pad.bottom}
		fill="var(--bone)"
		stroke="var(--line)"
	/>
	<rect
		x={x(ex.underMax)}
		y={y(st.idealMax)}
		width={x(ex.idealMax) - x(ex.underMax)}
		height={y(st.weakMax) - y(st.idealMax)}
		fill="url(#ideal-pool)"
	/>
	<foreignObject
		x={x(ex.underMax)}
		y={y(st.idealMax)}
		width={x(ex.idealMax) - x(ex.underMax)}
		height={y(st.weakMax) - y(st.idealMax)}
		style="pointer-events: none;"
	>
		<div style="position: relative; width: 100%; height: 100%;">
			<Caustic intensity={0.5} />
		</div>
	</foreignObject>

	{#each [ex.underMax, ex.idealMax] as bound (bound)}
		<line x1={x(bound)} y1={pad.top} x2={x(bound)} y2={height - pad.bottom} stroke="var(--line-strong)" stroke-width="0.8" stroke-dasharray="3,3" />
	{/each}
	{#each [st.weakMax, st.idealMax] as bound (bound)}
		<line x1={pad.left} y1={y(bound)} x2={width - pad.right} y2={y(bound)} stroke="var(--line-strong)" stroke-width="0.8" stroke-dasharray="3,3" />
	{/each}

	<text x={(x(ex.underMax) + pad.left) / 2} y={(y(st.weakMax) + y(st.idealMax)) / 2} class="zone under" text-anchor="middle">Under</text>
	<text x={(x(ex.underMax) + x(ex.idealMax)) / 2} y={(y(st.weakMax) + y(st.idealMax)) / 2} class="zone ideal" text-anchor="middle">Ideal</text>
	<text x={(x(ex.idealMax) + width - pad.right) / 2} y={(y(st.weakMax) + y(st.idealMax)) / 2} class="zone over" text-anchor="middle">Over</text>

	{#each raySegments as seg (seg.label)}
		<line x1={seg.x1} y1={seg.y1} x2={seg.x2} y2={seg.y2} stroke="var(--line)" stroke-width="1" stroke-dasharray="1,4" stroke-linecap="round" class="ray" />
		{#if seg.label}
			<text
				x={seg.labelAnchor === 'start' ? seg.x2 + 2 : seg.x2 - 3}
				y={seg.labelAnchor === 'start' ? seg.y2 + 10 : seg.y2 - 4}
				class="ray-label"
				text-anchor={seg.labelAnchor === 'start' ? 'middle' : 'end'}>{seg.label}</text>
		{/if}
	{/each}
	{#if hoverRay}
		<line x1={hoverRay.x1} y1={hoverRay.y1} x2={hoverRay.x2} y2={hoverRay.y2} stroke="var(--solar)" stroke-width="1.2" stroke-dasharray="5,4" class="ray" />
	{/if}

	{#if pathD}
		<path d={pathD} fill="none" stroke="var(--graphite-soft)" stroke-width="1.5" stroke-dasharray="2,4" stroke-linecap="round" />
	{/if}

	{#each points as p, i (p.id)}
		<circle
			cx={x(p.ey)}
			cy={y(p.tds)}
			r={r(p.score)}
			fill={fillOf(p)}
			opacity={p.latest || p.id === highlightId ? 1 : 0.72}
			class="dot"
			class:interactive
			role="button"
			tabindex={interactive ? (i === tabStop ? 0 : -1) : undefined}
			data-index={i}
			aria-label="Cup {p.id}: extraction {p.ey.toFixed(1)}%, TDS {p.tds}%"
			onmouseenter={(e) => onhover?.(p, e.clientX, e.clientY)}
			onmousemove={(e) => onhover?.(p, e.clientX, e.clientY)}
			onclick={() => onselect?.(p)}
			onkeydown={(e) => onDotKeydown(e, i, p)}
			onfocus={(e) => onDotFocus(e, i, p)}
			onblur={onDotBlur}
		/>
		{#if p.id === highlightId && !p.latest && p.id !== focusedId}
			<circle cx={x(p.ey)} cy={y(p.tds)} r={r(p.score) + 5} fill="none" stroke="var(--graphite)" stroke-width="1.2" stroke-dasharray="2,2" class="ring" />
		{/if}
		{#if p.id === focusedId}
			<circle cx={x(p.ey)} cy={y(p.tds)} r={r(p.score) + 5} fill="none" stroke="var(--graphite)" stroke-width="2" class="ring focus-ring" />
		{/if}
	{/each}

	{#each xTicks as tick (tick)}
		<text x={x(tick)} y={height - pad.bottom + 16} class="tick" text-anchor="middle">{tick}</text>
	{/each}
	{#each yTicks as tick (tick)}
		<text x={pad.left - 8} y={y(tick) + 3} class="tick" text-anchor="end">{tick}</text>
	{/each}
	<text x={(pad.left + width - pad.right) / 2} y={height - 8} class="axis" text-anchor="middle">Extraction yield %</text>
	<text x={14} y={(pad.top + height - pad.bottom) / 2} class="axis" text-anchor="middle" transform="rotate(-90 14 {(pad.top + height - pad.bottom) / 2})">TDS %</text>
</svg>

<style>
	svg {
		width: 100%;
		height: auto;
		display: block;
	}
	.dot.interactive {
		cursor: pointer;
	}
	/* The focused cup draws its own solid ring instead of a box outline. */
	.dot:focus-visible {
		outline: none;
	}
	.ring {
		pointer-events: none;
	}
	.ray {
		pointer-events: none;
	}
	.ray-label {
		font-family: var(--font-mono);
		font-size: 9px;
		fill: var(--line-strong);
		pointer-events: none;
	}
	.tick,
	.axis {
		font-family: var(--font-mono);
		font-size: 10px;
		fill: var(--graphite-soft);
	}
	.zone {
		font-family: var(--font-mono);
		font-size: 10px;
	}
	.zone.under {
		fill: var(--amber-deep);
	}
	.zone.ideal {
		fill: var(--olive-deep);
		font-weight: 600;
	}
	.zone.over {
		fill: var(--ember);
	}
</style>
