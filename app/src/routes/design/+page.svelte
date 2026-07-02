<script lang="ts">
	import { METHODS } from '$lib/domain/methods';
	import { ILLUSTRATIONS, Beans, Kettle, Steam } from '$lib/components/ink';
	import Stamp from '$lib/components/ui/Stamp.svelte';
	import StampBadge from '$lib/components/ui/StampBadge.svelte';
	import ZoneChip from '$lib/components/ui/ZoneChip.svelte';
	import DottedRow from '$lib/components/ui/DottedRow.svelte';
	import CheckerStrip from '$lib/components/ui/CheckerStrip.svelte';
	import CircledStep from '$lib/components/ui/CircledStep.svelte';
	import Squiggle from '$lib/components/ui/Squiggle.svelte';
	import PerfToken from '$lib/components/ui/PerfToken.svelte';

	const pigments = [
		{ name: 'Paper', hex: '#F2EAD9', varName: '--paper', bordered: true },
		{ name: 'Kraft', hex: '#C9AF8B', varName: '--kraft', bordered: false },
		{ name: 'Ink', hex: '#2A241C', varName: '--ink', bordered: false },
		{ name: 'Clay', hex: '#A94F2B', varName: '--clay', bordered: false },
		{ name: 'Leaf', hex: '#3F5A40', varName: '--leaf', bordered: false },
		{ name: 'Ochre', hex: '#C08A2D', varName: '--ochre', bordered: false },
		{ name: 'Roast', hex: '#5A4632', varName: '--roast', bordered: false }
	];

	const pickable = METHODS.filter((m, i) => METHODS.findIndex((x) => x.illustration === m.illustration) === i);
</script>

<svelte:head>
	<title>The Counter — design system</title>
</svelte:head>

<section>
	<h2 class="micro">01 — Palette · paper, ink &amp; origin earth</h2>
	<div class="swatches">
		{#each pigments as p (p.name)}
			<div>
				<div class="swatch" style:background={p.hex} class:bordered={p.bordered}></div>
				<div class="swatch-name">{p.name}</div>
				<div class="num swatch-hex">{p.hex}</div>
			</div>
		{/each}
	</div>
</section>

<section>
	<h2 class="micro">02 — Three voices, no handwriting font</h2>
	<div class="voices">
		<div class="voice">
			<span class="micro">The label · Archivo</span>
			<p class="label-caps specimen-label">Today's<br />pours</p>
			<p class="voice-note">poster caps, structure, nav</p>
		</div>
		<div class="voice">
			<span class="micro">The instrument · Plex Mono</span>
			<p class="num specimen-num">18.0g · 1:16.7<br /><span class="roast">94.5°C → 21.2%</span></p>
			<p class="voice-note">every number in the app</p>
		</div>
		<div class="voice">
			<span class="micro">The etching · Fraunces</span>
			<p class="etch specimen-etch">Hamararo</p>
			<p class="etch-italic specimen-etch-sub">apricot jam, long finish</p>
			<p class="voice-note">bean names, notes, editorial</p>
		</div>
	</div>
</section>

<section>
	<h2 class="micro">03 — Brush-ink brewers · thick strokes, one accent</h2>
	<div class="brewers">
		{#each pickable as method (method.id)}
			{@const Ink = ILLUSTRATIONS[method.illustration]}
			<div class="brewer">
				<Ink size={76} />
				<span class="micro">{method.shortLabel}</span>
			</div>
		{/each}
		<div class="brewer"><Beans size={76} /><span class="micro">The bag</span></div>
		<div class="brewer"><Kettle size={76} /><span class="micro">Kettle</span></div>
		<div class="brewer"><Steam size={60} /><span class="micro">Steam</span></div>
	</div>
</section>

<section>
	<h2 class="micro">04 — Drawn artifacts · bespoke SVG, never a font</h2>
	<div class="artifacts">
		<CircledStep n="01" />
		<Squiggle kind="arrow" color="var(--ink)" />
		<span class="note-sample">
			<span class="etch-italic">keep this grind</span>
			<Squiggle kind="underline" />
		</span>
		<Stamp top="Ideal" bottom="zone" ringTop="Nº 061" ringBottom="18–22% EY" />
		<StampBadge text="Personal best" />
		<PerfToken lines={['Cup', 'Nº100']} />
	</div>
	<div class="zones">
		<ZoneChip zone="under" />
		<ZoneChip zone="ideal" />
		<ZoneChip zone="over" />
		<ZoneChip zone="weak" />
		<ZoneChip zone="strong" />
	</div>
</section>

<section>
	<h2 class="micro">05 — Menu rows · dotted leaders</h2>
	<div class="menu">
		<DottedRow>
			{#snippet left()}
				<span class="etch menu-bean">Hamararo</span> <span class="micro">V60</span>
			{/snippet}
			{#snippet right()}21.2% · 4.2{/snippet}
		</DottedRow>
		<DottedRow>
			{#snippet left()}
				<span class="etch menu-bean">La Palma</span> <span class="micro">Switch</span>
			{/snippet}
			{#snippet right()}19.8% · 3.5{/snippet}
		</DottedRow>
	</div>
	<div class="checker"><CheckerStrip /></div>
</section>

<style>
	section {
		margin-bottom: 34px;
	}
	h2 {
		margin: 0 0 12px;
		font-weight: 500;
	}
	.swatches {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
		gap: 8px;
	}
	.swatch {
		height: 46px;
	}
	.swatch.bordered {
		border: 1px solid var(--line);
	}
	.swatch-name {
		font-size: 0.6875rem;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		margin-top: 5px;
	}
	.swatch-hex {
		font-size: 0.625rem;
		color: var(--ink-soft);
	}
	.voices {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 12px;
	}
	.voice {
		border: 1px solid var(--line);
		padding: 14px;
	}
	.specimen-label {
		font-size: 1.25rem;
		margin: 10px 0 0;
	}
	.specimen-num {
		font-size: 0.9375rem;
		font-weight: 500;
		margin: 10px 0 0;
	}
	.specimen-num .roast {
		color: var(--roast);
	}
	.specimen-etch {
		font-size: 1.5rem;
		margin: 8px 0 0;
		line-height: 1;
	}
	.specimen-etch-sub {
		font-size: 0.9375rem;
		color: var(--roast);
		margin: 4px 0 0;
	}
	.voice-note {
		font-size: 0.6875rem;
		color: var(--ink-soft);
		margin: 10px 0 0;
	}
	.brewers {
		display: flex;
		gap: 22px;
		align-items: flex-end;
		flex-wrap: wrap;
	}
	.brewer {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 4px;
	}
	.artifacts {
		display: flex;
		gap: 20px;
		align-items: center;
		flex-wrap: wrap;
	}
	.note-sample {
		display: inline-flex;
		flex-direction: column;
	}
	.note-sample .etch-italic {
		font-size: 1.1875rem;
	}
	.zones {
		display: flex;
		gap: 8px;
		margin-top: 16px;
	}
	.menu {
		border: 1px solid var(--line);
		padding: 14px 16px;
		display: flex;
		flex-direction: column;
		gap: 8px;
		max-width: 460px;
	}
	.menu-bean {
		font-size: 1rem;
	}
	.checker {
		margin-top: 16px;
		max-width: 460px;
	}
</style>
