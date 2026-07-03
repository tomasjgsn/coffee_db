<script lang="ts">
	import { scaleLinear } from 'd3-scale';
	import { EXTRACTION_THRESHOLDS, STRENGTH_THRESHOLDS } from '$lib/brewing/calculations';

	export interface ChartPoint {
		id: number;
		ey: number;
		tds: number;
		score: number | null;
		latest?: boolean;
	}

	let {
		points,
		connect = false,
		width = 640,
		height = 380,
		highlightId = null,
		tintPercentOf = null,
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
		if (p.latest) return 'var(--clay)';
		const pct = tintPercentOf?.(p);
		if (pct === null || pct === undefined) return 'var(--ink)';
		return `color-mix(in srgb, var(--ink) ${Math.round(pct)}%, var(--kraft))`;
	}

	const pathD = $derived.by(() => {
		if (!connect || points.length < 2) return null;
		return points.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(p.ey)},${y(p.tds)}`).join(' ');
	});
</script>

<svg
	viewBox="0 0 {width} {height}"
	role="img"
	aria-label="Brewing control chart: extraction yield against TDS with the ideal zone shaded"
	onmouseleave={(e) => onhover?.(null, e.clientX, e.clientY)}
>
	<rect
		x={pad.left}
		y={pad.top}
		width={width - pad.left - pad.right}
		height={height - pad.top - pad.bottom}
		fill="var(--paper-bright)"
		stroke="var(--line-soft)"
	/>
	<rect
		x={x(ex.underMax)}
		y={y(st.idealMax)}
		width={x(ex.idealMax) - x(ex.underMax)}
		height={y(st.weakMax) - y(st.idealMax)}
		fill="var(--leaf-wash)"
	/>

	{#each [ex.underMax, ex.idealMax] as bound (bound)}
		<line x1={x(bound)} y1={pad.top} x2={x(bound)} y2={height - pad.bottom} stroke="var(--line-soft)" stroke-width="0.8" stroke-dasharray="3,3" />
	{/each}
	{#each [st.weakMax, st.idealMax] as bound (bound)}
		<line x1={pad.left} y1={y(bound)} x2={width - pad.right} y2={y(bound)} stroke="var(--line-soft)" stroke-width="0.8" stroke-dasharray="3,3" />
	{/each}

	<text x={(x(ex.underMax) + pad.left) / 2} y={(y(st.weakMax) + y(st.idealMax)) / 2} class="zone under" text-anchor="middle">Under</text>
	<text x={(x(ex.underMax) + x(ex.idealMax)) / 2} y={(y(st.weakMax) + y(st.idealMax)) / 2} class="zone ideal" text-anchor="middle">Ideal</text>
	<text x={(x(ex.idealMax) + width - pad.right) / 2} y={(y(st.weakMax) + y(st.idealMax)) / 2} class="zone over" text-anchor="middle">Over</text>

	{#if pathD}
		<path d={pathD} fill="none" stroke="var(--roast)" stroke-width="1.5" stroke-dasharray="2,4" stroke-linecap="round" />
	{/if}

	{#each points as p (p.id)}
		<circle
			cx={x(p.ey)}
			cy={y(p.tds)}
			r={r(p.score)}
			fill={fillOf(p)}
			opacity={p.latest || p.id === highlightId ? 1 : 0.72}
			class="dot"
			class:interactive={onhover !== null || onselect !== null}
			role={onselect ? 'button' : undefined}
			aria-label="Cup {p.id}"
			onmouseenter={(e) => onhover?.(p, e.clientX, e.clientY)}
			onmousemove={(e) => onhover?.(p, e.clientX, e.clientY)}
			onclick={() => onselect?.(p)}
		/>
		{#if p.latest}
			<circle cx={x(p.ey)} cy={y(p.tds)} r={r(p.score) + 5} fill="none" stroke="var(--clay)" stroke-width="1.5" stroke-dasharray="2,2" class="ring" />
		{/if}
		{#if p.id === highlightId && !p.latest}
			<circle cx={x(p.ey)} cy={y(p.tds)} r={r(p.score) + 5} fill="none" stroke="var(--ink)" stroke-width="1.5" stroke-dasharray="2,2" class="ring" />
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
	.ring {
		pointer-events: none;
	}
	.tick,
	.axis {
		font-family: var(--font-mono);
		font-size: 10px;
		letter-spacing: 0.08em;
		fill: var(--ink-soft);
		text-transform: uppercase;
	}
	.zone {
		font-family: var(--font-mono);
		font-size: 10px;
		letter-spacing: 0.14em;
		text-transform: uppercase;
	}
	.zone.under {
		fill: var(--ochre-deep);
	}
	.zone.ideal {
		fill: var(--leaf-deep);
		font-weight: 600;
	}
	.zone.over {
		fill: var(--clay-deep);
	}
</style>
