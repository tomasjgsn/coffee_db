<script lang="ts">
	import { enhance } from '$app/forms';
	import { METHODS, methodById, methodLabel } from '$lib/domain/methods';
	import { immersionEY } from '$lib/brewing/rays';
	import { ILLUSTRATIONS } from '$lib/components/ink';
	import Stamp from '$lib/components/ui/Stamp.svelte';
	import ZoneChip from '$lib/components/ui/ZoneChip.svelte';
	import Squiggle from '$lib/components/ui/Squiggle.svelte';
	import { grams, pct, ratioLabel, score1, weekdayDay } from '$lib/format';
	import type { PageProps } from './$types';

	import { page } from '$app/state';

	let { data, form: pageForm }: PageProps = $props();

	const stamped = page.url.searchParams.has('stamped');
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

	const immersionReading = $derived.by(() => {
		const category = methodById(brew.method)?.category;
		if (category !== 'immersion' && category !== 'hybrid') return null;
		return immersionEY(brew.tdsPercent, brew.waterG, brew.doseG);
	});

	function dots(value: number | null): string {
		if (value === null) return '·····';
		const full = Math.round(value);
		return '●'.repeat(full) + '○'.repeat(Math.max(0, 5 - full));
	}
</script>

<svelte:head><title>The Counter: cup {brew.id}</title></svelte:head>

<a href="/log" class="micro back">← Log</a>

<article class="label">
	{#if stamped}
		<div class="thunk" aria-hidden="true">
			<Stamp top="Logged" ringTop="The Counter" ringBottom={weekdayDay(brew.brewedAt)} color="var(--clay)" size={104} rotate={8} />
		</div>
	{/if}
	<header>
		<div class="corners micro">
			<span>Cup {String(brew.id).padStart(3, '0')}</span>
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
						.join(' · ') || 'No bag details'}
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
			<span>
				<span class="micro">Extraction</span> {pct(metrics.extractionYieldPercent)}
				{#if immersionReading !== null}
					<span class="micro immersion">immersion reading ≈ {pct(immersionReading)}</span>
				{/if}
			</span>
		</div>
		<div class="zone">
			{#if metrics.zone === 'Ideal-Ideal'}
				<Stamp top="Ideal" bottom="zone" ringTop={`cup ${String(brew.id).padStart(3, '0')}`} ringBottom="18–22% ey" size={92} />
			{:else if metrics.extraction && metrics.strength}
				<div class="chips">
					<ZoneChip zone={metrics.extraction.toLowerCase() as 'under' | 'ideal' | 'over'} />
					<ZoneChip zone={metrics.strength.toLowerCase() as 'weak' | 'ideal' | 'strong'} />
				</div>
			{:else}
				<p class="micro">No reading</p>
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
		<span class="micro">lot {String(brew.id).padStart(3, '0')}</span>
		<span class="barcode" aria-hidden="true">
			{#each [2, 1, 3, 1, 2, 4, 1, 2, 1, 3] as w, i (i)}
				<span style:width="{w}px"></span>
			{/each}
		</span>
	</footer>
</article>

<details class="edit">
	<summary class="micro">Edit record</summary>
	<form method="POST" action="?/update" use:enhance class="edit-form">
		<div class="edit-grid num">
			<label><span class="micro">Method</span>
				<select name="method" value={brew.method}>
					{#if !methodById(brew.method)}<option value={brew.method}>{methodLabel(brew.method)}</option>{/if}
					{#each METHODS as m (m.id)}<option value={m.id}>{m.label}</option>{/each}
				</select>
			</label>
			<label><span class="micro">Dose g</span><input name="doseG" type="number" step="0.1" value={brew.doseG} /></label>
			<label><span class="micro">Water g</span><input name="waterG" type="number" step="1" value={brew.waterG} /></label>
			<label><span class="micro">Temp °C</span><input name="tempC" type="number" step="0.5" value={brew.tempC} /></label>
			<label><span class="micro">Grind</span><input name="grindSize" type="number" step="0.1" value={brew.grindSize} /></label>
			<label><span class="micro">Mug g</span><input name="mugWeightG" type="number" step="0.1" value={brew.mugWeightG} /></label>
			<label><span class="micro">Mug + brew g</span><input name="finalCombinedWeightG" type="number" step="0.1" value={brew.finalCombinedWeightG} /></label>
			<label><span class="micro">Brew mass g</span><input name="brewMassG" type="number" step="0.1" value={brew.brewMassG} /></label>
			<label><span class="micro">TDS %</span><input name="tdsPercent" type="number" step="0.01" value={brew.tdsPercent} /></label>
			<label><span class="micro">Time</span><input name="totalTime" type="text" value={brew.totalTimeS === null ? '' : timeLabel(brew.totalTimeS)} /></label>
			<label><span class="micro">Complexity</span><input name="scoreComplexity" type="number" step="0.5" min="0" max="5" value={brew.scoreComplexity} /></label>
			<label><span class="micro">Bitterness</span><input name="scoreBitterness" type="number" step="0.5" min="0" max="5" value={brew.scoreBitterness} /></label>
			<label><span class="micro">Mouthfeel</span><input name="scoreMouthfeel" type="number" step="0.5" min="0" max="5" value={brew.scoreMouthfeel} /></label>
		</div>
		<label class="edit-notes"><span class="micro">Tasting notes</span><textarea name="tastingNotes" rows="2">{brew.tastingNotes ?? ''}</textarea></label>
		<label class="edit-notes"><span class="micro">Notes</span><textarea name="notes" rows="1">{brew.notes ?? ''}</textarea></label>
		{#if pageForm?.message}<p class="edit-error micro">{pageForm.message}</p>{/if}
		{#if pageForm?.updated}<p class="edit-ok micro">Saved</p>{/if}
		<div class="edit-actions">
			<button type="submit" class="save label-caps">Save</button>
		</div>
	</form>
	<form
		method="POST"
		action="?/remove"
		class="remove-form"
		onsubmit={(e) => {
			if (!confirm(`Delete cup ${brew.id}? This is permanent.`)) e.preventDefault();
		}}
	>
		<button type="submit" class="tear micro">Delete cup</button>
	</form>
</details>

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
		position: relative;
	}
	.thunk {
		position: absolute;
		top: 14px;
		right: 18px;
		z-index: 1;
		animation: thunk 420ms var(--ease-thunk) both;
		pointer-events: none;
	}
	@keyframes thunk {
		0% {
			transform: scale(2.6) rotate(-14deg);
			opacity: 0;
		}
		55% {
			opacity: 1;
		}
		100% {
			transform: scale(1) rotate(0deg);
			opacity: 0.92;
		}
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
	.immersion {
		display: block;
		margin-top: 3px;
		color: var(--leaf-deep);
		text-transform: none;
		letter-spacing: 0.06em;
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
	.edit {
		margin-top: 14px;
	}
	.edit summary {
		cursor: pointer;
	}
	.edit-form {
		border: 1px dashed var(--line-soft);
		padding: 14px;
		margin-top: 8px;
	}
	.edit-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
		gap: 10px;
	}
	.edit-grid label {
		display: flex;
		flex-direction: column;
		gap: 3px;
	}
	.edit-grid input,
	.edit-grid select {
		font-family: var(--font-mono);
		font-weight: 600;
		color: var(--ink);
		background: transparent;
		border: none;
		border-bottom: 1.5px solid var(--line);
		padding: 3px 2px;
	}
	.edit-grid input:focus,
	.edit-grid select:focus {
		outline: none;
		border-bottom-color: var(--ink);
	}
	.edit-notes {
		display: flex;
		flex-direction: column;
		gap: 3px;
		margin-top: 10px;
	}
	.edit-notes textarea {
		font-family: var(--font-etch);
		font-style: italic;
		font-size: 1.05rem;
		background: transparent;
		border: 1px solid var(--line);
		color: #3b3227;
		padding: 6px 8px;
	}
	.edit-error {
		color: var(--clay-deep);
		margin: 10px 0 0;
	}
	.edit-ok {
		color: var(--leaf-deep);
		margin: 10px 0 0;
	}
	.edit-actions {
		margin-top: 12px;
	}
	.save {
		background: var(--ink);
		color: var(--paper);
		border: none;
		font-size: 0.7rem;
		padding: 10px 16px;
		cursor: pointer;
	}
	.remove-form {
		margin-top: 10px;
		text-align: right;
	}
	.tear {
		background: none;
		border: none;
		color: var(--clay-deep);
		text-decoration: underline dashed;
		cursor: pointer;
	}
</style>
