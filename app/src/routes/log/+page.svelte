<script lang="ts">
	import { goto } from '$app/navigation';
	import { methodShortLabel } from '$lib/domain/methods';
	import { dayNumber, monthHeading, pct, score1 } from '$lib/format';
	import DottedRow from '$lib/components/ui/DottedRow.svelte';
	import CheckerStrip from '$lib/components/ui/CheckerStrip.svelte';
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

	function zoneColor(zone: string | null): string {
		if (zone === 'Ideal-Ideal') return 'var(--leaf)';
		if (zone?.startsWith('Under')) return 'var(--ochre)';
		if (zone?.startsWith('Over')) return 'var(--clay)';
		if (zone) return 'var(--roast)';
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

<svelte:head><title>The Counter — the log</title></svelte:head>

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
			<option value="">Every bean</option>
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
			<option value="">Every method</option>
			{#each data.methodOptions as method (method)}
				<option value={method}>{methodShortLabel(method)}</option>
			{/each}
		</select>
	</div>
</div>

<CheckerStrip squares={60} size={8} />

{#each groups as [month, brews] (month)}
	<section>
		<h3 class="micro month">{month}</h3>
		<ul>
			{#each brews as brew (brew.id)}
				<li>
					<a href="/log/{brew.id}">
						<span class="day num">{dayNumber(brew.brewedAt)}</span>
						<span class="dot" style:background={zoneColor(brew.derived.zone)} aria-hidden="true"
						></span>
						<span class="row-body">
							<DottedRow>
								{#snippet left()}
									<span class="etch bean-name">{brew.beanName ?? 'Unnamed cup'}</span>
									<span class="micro method">{methodShortLabel(brew.method)}</span>
								{/snippet}
								{#snippet right()}
									{pct(brew.derived.extractionYieldPercent)} · {score1(brew.derived.overall)}
								{/snippet}
							</DottedRow>
						</span>
					</a>
				</li>
			{/each}
		</ul>
	</section>
{/each}

{#if data.brews.length === 0}
	<p class="etch-italic empty">Nothing on the menu — pour something.</p>
{/if}

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
	.filters {
		display: flex;
		gap: 8px;
	}
	select {
		background: var(--paper-bright);
		border: 1px solid var(--line);
		color: var(--ink);
		padding: 6px 8px;
		max-width: 180px;
	}
	section {
		margin-top: 22px;
	}
	.month {
		border-bottom: 1px solid var(--ink);
		padding-bottom: 5px;
		margin: 0 0 6px;
		font-weight: 500;
	}
	ul {
		list-style: none;
		margin: 0;
		padding: 0;
	}
	li a {
		display: flex;
		align-items: baseline;
		gap: 10px;
		padding: 7px 4px;
		color: inherit;
		text-decoration: none;
		border-bottom: 1px dashed color-mix(in srgb, var(--line) 50%, transparent);
	}
	li a:hover {
		background: var(--paper-bright);
	}
	.day {
		flex: none;
		width: 1.6em;
		text-align: right;
		font-size: 0.75rem;
		color: var(--ink-soft);
	}
	.dot {
		flex: none;
		width: 9px;
		height: 9px;
		border-radius: 50%;
		transform: translateY(-1px);
	}
	.row-body {
		flex: 1;
		min-width: 0;
	}
	.bean-name {
		font-size: 1.05rem;
	}
	.method {
		margin-left: 6px;
	}
	.empty {
		text-align: center;
		font-size: 1.25rem;
		color: var(--roast);
		padding: 40px 0;
	}
</style>
