<script lang="ts">
	import { score1, weekdayDay } from '$lib/format';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	function bagDots(item: (typeof data.shelf)[number]): { filled: number; total: number } | null {
		const size = item.bean.bagSizeG;
		if (!size) return null;
		const used = Math.min(1, item.dosedGrams / size);
		const total = 8;
		return { filled: Math.round(used * total), total };
	}

	function remaining(item: (typeof data.shelf)[number]): number | null {
		const size = item.bean.bagSizeG;
		if (!size) return null;
		return Math.max(0, Math.round(size - item.dosedGrams));
	}
</script>

<svelte:head><title>The Counter — the shelf</title></svelte:head>

<h2 class="label-caps page-title">The shelf</h2>
<p class="micro subtitle">{data.shelf.length} bags · newest pour first</p>

<div class="grid">
	{#each data.shelf as item (item.bean.id)}
		<article class="bag">
			<div class="bag-head">
				<span class="label-caps country">{item.bean.originCountry ?? 'Origin unknown'}</span>
				{#if item.bean.process}
					<span class="process">{item.bean.process}</span>
				{/if}
			</div>
			<h3 class="etch name">{item.bean.name}</h3>
			{#if item.bean.originRegion}
				<p class="micro region">{item.bean.originRegion}</p>
			{/if}
			<div class="rule" role="presentation"></div>
			<dl class="stats num">
				<div><dt class="micro">Roast</dt><dd>{item.bean.roastDate ?? '—'}</dd></div>
				<div><dt class="micro">Brews</dt><dd>{item.brewCount}</dd></div>
				<div><dt class="micro">Best</dt><dd>{score1(item.bestScore)}</dd></div>
				<div><dt class="micro">Avg</dt><dd>{score1(item.avgOverall)}</dd></div>
			</dl>
			{#if bagDots(item)}
				{@const dots = bagDots(item)!}
				<div class="level" title="{remaining(item)}g left of {item.bean.bagSizeG}g">
					{#each { length: dots.total } as _, i (i)}
						<span class:used={i < dots.filled}></span>
					{/each}
					<span class="micro left">~{remaining(item)}g left</span>
				</div>
			{/if}
			{#if item.lastBrewedAt}
				<p class="micro last">Last poured {weekdayDay(item.lastBrewedAt)}</p>
			{/if}
			{#if item.bean.notes}
				<p class="etch-italic bag-notes">{item.bean.notes}</p>
			{/if}
		</article>
	{/each}
</div>

<style>
	.page-title {
		font-size: 1.4rem;
		margin: 0 0 4px;
	}
	.subtitle {
		margin: 0 0 18px;
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
		gap: 14px;
	}
	.bag {
		background: var(--kraft-light);
		border: 2px solid var(--ink);
		padding: 16px;
	}
	.bag-head {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 8px;
	}
	.country {
		font-size: 0.95rem;
		letter-spacing: 0.18em;
	}
	.process {
		border: 1.5px solid var(--leaf);
		color: var(--leaf-deep);
		font-weight: 700;
		font-size: 0.5625rem;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		padding: 3px 6px;
		transform: rotate(3deg);
		flex: none;
	}
	.name {
		font-size: 1.35rem;
		font-weight: 470;
		margin: 6px 0 0;
		line-height: 1.05;
	}
	.region {
		margin: 4px 0 0;
	}
	.rule {
		border-top: 1px dashed var(--line-soft);
		margin: 12px 0;
	}
	.stats {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 6px;
		margin: 0;
	}
	.stats dd {
		margin: 2px 0 0;
		font-size: 0.8rem;
		font-weight: 600;
	}
	.level {
		display: flex;
		align-items: center;
		gap: 4px;
		margin-top: 12px;
	}
	.level span:not(.left) {
		width: 9px;
		height: 9px;
		border-radius: 50%;
		border: 1px solid var(--line-soft);
	}
	.level span.used {
		background: var(--roast);
		border-color: var(--roast);
	}
	.level .left {
		margin-left: 6px;
	}
	.last {
		margin: 10px 0 0;
	}
	.bag-notes {
		font-size: 0.95rem;
		color: #3b3227;
		margin: 10px 0 0;
		line-height: 1.3;
	}
</style>
