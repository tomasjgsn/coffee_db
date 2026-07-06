<script lang="ts">
	import { scaleLinear } from 'd3-scale';
	import { leastSquares, trendDirection } from '$lib/analysis';

	let {
		title,
		unit = '',
		points,
		highlightId = null
	}: {
		title: string;
		unit?: string;
		points: { id: number; x: number; y: number }[];
		highlightId?: number | null;
	} = $props();

	const W = 220;
	const H = 150;
	const pad = { top: 10, right: 10, bottom: 26, left: 26 };

	const fit = $derived(leastSquares(points));
	const direction = $derived(trendDirection(fit));

	const x = $derived.by(() => {
		if (points.length === 0) return null;
		const values = points.map((p) => p.x);
		const min = Math.min(...values);
		const max = Math.max(...values);
		const span = Math.max(0.001, max - min);
		// Don't pad below zero for naturally non-negative variables (rest days).
		const lo = min >= 0 ? Math.max(0, min - span * 0.08) : min - span * 0.08;
		return scaleLinear()
			.domain([lo, max + span * 0.08])
			.range([pad.left, W - pad.right]);
	});
	const y = $derived(
		scaleLinear()
			.domain([0, 5])
			.range([H - pad.bottom, pad.top])
	);

	const trendLine = $derived.by(() => {
		if (!fit || !x || direction === null) return null;
		const [x0, x1] = x.domain();
		const clamp = (v: number) => Math.max(0, Math.min(5, v));
		return {
			x1: x(x0),
			y1: y(clamp(fit.intercept + fit.slope * x0)),
			x2: x(x1),
			y2: y(clamp(fit.intercept + fit.slope * x1))
		};
	});

	const GLYPHS = { up: '↗', down: '↘', flat: '—' } as const;
</script>

<div class="panel">
	<div class="panel-head">
		<span class="micro">{title}{unit ? ` (${unit})` : ''}</span>
		<span class="num direction" class:up={direction === 'up'} class:down={direction === 'down'}>
			{direction ? GLYPHS[direction] : ''}
			<span class="micro n">n={points.length}</span>
		</span>
	</div>
	{#if points.length === 0 || !x}
		<p class="micro empty">No cups with this reading in the slice</p>
	{:else}
		<svg viewBox="0 0 {W} {H}" role="img" aria-label="Score against {title.toLowerCase()}">
			<line x1={pad.left} y1={H - pad.bottom} x2={W - pad.right} y2={H - pad.bottom} stroke="var(--line-strong)" stroke-width="0.8" />
			<line x1={pad.left} y1={pad.top} x2={pad.left} y2={H - pad.bottom} stroke="var(--line-strong)" stroke-width="0.8" />
			{#if trendLine}
				<line {...trendLine} stroke="var(--solar)" stroke-width="1.5" stroke-dasharray="4,3" stroke-linecap="round" />
			{/if}
			{#each points as p (p.id)}
				<circle
					cx={x(p.x)}
					cy={y(p.y)}
					r={p.id === highlightId ? 4.5 : 3}
					fill={p.id === highlightId ? 'var(--solar)' : 'var(--graphite)'}
					opacity={p.id === highlightId ? 1 : 0.65}
				/>
			{/each}
			<text x={pad.left - 4} y={y(5) + 3} class="tick" text-anchor="end">5</text>
			<text x={pad.left - 4} y={y(0) + 3} class="tick" text-anchor="end">0</text>
			<text x={x.range()[0]} y={H - 8} class="tick" text-anchor="start">{Math.round(x.domain()[0] * 10) / 10}</text>
			<text x={x.range()[1]} y={H - 8} class="tick" text-anchor="end">{Math.round(x.domain()[1] * 10) / 10}</text>
		</svg>
	{/if}
</div>

<style>
	.panel {
		border: 1px solid var(--line);
		padding: 10px 12px;
		background: var(--bone);
	}
	.panel-head {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 8px;
		margin-bottom: 6px;
	}
	.direction {
		font-weight: 600;
		font-size: 0.95rem;
		color: var(--graphite-soft);
	}
	.direction.up {
		color: var(--olive-deep);
	}
	.direction.down {
		color: var(--ember);
	}
	.n {
		margin-left: 5px;
	}
	svg {
		width: 100%;
		height: auto;
		display: block;
	}
	.tick {
		font-family: var(--font-mono);
		font-size: 9px;
		fill: var(--graphite-soft);
	}
	.empty {
		margin: 18px 0;
		text-align: center;
	}
</style>
