<script lang="ts">
	import { enhance } from '$app/forms';
	import { methodLabel } from '$lib/domain/methods';
	import { extractionYield, brewingZone, overallRating } from '$lib/brewing/calculations';
	import { pct, score1, zoneLabel } from '$lib/format';
	import FactorDots from '$lib/components/ui/FactorDots.svelte';
	import Caustic from '$lib/light/Caustic.svelte';
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
	// What the extraction reading is waiting for, in words.
	const awaiting = $derived(tds === null ? 'enter tds' : brewMass === null ? 'enter weights' : 'no reading');
	const overall = $derived(overallRating(complexity, bitterness, mouthfeel));

	const FLAVOR_PROFILES = ['Bright/Acidic', 'Balanced', 'Rich/Full', 'Sweet', 'Bitter', 'Fruity', 'Nutty', 'Chocolatey'];
	const showTimeFields = $derived(data.manual || data.brew.totalTimeS === null);
</script>

<svelte:head><title>The Counter: taste cup {data.brew.id}</title></svelte:head>

<div class="head">
	<p class="micro">Cup {String(data.brew.id).padStart(3, '0')}, {methodLabel(data.brew.method)}, open draft</p>
	<h2 class="etch bean">{data.bean?.name ?? 'Unnamed cup'}</h2>
</div>

<form method="POST" action="?/save" use:enhance class="sheet">
	<section>
		<span class="micro section-title">Measurements</span>
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
				<span class="value" class:empty={brewMass === null}>{brewMass === null ? 'enter weights' : `${brewMass} g`}</span>
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
		<div class="verdict" class:pool={zone === 'Ideal-Ideal'}>
			{#if zone === 'Ideal-Ideal'}
				<Caustic intensity={0.75} />
			{/if}
			<span class="micro">Extraction</span>
			<span class="reading-wrap">
				<span class="num ey" class:empty={ey === null}>{ey === null ? awaiting : pct(ey)}</span>
				{#if ey !== null}
					<span class="fringe" aria-hidden="true"></span>
				{/if}
			</span>
			{#if zone}
				<span
					class="zone-chip num"
					class:ideal={zone === 'Ideal-Ideal'}
					class:under={zone.startsWith('Under')}
					class:over={zone.startsWith('Over')}>{zoneLabel(zone)}</span
				>
			{/if}
		</div>
	</section>

	<section>
		<span class="micro section-title">Score (optional)</span>
		<div class="factors">
			<FactorDots name="scoreComplexity" label="Complexity" bind:value={complexity} />
			<FactorDots name="scoreBitterness" label="Bitterness" bind:value={bitterness} />
			<FactorDots name="scoreMouthfeel" label="Mouthfeel" bind:value={mouthfeel} />
		</div>
		<div class="overall num">
			<span class="micro">Overall</span>
			<span class="big" class:empty={overall === null}>{overall === null ? 'needs all three' : score1(overall)}</span>
		</div>
		<label class="profile">
			<span class="micro">Flavor profile</span>
			<select name="flavorProfile" value={data.brew.flavorProfile ?? ''}>
				<option value="">none</option>
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
		<label class="notes-label">
			<span class="micro">Notes</span>
			<textarea name="notes" rows="1">{data.brew.notes ?? ''}</textarea>
		</label>
	</section>

	{#if form?.message}<p class="error micro">{form.message}</p>{/if}

	<div class="actions">
		<button class="later micro" type="submit" name="intent" value="draft">Save draft</button>
		<button class="field-red" type="submit" name="intent" value="complete">Complete</button>
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
		border: 1px solid var(--line);
		background: var(--bone);
		padding: 20px;
	}
	section + section {
		border-top: 1px solid var(--line);
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
		color: var(--graphite);
		background: transparent;
		border: none;
		border-bottom: 2px solid var(--line);
		padding: 4px 2px;
	}
	.grid input:focus {
		outline: none;
		border-bottom-color: var(--graphite);
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
		color: var(--graphite);
		background: transparent;
		border: none;
		border-bottom: 2px solid var(--line);
		padding: 4px 2px;
	}
	.verdict {
		position: relative;
		display: flex;
		align-items: baseline;
		gap: 12px;
		margin-top: 14px;
		padding: 8px 12px;
		overflow: hidden;
	}
	.verdict > :global(:not(canvas)) {
		position: relative;
	}
	.reading-wrap {
		display: inline-flex;
		flex-direction: column;
	}
	/* The dispersion fringe: the one live element on this screen. It
	   resolves once when a reading appears, then holds: no idle drift. */
	.fringe {
		height: 2px;
		margin-top: 2px;
		background: var(--dispersion);
		background-size: 220% 100%;
		background-position: 0% 0;
		animation: fringe-resolve var(--dur-settle) var(--ease-settle) 1 both;
	}
	@media (prefers-reduced-motion: reduce) {
		.fringe {
			animation: none;
		}
	}
	@keyframes fringe-resolve {
		from {
			background-position: 100% 0;
			opacity: 0;
		}
		to {
			background-position: 0% 0;
			opacity: 1;
		}
	}
	.verdict.pool {
		background: radial-gradient(ellipse 60% 100% at 30% 60%, #fffdf2, #f8eec8 45%, rgba(232, 163, 61, 0.16) 75%, transparent);
	}
	/* A reading that is not there yet says what it needs, at label size. */
	.value.empty,
	.ey.empty,
	.overall .big.empty {
		font-size: 0.85rem;
		font-weight: 500;
		color: var(--graphite-soft);
	}
	.ey {
		font-size: 1.6rem;
		font-weight: 600;
	}
	.zone-chip {
		font-size: 0.65rem;
		font-weight: 600;
		border: 1px solid var(--graphite-soft);
		color: var(--graphite-soft);
		padding: 3px 8px;
	}
	.zone-chip.ideal {
		background: var(--olive);
		border-color: var(--olive);
		color: var(--bone);
	}
	.zone-chip.under {
		border-color: var(--amber);
		color: var(--amber-deep);
	}
	.zone-chip.over {
		border-color: var(--ember);
		color: var(--ember);
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
		color: var(--graphite);
		padding: 7px 8px;
	}
	textarea {
		font-family: var(--font-sans);
		font-style: italic;
		font-size: 1rem;
		color: var(--graphite-soft);
	}
	textarea:focus,
	select:focus {
		outline: none;
		border-color: var(--graphite);
	}
	.error {
		color: var(--ember);
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
		border: 1px dashed var(--line-strong);
		color: var(--graphite-soft);
		padding: 10px 14px;
		cursor: pointer;
	}
</style>
