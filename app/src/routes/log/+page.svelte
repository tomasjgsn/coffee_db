<script lang="ts">
	import { goto } from '$app/navigation';
	import { methodShortLabel } from '$lib/domain/methods';
	import { dayNumber, monthHeading, pct, score1 } from '$lib/format';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const groups = $derived.by(() => {
		const map = new Map<string, typeof data.brews>();
		for (const brew of data.brews) {
			const key = monthHeading(brew.brewedAt);
			const group = map.get(key) ?? [];
			group.push(brew);
			map.set(key, group);
		}
		return [...map.entries()];
	});

	/** Zone as cast light: a small radial glow tick, not a paint dot. */
	function zoneGlow(zone: string | null): string {
		if (zone === 'Ideal-Ideal')
			return 'radial-gradient(circle at 40% 35%, #fdf6d8, var(--olive) 65%, var(--olive-deep))';
		if (zone?.startsWith('Under'))
			return 'radial-gradient(circle at 40% 35%, #fdeecd, var(--amber) 65%, var(--amber-deep))';
		if (zone?.startsWith('Over'))
			return 'radial-gradient(circle at 40% 35%, #f3c4b8, var(--ember) 60%, var(--ember-deep))';
		if (zone) return 'radial-gradient(circle at 40% 35%, var(--chrome-2), var(--graphite-soft))';
		return 'var(--line)';
	}

	function applyFilter(kind: 'bean' | 'method', value: string) {
		const params = new URLSearchParams();
		const bean = kind === 'bean' ? value : (data.beanFilter ?? '');
		const method = kind === 'method' ? value : (data.methodFilter ?? '');
		if (bean) params.set('bean', bean);
		if (method) params.set('method', method);
		goto(`/log${params.size > 0 ? `?${params}` : ''}`, { keepFocus: true });
	}
</script>

<svelte:head><title>The Counter: log</title></svelte:head>

<div class="head">
	<div>
		<h2 class="label-caps page-title">The log</h2>
		<p class="micro">{data.brews.length} of {data.total} cups</p>
	</div>
	<div class="filters">
		<select
			class="micro"
			value={data.beanFilter ?? ''}
			onchange={(e) => applyFilter('bean', e.currentTarget.value)}
			aria-label="Filter by bean"
		>
			<option value="">All beans</option>
			{#each data.beanOptions as bean (bean)}
				<option value={bean}>{bean}</option>
			{/each}
		</select>
		<select
			class="micro"
			value={data.methodFilter ?? ''}
			onchange={(e) => applyFilter('method', e.currentTarget.value)}
			aria-label="Filter by method"
		>
			<option value="">All methods</option>
			{#each data.methodOptions as method (method)}
				<option value={method}>{methodShortLabel(method)}</option>
			{/each}
		</select>
	</div>
</div>

<div class="chrome-rule" role="presentation"></div>

{#each groups as [month, brews] (month)}
	<section>
		<h3 class="micro month">{month.toLowerCase()}</h3>
		<ul>
			{#each brews as brew (brew.id)}
				<li>
					<a href="/log/{brew.id}">
						<span class="day num">{dayNumber(brew.brewedAt)}</span>
						<span class="glow" style:background={zoneGlow(brew.derived.zone)} aria-hidden="true"
						></span>
						<span class="bean-name">{brew.beanName ?? 'Unnamed cup'}</span>
						<span class="micro method">{methodShortLabel(brew.method).toLowerCase()}</span>
						<span class="reading num">
							{pct(brew.derived.extractionYieldPercent)} · {score1(brew.derived.overall)}
						</span>
					</a>
				</li>
			{/each}
		</ul>
	</section>
{/each}

{#if data.brews.length === 0}
	<p class="empty">No brews match</p>
{/if}

<style>
	.head {
		display: flex;
		justify-content: space-between;
		align-items: flex-end;
		gap: 16px;
		margin-bottom: 12px;
	}
	.page-title {
		font-size: 1.4rem;
		margin: 0 0 4px;
	}
	.head p {
		margin: 0;
	}
	.filters {
		display: flex;
		gap: 8px;
	}
	select {
		background: var(--bone);
		border: 1px solid var(--line);
		color: var(--graphite);
		padding: 6px 8px;
		max-width: 180px;
	}
	section {
		margin-top: 22px;
	}
	.month {
		border-bottom: 1px solid var(--line-strong);
		padding-bottom: 5px;
		margin: 0 0 2px;
	}
	ul {
		list-style: none;
		margin: 0;
		padding: 0;
	}
	li a {
		display: flex;
		align-items: baseline;
		gap: 12px;
		padding: 8px 4px;
		color: inherit;
		text-decoration: none;
		border-bottom: 1px solid var(--line);
	}
	li a:hover {
		background: var(--bone-warm);
	}
	.day {
		flex: none;
		width: 1.6em;
		text-align: right;
		font-size: 0.75rem;
		color: var(--graphite-soft);
	}
	.glow {
		flex: none;
		width: 9px;
		height: 9px;
		border-radius: 50%;
		transform: translateY(-1px);
	}
	.bean-name {
		font-weight: 500;
		font-size: 0.95rem;
		letter-spacing: -0.01em;
	}
	.method {
		flex: 1;
	}
	.reading {
		font-weight: 600;
		font-size: 0.8125rem;
		white-space: nowrap;
	}
	.empty {
		text-align: center;
		font-size: 1rem;
		color: var(--graphite-soft);
		padding: 40px 0;
	}
</style>
