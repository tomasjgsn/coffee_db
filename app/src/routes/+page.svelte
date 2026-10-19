<script lang="ts">
	import { methodLabel, methodShortLabel } from '$lib/domain/methods';
	import { pct, score1, weekdayDay } from '$lib/format';
	import { Medallion, Mark, Kettle, Drop, Eye, Prism, Habitat } from '$lib/components/engravings';
	import type { Component } from 'svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const MEDAL_ART: Record<string, Component> = {
		count: Drop,
		'dialed-in': Eye,
		best: Prism,
		streak: Habitat
	};
</script>

<svelte:head><title>The Counter: today</title></svelte:head>

<div class="lead">
	<h2 class="label-caps page-title">Today</h2>
	<a class="field-red pour" href="/brew">Start brew</a>
</div>

{#if data.drafts.length > 0}
	<section class="drafts">
		<h3 class="micro section">Open drafts</h3>
		{#each data.drafts as draft (draft.id)}
			<div class="draft">
				<span class="lamp" aria-hidden="true"></span>
				<span class="name">{draft.beanName ?? 'Unnamed cup'}</span>
				<span class="micro">{methodShortLabel(draft.method).toLowerCase()}, {weekdayDay(draft.brewedAt).toLowerCase()}</span>
				<span class="spacer"></span>
				<a class="micro resume hit" href="/brew/{draft.id}/live">timer</a>
				<a class="micro resume taste hit" href="/brew/{draft.id}/taste">taste</a>
			</div>
		{/each}
	</section>
{/if}

{#if data.again.length > 0}
	<section>
		<h3 class="micro section">Brew again</h3>
		<div class="again-row">
			{#each data.again as item (item.id)}
				<a class="again" href="/brew?bean={item.beanId}&method={item.method}">
					<span class="name">{item.beanName}</span>
					<span class="micro">{methodLabel(item.method).toLowerCase()}, last {score1(item.derived.overall)}</span>
				</a>
			{/each}
		</div>
	</section>
{/if}

<section>
	<h3 class="micro section">Poured today</h3>
	{#if data.todaysCups.length === 0}
		<div class="empty">
			<Mark size={72} label="kettle">
				<Kettle />
			</Mark>
			<p>No brews today</p>
		</div>
	{:else}
		<div class="menu">
			{#each data.todaysCups as cup (cup.id)}
				<a href="/log/{cup.id}" class="menu-link">
					<span class="name">{cup.beanName ?? 'Unnamed cup'}</span>
					<span class="micro">{methodShortLabel(cup.method).toLowerCase()}</span>
					<span class="spacer"></span>
					<span class="num reading">
						{pct(cup.derived.extractionYieldPercent)} · {score1(cup.derived.overall)}
					</span>
				</a>
			{/each}
		</div>
	{/if}
</section>

{#if data.milestones.length > 0}
	<section>
		<h3 class="micro section">Medals</h3>
		<div class="medals">
			{#each data.milestones as milestone (milestone.kind + milestone.label)}
				{@const Art = MEDAL_ART[milestone.kind] ?? Drop}
				<Medallion label={milestone.label.toLowerCase()} sub={milestone.sub}>
					<Art />
				</Medallion>
			{/each}
		</div>
	</section>
{/if}

<style>
	.lead {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 16px;
		margin-bottom: 20px;
	}
	.page-title {
		font-size: 1.4rem;
		margin: 0;
	}
	.pour {
		text-decoration: none;
	}
	section {
		margin-bottom: 24px;
	}
	.section {
		border-bottom: 1px solid var(--line-strong);
		padding-bottom: 5px;
		margin: 0 0 10px;
	}
	.drafts .draft {
		display: flex;
		align-items: baseline;
		gap: 10px;
		border: 1px solid var(--line);
		border-left: 2px solid var(--graphite-soft);
		padding: 9px 12px;
		margin-bottom: 6px;
		background: var(--bone);
	}
	.lamp {
		flex: none;
		width: 8px;
		height: 8px;
		border-radius: 50%;
		align-self: center;
		/* An open draft is a dim chrome lamp: amber is reserved for under-extraction. */
		background: radial-gradient(circle at 35% 30%, var(--chrome-2), var(--chrome-3) 55%, var(--graphite-soft));
	}
	.name {
		font-weight: 500;
		font-size: 0.95rem;
		letter-spacing: -0.01em;
	}
	.spacer {
		flex: 1;
	}
	.resume {
		color: var(--graphite);
		font-weight: 600;
	}
	.resume.taste {
		color: var(--ember);
		/* Keeps the two links' 44px hit areas apart. */
		margin-left: 2px;
	}
	.again-row {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
		gap: 10px;
	}
	.again {
		display: flex;
		flex-direction: column;
		gap: 3px;
		border: 1px solid var(--line);
		background: var(--bone);
		padding: 11px 12px;
		text-decoration: none;
		color: inherit;
	}
	.again:hover {
		border-color: var(--line-strong);
		background: var(--bone-warm);
	}
	.menu-link {
		display: flex;
		align-items: baseline;
		gap: 10px;
		color: inherit;
		text-decoration: none;
		padding: 8px 2px;
		border-bottom: 1px solid var(--line);
	}
	.menu-link:hover {
		background: var(--bone-warm);
	}
	.reading {
		font-weight: 600;
		font-size: 0.8125rem;
	}
	.empty {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 6px;
		padding: 22px 0;
	}
	.empty p {
		margin: 0;
		font-size: 0.95rem;
		color: var(--graphite-soft);
	}
	.medals {
		display: flex;
		gap: 18px;
		align-items: flex-start;
		flex-wrap: wrap;
	}
</style>
