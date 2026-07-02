<script lang="ts">
	import { enhance } from '$app/forms';
	import { methodLabel } from '$lib/domain/methods';
	import { extractionYield, brewingZone, overallRating } from '$lib/brewing/calculations';
	import { pct, score1 } from '$lib/format';
	import FactorDots from '$lib/components/ui/FactorDots.svelte';
	import Squiggle from '$lib/components/ui/Squiggle.svelte';
	import type { PageProps } from './$types';

	let { data, form }: PageProps = $props();

	// svelte-ignore state_referenced_locally
	let tds = $state<number | null>(data.brew.tdsPercent);
	// svelte-ignore state_referenced_locally
	let mugWeight = $state<number | null>(data.brew.mugWeightG);
	// svelte-ignore state_referenced_locally
	let combined = $state<number | null>(data.brew.finalCombinedWeightG);
	// svelte-ignore state_referenced_locally
	let complexity = $state<number | null>(data.brew.scoreComplexity);
	// svelte-ignore state_referenced_locally
	let bitterness = $state<number | null>(data.brew.scoreBitterness);
	// svelte-ignore state_referenced_locally
	let mouthfeel = $state<number | null>(data.brew.scoreMouthfeel);

	const brewMass = $derived(
		mugWeight !== null && combined !== null ? Math.round((combined - mugWeight) * 10) / 10 : data.brew.brewMassG
	);

	const ey = $derived.by(() => {
		if (tds === null || brewMass === null || !data.brew.doseG) return null;
		return extractionYield(brewMass, tds, data.brew.doseG);
	});

	const zone = $derived(tds !== null && ey !== null ? brewingZone(tds, ey) : null);
	const overall = $derived(overallRating(complexity, bitterness, mouthfeel));

	const FLAVOR_PROFILES = ['Bright/Acidic', 'Balanced', 'Rich/Full', 'Sweet', 'Bitter', 'Fruity', 'Nutty', 'Chocolatey'];
	const showTimeFields = $derived(data.manual || data.brew.totalTimeS === null);
</script>

<svelte:head><title>The Counter — taste cup Nº {data.brew.id}</title></svelte:head>

<div class="head">
	<p class="micro">Cup Nº {String(data.brew.id).padStart(3, '0')} · {methodLabel(data.brew.method)} · open draft</p>
	<h2 class="etch bean">{data.bean?.name ?? 'Unnamed cup'}</h2>
</div>

<form method="POST" action="?/save" use:enhance class="sheet">
	<section>
		<span class="micro section-title">The measurements — whenever the sample's cool</span>
		<div class="grid num">
			<label>
				<span class="micro">Mug g</span>
				<input type="number" step="0.1" name="mugWeightG" bind:value={mugWeight} />
			</label>
			<label>
				<span class="micro">Mug + brew g</span>
				<input type="number" step="0.1" name="finalCombinedWeightG" bind:value={combined} />
			</label>
			<div class="readout">
				<span class="micro">Brew mass</span>
				<span class="value">{brewMass === null ? '—' : `${brewMass} g`}</span>
			</div>
			<label>
				<span class="micro">TDS %</span>
				<input type="number" step="0.01" min="0" max="5" name="tdsPercent" bind:value={tds} />
			</label>
		</div>
		{#if showTimeFields}
			<label class="time num">
				<span class="micro">Total time (3:02)</span>
				<input type="text" name="totalTime" placeholder="3:02" size="6" />
			</label>
		{/if}
		<div class="verdict">
			<span class="micro">Extraction</span>
			<span class="num ey">{pct(ey)}</span>
			{#if zone}
				<span
					class="zone-chip num"
					class:ideal={zone === 'Ideal-Ideal'}
					class:under={zone.startsWith('Under')}
					class:over={zone.startsWith('Over')}>{zone}</span
				>
			{/if}
		</div>
	</section>

	<section>
		<span class="micro section-title">The cup — skippable, honest when you do</span>
		<div class="factors">
			<FactorDots name="scoreComplexity" label="Complexity" bind:value={complexity} />
			<FactorDots name="scoreBitterness" label="Bitterness" bind:value={bitterness} />
			<FactorDots name="scoreMouthfeel" label="Mouthfeel" bind:value={mouthfeel} />
		</div>
		<div class="overall num">
			<span class="micro">Overall</span>
			<span class="big">{score1(overall)}</span>
		</div>
		<label class="profile">
			<span class="micro">Flavor profile</span>
			<select name="flavorProfile" value={data.brew.flavorProfile ?? ''}>
				<option value="">—</option>
				{#each FLAVOR_PROFILES as profile (profile)}
					<option value={profile}>{profile}</option>
				{/each}
			</select>
		</label>
		<label class="notes-label">
			<span class="micro">Tasting notes</span>
			<textarea name="tastingNotes" rows="2" placeholder="apricot jam, long finish…"
				>{data.brew.tastingNotes ?? ''}</textarea
			>
		</label>
		<Squiggle kind="underline" width={150} />
		<label class="notes-label">
			<span class="micro">Anything else</span>
			<textarea name="notes" rows="1">{data.brew.notes ?? ''}</textarea>
		</label>
	</section>

	{#if form?.message}<p class="error micro">{form.message}</p>{/if}

	<div class="actions">
		<button class="later micro" type="submit" name="intent" value="draft">Save — taste later</button>
		<button class="stamp label-caps" type="submit" name="intent" value="complete">Stamp it — done</button>
	</div>
</form>

<style>
	.head p {
		margin: 0 0 4px;
	}
	.bean {
		font-size: 1.6rem;
		margin: 0 0 12px;
		line-height: 1;
	}
	.sheet {
		border: 2px solid var(--ink);
		background: var(--paper-bright);
		padding: 20px;
	}
	section + section {
		border-top: 1px dashed var(--line-soft);
		margin-top: 18px;
		padding-top: 16px;
	}
	.section-title {
		display: block;
		margin-bottom: 12px;
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
		gap: 12px;
	}
	.grid label,
	.readout {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.grid input {
		font-family: var(--font-mono);
		font-size: 1.05rem;
		font-weight: 600;
		color: var(--ink);
		background: transparent;
		border: none;
		border-bottom: 2px solid var(--line);
		padding: 4px 2px;
	}
	.grid input:focus {
		outline: none;
		border-bottom-color: var(--ink);
	}
	.readout .value {
		font-size: 1.05rem;
		font-weight: 600;
		padding: 4px 2px;
	}
	.time {
		display: inline-flex;
		flex-direction: column;
		gap: 4px;
		margin-top: 12px;
	}
	.time input {
		font-family: var(--font-mono);
		font-weight: 600;
		background: transparent;
		border: none;
		border-bottom: 2px solid var(--line);
		padding: 4px 2px;
	}
	.verdict {
		display: flex;
		align-items: baseline;
		gap: 12px;
		margin-top: 14px;
	}
	.ey {
		font-size: 1.6rem;
		font-weight: 600;
	}
	.zone-chip {
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		border: 1px solid var(--roast);
		color: var(--roast);
		padding: 3px 8px;
	}
	.zone-chip.ideal {
		background: var(--leaf);
		border-color: var(--leaf);
		color: var(--paper);
	}
	.zone-chip.under {
		border-color: var(--ochre);
		color: var(--ochre-deep);
	}
	.zone-chip.over {
		border-color: var(--clay);
		color: var(--clay-deep);
	}
	.factors {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}
	.overall {
		display: flex;
		align-items: baseline;
		gap: 10px;
		margin-top: 10px;
	}
	.overall .big {
		font-size: 1.4rem;
		font-weight: 600;
	}
	.profile,
	.notes-label {
		display: flex;
		flex-direction: column;
		gap: 4px;
		margin-top: 12px;
	}
	select,
	textarea {
		background: transparent;
		border: 1px solid var(--line);
		color: var(--ink);
		padding: 7px 8px;
	}
	textarea {
		font-family: var(--font-etch);
		font-style: italic;
		font-size: 1.1rem;
		color: #3b3227;
	}
	textarea:focus,
	select:focus {
		outline: none;
		border-color: var(--ink);
	}
	.error {
		color: var(--clay-deep);
		margin: 12px 0 0;
	}
	.actions {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 12px;
		margin-top: 20px;
	}
	.later {
		background: none;
		border: 1px dashed var(--line-soft);
		color: var(--ink-soft);
		padding: 10px 14px;
		cursor: pointer;
	}
	.stamp {
		background: var(--leaf);
		color: var(--paper);
		border: none;
		font-size: 0.85rem;
		padding: 13px 22px;
		cursor: pointer;
	}
	.stamp:hover {
		background: var(--leaf-deep);
	}
</style>
