<script lang="ts">
	import { enhance } from '$app/forms';
	import { METHODS, type MethodId } from '$lib/domain/methods';
	import { ENGRAVINGS, Mark } from '$lib/components/engravings';
	import CautionLight from '$lib/components/ui/CautionLight.svelte';
	import { clock, countLabel, parseClock, ratioLabel, score1, weekdayDay } from '$lib/format';
	import { brewRatio } from '$lib/brewing/calculations';
	import { classifyRay, ratioWindowForBox, slopeForRatio } from '$lib/brewing/rays';
	import { splitForPicker } from '$lib/domain/bag-picker';
	import type { PageProps } from './$types';

	type Bag = PageProps['data']['bags'][number];

	let { data, form }: PageProps = $props();

	// Folded once from the bag the plan opened with, so a card never jumps
	// out from under the pointer when it is picked.
	const picker = $derived(splitForPicker(data.bags, data.initialBeanId ?? data.bags[0]?.bean.id ?? null));

	// svelte-ignore state_referenced_locally
	let beanId = $state<number | null>(data.initialBeanId ?? data.bags[0]?.bean.id ?? null);
	let method = $state<MethodId>('v60');
	// svelte-ignore state_referenced_locally
	let pinnedMethod = data.initialMethod;

	const prefill = $derived(beanId !== null ? (data.prefills[beanId]?.[method] ?? null) : null);

	let doseG = $state(0);
	let waterG = $state(0);
	let tempC = $state<number | null>(null);
	let grindSize = $state<number | null>(null);
	let grinder = $state('');
	let iceG = $state<number | null>(null);
	let hotWaterG = $state<number | null>(null);
	let pours = $state<{ at: string; targetG: number; label: string }[]>([]);

	const isIced = $derived(METHODS.find((m) => m.id === method)?.iced ?? false);
	const ratio = $derived(doseG > 0 && waterG > 0 ? brewRatio(waterG, doseG) : null);

	$effect(() => {
		if (pinnedMethod) {
			method = pinnedMethod;
			pinnedMethod = null;
			return;
		}
		if (beanId !== null && data.lastMethod[beanId]) method = data.lastMethod[beanId];
	});

	$effect(() => {
		if (!prefill) return;
		doseG = prefill.doseG;
		waterG = prefill.waterG;
		tempC = prefill.tempC;
		grindSize = prefill.grindSize;
		grinder = prefill.grinder ?? '';
		iceG = prefill.iceG;
		hotWaterG = prefill.hotWaterG;
		pours = prefill.plan.pours.map((p) => ({ at: clock(p.at), targetG: p.targetG, label: p.label }));
	});

	$effect(() => {
		if (isIced && iceG !== null && hotWaterG !== null) waterG = iceG + hotWaterG;
	});

	function delta(current: number | null, original: number | null | undefined): boolean {
		return original !== null && original !== undefined && current !== null && current !== original;
	}

	function addPour() {
		const last = pours.at(-1);
		const lastAt = last ? (parseClock(last.at) ?? 0) : 0;
		pours.push({
			at: clock(lastAt + 30),
			targetG: last ? last.targetG : Math.round(doseG * 3),
			label: `Pour ${pours.length + 1}`
		});
	}

	const planJson = $derived(
		JSON.stringify({
			pours: pours
				.map((p) => ({ at: parseClock(p.at) ?? 0, targetG: p.targetG, label: p.label }))
				.sort((a, b) => a.at - b.at)
		})
	);

	// Ray check before pouring: is the ideal box even reachable at this ratio?
	const rayAdvisory = $derived.by(() => {
		if (ratio === null) return null;
		const lrr = data.lrrByMethod[method] ?? 2;
		const slope = slopeForRatio(ratio, lrr);
		if (slope === null) return null;
		if (classifyRay(slope) === 'through') return null;
		const window = ratioWindowForBox(lrr);
		return {
			tooTight: classifyRay(slope) === 'above',
			lrr: Math.round(lrr * 100) / 100,
			min: Math.round(window.min * 10) / 10,
			max: Math.round(window.max * 10) / 10
		};
	});

	const sourceNote = $derived.by(() => {
		if (!prefill) return '';
		if (prefill.source.kind === 'same-method')
			return `same as ${weekdayDay(prefill.source.brewedAt!)}`;
		if (prefill.source.kind === 'same-bean')
			return `from last brew, ${weekdayDay(prefill.source.brewedAt!)}`;
		return 'house recipe';
	});
</script>

<svelte:head><title>The Counter: plan</title></svelte:head>

<form method="POST" action="?/start" use:enhance>
	<section>
		<div class="step-head"><span class="clause num">1.0</span><h2 class="label-caps">The bag</h2></div>
		{#snippet bagCard(bag: Bag)}
			<label class="bag-card" class:selected={beanId === bag.bean.id}>
				<input type="radio" name="beanId" value={bag.bean.id} bind:group={beanId} />
				<span class="label-caps country">{bag.bean.originCountry ?? 'Origin unknown'}</span>
				<span class="etch name">{bag.bean.name}</span>
				<span class="micro">{countLabel(bag.brewCount, 'brew')}{bag.bestScore === null ? '' : ` · best ${score1(bag.bestScore)}`}</span>
			</label>
		{/snippet}
		<div class="bags recent">
			{#each picker.recent as bag (bag.bean.id)}
				{@render bagCard(bag)}
			{/each}
		</div>
		{#if picker.other.length > 0}
			<details class="other-bags">
				<summary class="micro">other bags ({picker.other.length})</summary>
				<div class="bags">
					{#each picker.other as bag (bag.bean.id)}
						{@render bagCard(bag)}
					{/each}
				</div>
			</details>
		{/if}
	</section>

	<section>
		<div class="step-head"><span class="clause num">2.0</span><h2 class="label-caps">The brewer</h2></div>
		<div class="methods">
			{#each METHODS as m (m.id)}
				{@const Art = ENGRAVINGS[m.illustration]}
				<label class="method-card" class:selected={method === m.id}>
					<input type="radio" name="method" value={m.id} bind:group={method} />
					<Mark size={54} label={m.label}><Art /></Mark>
					<span class="micro">{m.label}</span>
				</label>
			{/each}
		</div>
	</section>

	<section>
		<div class="step-head">
			<span class="clause num">3.0</span><h2 class="label-caps">The recipe</h2>
			<span class="etch-italic source">{sourceNote}</span>
		</div>
		<div class="recipe">
			<div class="grid num">
				<label>
					<span class="micro">Dose g</span>
					<input type="number" step="0.1" min="1" name="doseG" bind:value={doseG}
						class:changed={delta(doseG, prefill?.doseG)} />
				</label>
				{#if isIced}
					<label>
						<span class="micro">Hot water g</span>
						<input type="number" step="1" min="1" name="hotWaterG" bind:value={hotWaterG} />
					</label>
					<label>
						<span class="micro">Ice g</span>
						<input type="number" step="1" min="1" name="iceG" bind:value={iceG} />
					</label>
					<div class="readout">
						<span class="micro">Total water</span>
						<span class="value">{waterG} g</span>
						<input type="hidden" name="waterG" value={waterG} />
					</div>
				{:else}
					<label>
						<span class="micro">Water g</span>
						<input type="number" step="1" min="1" name="waterG" bind:value={waterG}
							class:changed={delta(waterG, prefill?.waterG)} />
					</label>
				{/if}
				<label>
					<span class="micro">Temp °C</span>
					<input type="number" step="0.5" min="60" max="100" name="tempC" bind:value={tempC}
						class:changed={delta(tempC, prefill?.tempC)} />
				</label>
				<label>
					<span class="micro">Grind</span>
					<input type="number" step="0.1" min="0" name="grindSize" bind:value={grindSize}
						class:changed={delta(grindSize, prefill?.grindSize)} />
				</label>
				<div class="readout">
					<span class="micro">Ratio</span>
					<span class="value">{ratioLabel(ratio)}</span>
				</div>
			</div>
			<input type="hidden" name="grinder" value={grinder} />
			<input type="hidden" name="mugWeightG" value={prefill?.mugWeightG ?? ''} />
			<input type="hidden" name="plan" value={planJson} />

			{#if rayAdvisory}
				<div class="advisory-slot" data-testid="plan-ray-advisory">
					<CautionLight label="caution: ratio">
						{#if rayAdvisory.tooTight}
							At {ratioLabel(ratio)} this brewer's ray misses the ideal box (retention ≈{rayAdvisory.lrr} g/g).
							Grind can't fix it. Reachable between 1:{rayAdvisory.min} and 1:{rayAdvisory.max}.
						{:else}
							At {ratioLabel(ratio)} the ray passes below the ideal box: ideal extraction reads Weak.
							Reachable between 1:{rayAdvisory.min} and 1:{rayAdvisory.max}.
						{/if}
					</CautionLight>
				</div>
			{/if}

			<div class="plan">
				<span class="micro plan-title">Pour plan{isIced ? ': hot water only' : ''}</span>
				{#each pours as pour, i (i)}
					<div class="pour num">
						<span class="pour-label">{pour.label}</span>
						<label><span class="micro">at</span><input type="text" bind:value={pour.at} size="4" /></label>
						<label><span class="micro">to</span><input type="number" bind:value={pour.targetG} step="1" min="0" style="width:70px" /> <span class="micro">g</span></label>
						{#if pours.length > 1}
							<button type="button" class="remove" onclick={() => pours.splice(i, 1)} aria-label="Remove {pour.label}">×</button>
						{/if}
					</div>
				{/each}
				<button type="button" class="add micro" onclick={addPour}>Add pour</button>
			</div>

			{#if form?.message}
				<p class="error micro">{form.message}</p>
			{/if}

			<button class="start field-red" type="submit">Start brew</button>
		</div>
	</section>
</form>

<style>
	section {
		margin-bottom: 26px;
	}
	.step-head {
		display: flex;
		align-items: center;
		gap: 10px;
		margin-bottom: 12px;
	}
	.step-head h2 {
		font-size: 1.05rem;
		margin: 0;
	}
	/* Body-size red is ember; solar is for display sizes only. */
	.clause {
		font-size: 0.8rem;
		color: var(--ember);
	}
	.source {
		font-size: 0.85rem;
		color: var(--graphite-soft);
		margin-left: 6px;
	}
	.bags {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
		gap: 10px;
	}
	.other-bags summary {
		cursor: pointer;
		padding: 10px 0 2px;
	}
	.other-bags .bags {
		margin-top: 8px;
	}
	.bag-card,
	.method-card {
		display: flex;
		flex-direction: column;
		gap: 4px;
		border: 1px solid var(--line);
		background: var(--bone);
		padding: 12px;
		cursor: pointer;
	}
	.bag-card input,
	.method-card input {
		position: absolute;
		opacity: 0;
	}
	.bag-card.selected,
	.method-card.selected {
		border-color: var(--line-strong);
		outline: 1px solid var(--graphite);
		outline-offset: -1px;
		background: var(--bone-warm);
	}
	/* The radios are invisible; their keyboard focus shows on the card. */
	.bag-card:has(input:focus-visible),
	.method-card:has(input:focus-visible) {
		outline: 2px solid var(--graphite);
		outline-offset: 2px;
	}
	.country {
		font-size: 0.7rem;
		color: var(--graphite-soft);
	}
	.name {
		font-size: 1.1rem;
		line-height: 1.05;
	}
	.methods {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
		gap: 10px;
	}
	.method-card {
		align-items: center;
		text-align: center;
	}
	.recipe {
		border: 1px solid var(--line);
		background: var(--bone);
		padding: 18px;
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
		width: 100%;
	}
	.grid input:focus {
		outline: none;
		border-bottom-color: var(--graphite);
	}
	/* Changed from the prefill: a shaded field in ink. Amber means under-extracted. */
	.grid input.changed {
		background: var(--bone-shade);
		border-bottom-color: var(--graphite-soft);
	}
	.readout .value {
		font-size: 1.05rem;
		font-weight: 600;
		padding: 4px 2px;
	}
	.plan {
		border-top: 1px solid var(--line);
		margin-top: 16px;
		padding-top: 12px;
	}
	.plan-title {
		display: block;
		margin-bottom: 8px;
	}
	.pour {
		display: flex;
		align-items: baseline;
		gap: 12px;
		padding: 4px 0;
	}
	.pour-label {
		width: 70px;
		font-size: 0.8rem;
		font-weight: 600;
	}
	.pour label {
		display: inline-flex;
		align-items: baseline;
		gap: 5px;
	}
	.pour input {
		font-family: var(--font-mono);
		font-weight: 600;
		background: transparent;
		border: none;
		border-bottom: 1.5px solid var(--line);
		color: var(--graphite);
		padding: 2px;
	}
	.pour input:focus {
		outline: none;
		border-bottom-color: var(--graphite);
	}
	.remove {
		background: none;
		border: none;
		color: var(--ember);
		font-size: 1rem;
		cursor: pointer;
	}
	.add {
		background: none;
		border: 1px dashed var(--line-strong);
		color: var(--graphite-soft);
		padding: 5px 10px;
		margin-top: 6px;
		cursor: pointer;
	}
	.error {
		color: var(--ember);
		margin: 10px 0 0;
	}
	.advisory-slot {
		margin: 14px 0 0;
	}
	.start {
		display: block;
		width: 100%;
		margin-top: 16px;
	}
</style>
