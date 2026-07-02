<script lang="ts">
	import { methodLabel, methodShortLabel } from '$lib/domain/methods';
	import { pct, score1, weekdayDay } from '$lib/format';
	import DottedRow from '$lib/components/ui/DottedRow.svelte';
	import PerfToken from '$lib/components/ui/PerfToken.svelte';
	import StampBadge from '$lib/components/ui/StampBadge.svelte';
	import CheckerStrip from '$lib/components/ui/CheckerStrip.svelte';
	import { Kettle } from '$lib/components/ink';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
</script>

<svelte:head><title>The Counter — today</title></svelte:head>

<div class="lead">
	<div>
		<h2 class="label-caps page-title">Today</h2>
		<p class="etch-italic sub">what's pouring at the counter</p>
	</div>
	<a class="pour label-caps" href="/brew">Put the kettle on →</a>
</div>

{#if data.drafts.length > 0}
	<section class="drafts">
		<h3 class="micro section">Open drafts — cups waiting on you</h3>
		{#each data.drafts as draft (draft.id)}
			<div class="draft">
				<span class="etch name">{draft.beanName ?? 'Unnamed cup'}</span>
				<span class="micro">{methodShortLabel(draft.method)} · {weekdayDay(draft.brewedAt)}</span>
				<span class="spacer"></span>
				<a class="micro resume" href="/brew/{draft.id}/live">timer</a>
				<a class="micro resume taste" href="/brew/{draft.id}/taste">taste it →</a>
			</div>
		{/each}
	</section>
{/if}

{#if data.again.length > 0}
	<section>
		<h3 class="micro section">Pour it again</h3>
		<div class="again-row">
			{#each data.again as item (item.id)}
				<a class="again" href="/brew?bean={item.beanId}&method={item.method}">
					<span class="etch name">{item.beanName}</span>
					<span class="micro">{methodLabel(item.method)} · last {score1(item.derived.overall)}</span>
				</a>
			{/each}
		</div>
	</section>
{/if}

<section>
	<h3 class="micro section">Today's pours</h3>
	{#if data.todaysCups.length === 0}
		<div class="empty">
			<Kettle size={64} />
			<p class="etch-italic">Nothing poured yet — the kettle's cold.</p>
		</div>
	{:else}
		<div class="menu">
			{#each data.todaysCups as cup (cup.id)}
				<a href="/log/{cup.id}" class="menu-link">
					<DottedRow>
						{#snippet left()}
							<span class="etch name">{cup.beanName ?? 'Unnamed cup'}</span>
							<span class="micro">{methodShortLabel(cup.method)}</span>
						{/snippet}
						{#snippet right()}
							{pct(cup.derived.extractionYieldPercent)} · {score1(cup.derived.overall)}
						{/snippet}
					</DottedRow>
				</a>
			{/each}
		</div>
	{/if}
</section>

{#if data.milestones.length > 0}
	<section>
		<h3 class="micro section">The stamp collection</h3>
		<div class="stamps">
			{#each data.milestones as milestone (milestone.kind + milestone.label)}
				{#if milestone.kind === 'count'}
					<PerfToken lines={milestone.label.split(' ')} />
				{:else if milestone.kind === 'best'}
					<StampBadge text={milestone.label} color="var(--clay)" />
				{:else if milestone.kind === 'streak'}
					<StampBadge text={milestone.label} color="var(--roast)" rotate={2} />
				{:else}
					<StampBadge text={milestone.label} color="var(--leaf)" rotate={-2} />
				{/if}
			{/each}
		</div>
	</section>
{/if}

<div class="foot"><CheckerStrip squares={60} size={8} /></div>

<style>
	.lead {
		display: flex;
		justify-content: space-between;
		align-items: flex-end;
		gap: 16px;
		margin-bottom: 20px;
	}
	.page-title {
		font-size: 1.4rem;
		margin: 0 0 4px;
	}
	.sub {
		margin: 0;
		font-size: 1.1rem;
		color: var(--roast);
	}
	.pour {
		background: var(--ink);
		color: var(--paper);
		text-decoration: none;
		font-size: 0.75rem;
		padding: 12px 18px;
	}
	.pour:hover {
		background: var(--roast);
	}
	section {
		margin-bottom: 22px;
	}
	.section {
		border-bottom: 1px solid var(--ink);
		padding-bottom: 5px;
		margin: 0 0 10px;
		font-weight: 500;
	}
	.drafts .draft {
		display: flex;
		align-items: baseline;
		gap: 10px;
		background: var(--ochre-wash);
		border: 1px solid var(--ochre);
		padding: 9px 12px;
		margin-bottom: 6px;
	}
	.name {
		font-size: 1.05rem;
	}
	.spacer {
		flex: 1;
	}
	.resume {
		color: var(--ink);
		font-weight: 600;
	}
	.resume.taste {
		color: var(--clay-deep);
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
		border: 1.5px solid var(--line);
		background: var(--paper-bright);
		padding: 11px 12px;
		text-decoration: none;
		color: inherit;
	}
	.again:hover {
		border-color: var(--ink);
	}
	.menu-link {
		display: block;
		color: inherit;
		text-decoration: none;
		padding: 6px 2px;
	}
	.menu-link:hover {
		background: var(--paper-bright);
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
		font-size: 1.15rem;
		color: var(--roast);
	}
	.stamps {
		display: flex;
		gap: 14px;
		align-items: center;
		flex-wrap: wrap;
	}
	.foot {
		margin-top: 26px;
	}
</style>
