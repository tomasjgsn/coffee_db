<script lang="ts">
	import ControlChart from '$lib/components/charts/ControlChart.svelte';
	import Squiggle from '$lib/components/ui/Squiggle.svelte';
	import { score1 } from '$lib/format';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	let dialInBean = $state('');

	const shownPoints = $derived(
		dialInBean === ''
			? data.points
			: data.points.filter((p) => p.beanName === dialInBean)
	);

	const trendPath = $derived.by(() => {
		if (data.trend.length < 2) return null;
		const w = 240;
		const h = 56;
		const min = Math.min(...data.trend.map((t) => t.score));
		const max = Math.max(...data.trend.map((t) => t.score));
		const span = Math.max(0.5, max - min);
		return data.trend
			.map((t, i) => {
				const px = (i / (data.trend.length - 1)) * (w - 8) + 4;
				const py = h - 6 - ((t.score - min) / span) * (h - 12);
				return `${i === 0 ? 'M' : 'L'}${px.toFixed(1)},${py.toFixed(1)}`;
			})
			.join(' ');
	});
</script>

<svelte:head><title>The Counter — the chart</title></svelte:head>

<div class="head">
	<div>
		<h2 class="label-caps page-title">The chart</h2>
		<p class="micro">{shownPoints.length} measured cups{dialInBean ? ` · ${dialInBean}` : ''}</p>
	</div>
	<label class="dial-in">
		<span class="micro">Dial-in journey</span>
		<select bind:value={dialInBean} class="micro">
			<option value="">All beans</option>
			{#each data.beans as bean (bean)}
				<option value={bean}>{bean}</option>
			{/each}
		</select>
	</label>
</div>

<div class="chart-frame">
	<ControlChart points={shownPoints} connect={dialInBean !== ''} />
	{#if dialInBean}
		<p class="etch-italic journey-note">each dotted step is the next brew of this bag — walking it into the box</p>
	{/if}
</div>

<div class="stats">
	<div class="stat">
		<span class="micro">Ideal-zone hit rate · last 10</span>
		<span class="num big">{data.hitRateNow === null ? '—' : `${data.hitRateNow}%`}</span>
		{#if data.hitRateBefore !== null && data.hitRateNow !== null}
			<span class="num delta" class:up={data.hitRateNow >= data.hitRateBefore}>
				{data.hitRateNow >= data.hitRateBefore ? '↗' : '↘'} was {data.hitRateBefore}%
			</span>
		{/if}
	</div>
	<div class="stat">
		<span class="micro">Average score · last 10</span>
		<span class="num big">{score1(data.avgScoreNow)}</span>
	</div>
	<div class="stat trend">
		<span class="micro">Every scored cup, oldest → newest</span>
		{#if trendPath}
			<svg viewBox="0 0 240 56" aria-label="Score trend across all cups">
				<path d={trendPath} fill="none" stroke="var(--roast)" stroke-width="1.5" />
			</svg>
		{:else}
			<span class="micro">Not enough scored cups yet</span>
		{/if}
		<Squiggle kind="underline" width={110} />
	</div>
</div>

<style>
	.head {
		display: flex;
		justify-content: space-between;
		align-items: flex-end;
		gap: 16px;
		margin-bottom: 14px;
	}
	.page-title {
		font-size: 1.4rem;
		margin: 0 0 4px;
	}
	.head p {
		margin: 0;
	}
	.dial-in {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	select {
		background: var(--paper-bright);
		border: 1px solid var(--line);
		color: var(--ink);
		padding: 6px 8px;
		max-width: 200px;
	}
	.chart-frame {
		border: 2px solid var(--ink);
		background: var(--paper-bright);
		padding: 14px;
	}
	.journey-note {
		margin: 8px 4px 0;
		font-size: 1.05rem;
		color: var(--roast);
	}
	.stats {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 12px;
		margin-top: 14px;
	}
	.stat {
		border: 1px solid var(--line);
		padding: 12px 14px;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.stat .big {
		font-size: 1.7rem;
		font-weight: 600;
	}
	.delta {
		font-size: 0.75rem;
		color: var(--clay-deep);
	}
	.delta.up {
		color: var(--leaf-deep);
	}
	.trend svg {
		width: 100%;
		height: 56px;
	}
</style>
