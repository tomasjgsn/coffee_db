<script lang="ts">
	import type { ChartPointData } from '../../../routes/chart/+page.server';
	import ZoneChip from '$lib/components/ui/ZoneChip.svelte';
	import { methodById, methodShortLabel } from '$lib/domain/methods';
	import { immersionEY } from '$lib/brewing/rays';
	import { pct, ratioLabel, score1, weekdayDay } from '$lib/format';

	let {
		point,
		x,
		y,
		pinned = false,
		onclose = null
	}: {
		point: ChartPointData;
		x: number;
		y: number;
		pinned?: boolean;
		onclose?: (() => void) | null;
	} = $props();

	const CARD_W = 250;
	const CARD_H = 210;

	const left = $derived(
		typeof window === 'undefined' ? x : Math.min(x + 14, window.innerWidth - CARD_W - 12)
	);
	const top = $derived(
		typeof window === 'undefined' ? y : Math.min(y + 14, window.innerHeight - CARD_H - 12)
	);

	const note = $derived(
		point.tastingNotes && point.tastingNotes.length > 56
			? point.tastingNotes.slice(0, 54) + '…'
			: point.tastingNotes
	);

	// Steeped brews under-read on the percolation formula; show the
	// immersion-convention figure alongside, display-only.
	const immersionReading = $derived.by(() => {
		const category = methodById(point.method)?.category;
		if (category !== 'immersion' && category !== 'hybrid') return null;
		return immersionEY(point.tds, point.waterG, point.doseG);
	});
</script>

<div class="card" class:pinned style:left="{left}px" style:top="{top}px" role="tooltip">
	<div class="corners micro">
		<span>cup {String(point.id).padStart(3, '0')}</span>
		<span>{weekdayDay(point.brewedAt)} · {methodShortLabel(point.method)}</span>
	</div>
	<p class="etch bean">{point.beanName ?? 'Unnamed cup'}</p>
	<p class="num vitals">
		{point.grindSize === null ? '—' : `g${point.grindSize}`} · {point.tempC === null
			? '—'
			: `${point.tempC}°C`} · {ratioLabel(point.ratio)}{point.restDays === null
			? ''
			: ` · rest ${point.restDays}d`}
	</p>
	<div class="reading num">
		<span>{point.tds}% → {pct(point.ey)}</span>
		{#if point.zone === 'Ideal-Ideal'}
			<ZoneChip zone="ideal" />
		{:else if point.zone}
			<span class="micro zone-label">{point.zone}</span>
		{/if}
	</div>
	{#if immersionReading !== null}
		<p class="micro immersion">immersion reading ≈ {pct(immersionReading)}</p>
	{/if}
	<div class="scores num">
		<span><span class="micro">Overall</span> {score1(point.overall)}</span>
		<span><span class="micro">Brew</span> {score1(point.brewScore)}</span>
		{#if point.flavorProfile}<span class="micro profile">{point.flavorProfile}</span>{/if}
	</div>
	{#if note}
		<p class="etch-italic note">{note}</p>
	{/if}
	{#if pinned}
		<div class="pin-row">
			<a href="/log/{point.id}" class="micro open">Open cup</a>
			<button type="button" class="close" onclick={() => onclose?.()} aria-label="Close">×</button>
		</div>
	{/if}
</div>

<style>
	.card {
		position: fixed;
		z-index: 20;
		width: 250px;
		background: var(--paper-bright);
		border: 2px solid var(--ink);
		padding: 10px 12px;
		pointer-events: none;
		box-shadow: 4px 4px 0 color-mix(in srgb, var(--ink) 12%, transparent);
	}
	.card.pinned {
		pointer-events: auto;
	}
	.corners {
		display: flex;
		justify-content: space-between;
		gap: 8px;
		font-size: 0.5625rem;
	}
	.bean {
		font-size: 1.15rem;
		margin: 4px 0 2px;
		line-height: 1;
	}
	.vitals {
		font-size: 0.75rem;
		font-weight: 600;
		color: var(--roast);
		margin: 0 0 6px;
	}
	.reading {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 0.9rem;
		font-weight: 600;
		border-top: 1px dashed var(--line-soft);
		padding-top: 6px;
	}
	.zone-label {
		font-size: 0.5625rem;
	}
	.immersion {
		margin: 4px 0 0;
		color: var(--leaf-deep);
	}
	.scores {
		display: flex;
		align-items: baseline;
		gap: 12px;
		font-size: 0.85rem;
		font-weight: 600;
		margin-top: 5px;
	}
	.profile {
		margin-left: auto;
	}
	.note {
		font-size: 0.95rem;
		color: #3b3227;
		margin: 6px 0 0;
		line-height: 1.2;
	}
	.pin-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		border-top: 1px dashed var(--line-soft);
		margin-top: 8px;
		padding-top: 6px;
	}
	.open {
		color: var(--clay-deep);
		font-weight: 600;
		text-decoration: none;
	}
	.close {
		background: none;
		border: none;
		color: var(--ink-soft);
		font-size: 1rem;
		cursor: pointer;
		padding: 0 2px;
	}
</style>
