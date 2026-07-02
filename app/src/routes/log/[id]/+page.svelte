<script lang="ts">
	import { methodById, methodLabel } from '$lib/domain/methods';
	import { ILLUSTRATIONS } from '$lib/components/ink';
	import Stamp from '$lib/components/ui/Stamp.svelte';
	import ZoneChip from '$lib/components/ui/ZoneChip.svelte';
	import Squiggle from '$lib/components/ui/Squiggle.svelte';
	import { grams, pct, ratioLabel, score1, weekdayDay } from '$lib/format';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const brew = $derived(data.brew);
	const metrics = $derived(data.derived);
	const Ink = $derived.by(() => {
		const key = methodById(brew.method)?.illustration;
		return key ? ILLUSTRATIONS[key] : null;
	});

	const BOOL_HINTS = ['swirl', 'stir', 'valve', 'skim', 'break', 'water_before', 'orientation'];

	function paramLabel(key: string): string {
		return key
			.replace(/^(v60|hario|aeropress|frenchpress|espresso|brew)_/, '')
			.replaceAll('_', ' ')
			.replace(/\bs$/, '(s)');
	}

	function paramValue(key: string, value: string | number): string {
		if (typeof value === 'number' && (value === 0 || value === 1)) {
			if (BOOL_HINTS.some((h) => key.includes(h)) && key !== 'aeropress_orientation') {
				return value === 1 ? 'yes' : 'no';
			}
		}
		return String(value);
	}

	function timeLabel(seconds: number | null): string {
		if (seconds === null) return '—';
		const m = Math.floor(seconds / 60);
		const s = Math.round(seconds % 60);
		return `${m}:${String(s).padStart(2, '0')}`;
	}

	const factors = $derived([
		{ name: 'Complexity', value: brew.scoreComplexity },
		{ name: 'Bitterness', value: brew.scoreBitterness },
		{ name: 'Mouthfeel', value: brew.scoreMouthfeel }
	]);

	function dots(value: number | null): string {
		if (value === null) return '·····';
		const full = Math.round(value);
		return '●'.repeat(full) + '○'.repeat(Math.max(0, 5 - full));
	}
</script>

<svelte:head><title>The Counter — cup Nº {brew.id}</title></svelte:head>

<a href="/log" class="micro back">← Back to the log</a>

<article class="label">
	<header>
		<div class="corners micro">
			<span>Cup Nº {String(brew.id).padStart(3, '0')}</span>
			<span>{weekdayDay(brew.brewedAt)} · {methodLabel(brew.method)}</span>
		</div>
		<div class="title-row">
			<div>
				<h2 class="etch bean">{data.bean?.name ?? 'Unnamed cup'}</h2>
				{#if data.bean?.originCountry}
					<p class="label-caps origin">
						{data.bean.originCountry}{data.bean.originRegion ? ` — ${data.bean.originRegion}` : ''}
					</p>
				{/if}
				<p class="micro bean-meta">
					{[data.bean?.process, data.bean?.roastLevel, data.bean?.variety]
						.filter(Boolean)
						.join(' · ') || 'No bag details recorded'}
				</p>
			</div>
			{#if Ink}
				<div class="illustration"><Ink size={84} /></div>
			{/if}
		</div>
	</header>

	<div class="rule-press" role="presentation"></div>

	<dl class="specs num">
		<div><dt class="micro">Dose</dt><dd>{grams(brew.doseG)}</dd></div>
		<div><dt class="micro">Water</dt><dd>{grams(brew.waterG)}</dd></div>
		<div><dt class="micro">Temp</dt><dd>{brew.tempC === null ? '—' : `${brew.tempC}°C`}</dd></div>
		<div><dt class="micro">Grind</dt><dd>{brew.grindSize ?? '—'}</dd></div>
		<div><dt class="micro">Ratio</dt><dd>{ratioLabel(metrics.ratio)}</dd></div>
		<div><dt class="micro">Time</dt><dd>{timeLabel(brew.totalTimeS)}</dd></div>
		{#if brew.iceG !== null || brew.hotWaterG !== null}
			<div><dt class="micro">Hot water</dt><dd>{grams(brew.hotWaterG)}</dd></div>
			<div><dt class="micro">Ice</dt><dd>{grams(brew.iceG)}</dd></div>
		{/if}
	</dl>

	<div class="measure">
		<div class="tds-ey num">
			<span><span class="micro">TDS</span> {brew.tdsPercent === null ? '—' : `${brew.tdsPercent}%`}</span>
			<span class="arrow" aria-hidden="true">→</span>
			<span><span class="micro">Extraction</span> {pct(metrics.extractionYieldPercent)}</span>
		</div>
		<div class="zone">
			{#if metrics.zone === 'Ideal-Ideal'}
				<Stamp top="Ideal" bottom="zone" ringTop={`Nº ${String(brew.id).padStart(3, '0')}`} ringBottom="18–22% EY" size={92} />
			{:else if metrics.extraction && metrics.strength}
				<div class="chips">
					<ZoneChip zone={metrics.extraction.toLowerCase() as 'under' | 'ideal' | 'over'} />
					<ZoneChip zone={metrics.strength.toLowerCase() as 'weak' | 'ideal' | 'strong'} />
				</div>
			{:else}
				<p class="micro">No refractometer reading</p>
			{/if}
		</div>
	</div>

	<div class="scores">
		<div class="factors num">
			{#each factors as factor (factor.name)}
				<div class="factor">
					<span class="micro">{factor.name}</span>
					<span class="dots">{dots(factor.value)}</span>
				</div>
			{/each}
		</div>
		<div class="totals num">
			<div><span class="micro">Overall</span><span class="big">{score1(metrics.overall)}</span></div>
			<div><span class="micro">Brew score</span><span class="big">{score1(metrics.brewScore)}</span></div>
		</div>
	</div>

	{#if brew.tastingNotes}
		<div class="notes">
			<p class="etch-italic">{brew.tastingNotes}</p>
			<Squiggle kind="underline" width={160} />
		</div>
	{/if}

	{#if Object.keys(data.methodParams).length > 0}
		<details>
			<summary class="micro">Technique record</summary>
			<dl class="params num">
				{#each Object.entries(data.methodParams) as [key, value] (key)}
					<div><dt class="micro">{paramLabel(key)}</dt><dd>{paramValue(key, value)}</dd></div>
				{/each}
			</dl>
		</details>
	{/if}

	{#if brew.notes}
		<p class="general-notes micro">{brew.notes}</p>
	{/if}

	<footer>
		<span class="micro">Single origin · brewed at home · lot {String(brew.id).padStart(3, '0')}</span>
		<span class="barcode" aria-hidden="true">
			{#each [2, 1, 3, 1, 2, 4, 1, 2, 1, 3] as w, i (i)}
				<span style:width="{w}px"></span>
			{/each}
		</span>
	</footer>
</article>

<style>
	.back {
		text-decoration: none;
		color: var(--ink-soft);
	}
	.label {
		border: 2px solid var(--ink);
		background: var(--paper-bright);
		padding: 22px 24px;
		margin-top: 12px;
	}
	.corners {
		display: flex;
		justify-content: space-between;
		gap: 12px;
	}
	.title-row {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 18px;
		margin-top: 12px;
	}
	.bean {
		font-size: 2.2rem;
		font-weight: 480;
		margin: 0;
		line-height: 1;
	}
	.origin {
		font-size: 0.8rem;
		letter-spacing: 0.2em;
		margin: 8px 0 0;
		color: var(--roast);
	}
	.bean-meta {
		margin: 6px 0 0;
	}
	.illustration {
		flex: none;
	}
	.rule-press {
		margin: 16px 0;
	}
	.specs {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
		gap: 10px 14px;
		margin: 0;
	}
	.specs dt {
		margin-bottom: 2px;
	}
	.specs dd {
		margin: 0;
		font-size: 1rem;
		font-weight: 600;
	}
	.measure {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 16px;
		border-top: 1px dashed var(--line-soft);
		margin-top: 16px;
		padding-top: 14px;
	}
	.tds-ey {
		display: flex;
		align-items: baseline;
		gap: 12px;
		font-size: 1.3rem;
		font-weight: 600;
	}
	.tds-ey .micro {
		display: block;
		margin-bottom: 2px;
	}
	.arrow {
		color: var(--clay);
	}
	.chips {
		display: flex;
		gap: 6px;
	}
	.scores {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 16px;
		border-top: 1px dashed var(--line-soft);
		margin-top: 14px;
		padding-top: 14px;
	}
	.factor {
		display: flex;
		justify-content: space-between;
		gap: 14px;
		font-size: 0.8rem;
		line-height: 1.9;
	}
	.factor .dots {
		letter-spacing: 3px;
	}
	.totals {
		display: flex;
		gap: 22px;
		text-align: right;
	}
	.totals .micro {
		display: block;
	}
	.totals .big {
		font-size: 1.5rem;
		font-weight: 600;
	}
	.notes {
		margin-top: 16px;
	}
	.notes p {
		font-size: 1.25rem;
		margin: 0 0 2px;
		color: #3b3227;
	}
	details {
		margin-top: 16px;
	}
	summary {
		cursor: pointer;
	}
	.params {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 8px 14px;
		margin: 10px 0 0;
	}
	.params dd {
		margin: 0;
		font-size: 0.85rem;
		font-weight: 600;
	}
	.general-notes {
		margin: 14px 0 0;
	}
	footer {
		display: flex;
		justify-content: space-between;
		align-items: flex-end;
		border-top: 1px dashed var(--line-soft);
		margin-top: 18px;
		padding-top: 12px;
	}
	.barcode {
		display: inline-flex;
		gap: 2px;
		align-items: flex-end;
	}
	.barcode span {
		height: 18px;
		background: var(--ink);
		display: inline-block;
	}
</style>
