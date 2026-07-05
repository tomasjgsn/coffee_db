<script lang="ts">
	import CautionLight from '$lib/components/ui/CautionLight.svelte';
	import {
		Plate,
		Medallion,
		Pour,
		Switch,
		Press,
		Hourglass,
		Eye,
		Prism,
		Drop,
		Kettle,
		BeanBranch,
		Vessel,
		Habitat,
		PLATE_CAPTIONS
	} from '$lib/components/engravings';

	const plates = [
		{ art: Pour, caption: PLATE_CAPTIONS.pour },
		{ art: Switch, caption: PLATE_CAPTIONS.switch },
		{ art: Press, caption: PLATE_CAPTIONS.press },
		{ art: Hourglass, caption: PLATE_CAPTIONS.hourglass },
		{ art: Eye, caption: PLATE_CAPTIONS.eye },
		{ art: Prism, caption: PLATE_CAPTIONS.prism },
		{ art: Drop, caption: PLATE_CAPTIONS.drop },
		{ art: Kettle, caption: PLATE_CAPTIONS.kettle },
		{ art: BeanBranch, caption: PLATE_CAPTIONS.beanBranch },
		{ art: Vessel, caption: PLATE_CAPTIONS.vessel },
		{ art: Habitat, caption: PLATE_CAPTIONS.habitat }
	];

	const fields = [
		{ name: 'bone', spec: '#ffffff to #efe3de', style: 'background: var(--field-bone); border: 1px solid var(--line);' },
		{ name: 'solar red', spec: '#ff4d2e to #8e1a0d', style: 'background: var(--field-solar);' },
		{ name: 'ember', spec: '#8e1a0d to #5c0e06', style: 'background: var(--field-ember);' },
		{ name: 'chrome', spec: 'material, static ramp', style: 'background: var(--chrome-face);' },
		{ name: 'graphite', spec: '#141519', style: 'background: var(--graphite);' }
	];

	const specimens = [
		{ name: 'olive', spec: 'zone: ideal', style: 'background: var(--olive);' },
		{ name: 'amber', spec: 'zone: under', style: 'background: var(--amber);' },
		{ name: 'gold', spec: 'miniatures only', style: 'background: var(--gold);' }
	];
</script>

<svelte:head><title>The Counter: design reference</title></svelte:head>

<section>
	<div class="clause">
		<span class="n num">1.0</span>
		<h2>Color: fields, not fills</h2>
	</div>
	<div class="chips">
		{#each fields as field (field.name)}
			<div class="chip">
				<div class="swatch" style={field.style}></div>
				<span class="micro">{field.name}</span>
				<span class="spec num">{field.spec}</span>
			</div>
		{/each}
	</div>
	<div class="chips specimens">
		{#each specimens as s (s.name)}
			<div class="chip">
				<div class="swatch small" style={s.style}></div>
				<span class="micro">{s.name}</span>
				<span class="spec num">{s.spec}</span>
			</div>
		{/each}
	</div>
	<p class="note">One red action per screen. Solar is brand, live, and latest; it is never a zone. Over-extraction is ember.</p>
</section>

<div class="chrome-rule" role="presentation"></div>

<section>
	<div class="clause">
		<span class="n num">2.0</span>
		<h2>Type: the law</h2>
	</div>
	<div class="type-grid">
		<div>
			<span class="micro">plex sans, structure</span>
			<p class="spec-heading">Flight plan</p>
			<p class="spec-body">Hamararo, washed. Guji zone, rest 12 days.</p>
		</div>
		<div>
			<span class="micro">plex mono, every reading</span>
			<p class="spec-reading num">1.38 → 21.2%</p>
			<p class="spec-data num">18.0g · 1:16.7 · 94.5°C</p>
		</div>
	</div>
	<p class="note">No letterspaced caps. Labels lowercase mono. Hierarchy by size, weight, and clause numerals. No em dashes: colons and periods join. Middot only between readings.</p>
</section>

<div class="chrome-rule" role="presentation"></div>

<section>
	<div class="clause">
		<span class="n num">3.0</span>
		<h2>Instrument artifacts</h2>
	</div>
	<div class="artifacts">
		<button class="field-red" type="button">Start brew</button>
		<div class="caution-demo">
			<CautionLight label="caution: ratio">
				1:15.4 misses the ideal box. Reachable from 1:16.0.
			</CautionLight>
		</div>
	</div>
	<div class="caustic-demo caustic-slot">
		<svg viewBox="0 0 300 120" role="img" aria-label="Static caustic pool preview">
			<defs>
				<radialGradient id="pool" cx="50%" cy="50%" r="50%">
					<stop offset="0%" stop-color="#fffdf4" />
					<stop offset="36%" stop-color="#f9edc4" stop-opacity="0.9" />
					<stop offset="64%" stop-color="#e8a33d" stop-opacity="0.28" />
					<stop offset="84%" stop-color="#6b7c3f" stop-opacity="0.14" />
					<stop offset="100%" stop-color="#6b7c3f" stop-opacity="0" />
				</radialGradient>
			</defs>
			<rect width="300" height="120" fill="var(--bone-warm)" />
			<ellipse cx="150" cy="74" rx="104" ry="26" fill="url(#pool)" />
			<ellipse cx="150" cy="74" rx="64" ry="14" fill="none" stroke="#ffffff" stroke-width="1.4" opacity="0.85" />
			<text x="150" y="46" text-anchor="middle" class="pool-num">21.2%</text>
		</svg>
		<span class="micro">the caustic: cast by a verified reading. Engine version breathes; this is the still.</span>
	</div>
</section>

<div class="chrome-rule" role="presentation"></div>

<section>
	<div class="clause">
		<span class="n num">4.0</span>
		<h2>Engraved miniatures</h2>
	</div>
	<div class="plates">
		{#each plates as plate (plate.caption)}
			{@const Art = plate.art}
			<Plate caption={plate.caption} size={116}>
				<Art />
			</Plate>
		{/each}
	</div>
	<div class="medal-row">
		<Medallion label="cup 100" sub="service medal">
			<Drop />
		</Medallion>
		<Medallion label="dialed in" sub="first ideal, per bag">
			<Eye />
		</Medallion>
		<p class="note">Two-weight engraving: 1.3 structure, 0.55 detail, one red act per plate. Gold lives only in compass points and medal rims. Plates hold the margins; controls carry no icons.</p>
	</div>
</section>

<style>
	section {
		margin-bottom: 28px;
	}
	.clause {
		display: flex;
		align-items: baseline;
		gap: 10px;
		margin-bottom: 14px;
	}
	.clause .n {
		font-size: 0.8rem;
		color: var(--solar);
	}
	h2 {
		margin: 0;
		font-size: 1.25rem;
		font-weight: 600;
		letter-spacing: -0.015em;
	}
	.chips {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 10px;
	}
	.chips.specimens {
		grid-template-columns: repeat(5, 1fr);
		margin-top: 10px;
	}
	.chip {
		display: flex;
		flex-direction: column;
		gap: 3px;
	}
	.swatch {
		height: 56px;
	}
	.swatch.small {
		height: 26px;
	}
	.spec {
		font-size: 0.625rem;
		color: var(--graphite-faint);
	}
	.note {
		font-size: 0.8rem;
		color: var(--graphite-soft);
		margin: 12px 0 0;
		max-width: 560px;
		line-height: 1.55;
	}
	.chrome-rule {
		margin: 24px 0;
	}
	.type-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 22px;
	}
	.type-grid > div {
		border-top: 1px solid var(--line);
		padding-top: 10px;
	}
	.spec-heading {
		font-size: 1.5rem;
		font-weight: 600;
		letter-spacing: -0.015em;
		margin: 6px 0 0;
	}
	.spec-body {
		font-size: 0.85rem;
		color: var(--graphite-soft);
		margin: 3px 0 0;
	}
	.spec-reading {
		font-size: 1.3rem;
		font-weight: 600;
		margin: 8px 0 0;
	}
	.spec-data {
		font-size: 0.75rem;
		color: var(--graphite-soft);
		margin: 3px 0 0;
	}
	.artifacts {
		display: flex;
		gap: 18px;
		align-items: flex-start;
		flex-wrap: wrap;
	}
	.caution-demo {
		flex: 1;
		min-width: 260px;
	}
	.caustic-demo {
		margin-top: 18px;
		max-width: 360px;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.caustic-demo svg {
		width: 100%;
		height: auto;
		display: block;
	}
	.pool-num {
		font-family: var(--font-mono);
		font-weight: 600;
		font-size: 22px;
		fill: var(--graphite);
	}
	.plates {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
		gap: 16px 10px;
	}
	.medal-row {
		display: flex;
		gap: 22px;
		align-items: center;
		margin-top: 22px;
		flex-wrap: wrap;
	}
	.medal-row .note {
		flex: 1;
		min-width: 240px;
		margin: 0;
	}
</style>
