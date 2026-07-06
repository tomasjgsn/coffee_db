<script lang="ts">
	import { scaleLinear } from 'd3-scale';
	import ControlChart, { type ChartPoint, type GuideRay } from '$lib/components/charts/ControlChart.svelte';
	import HoverCard from '$lib/components/charts/HoverCard.svelte';
	import VariablePanel from '$lib/components/charts/VariablePanel.svelte';
	import Squiggle from '$lib/components/ui/Squiggle.svelte';
	import { methodLabel } from '$lib/domain/methods';
	import { score1 } from '$lib/format';
	import {
		classifyRay,
		liquidRetainedRatio,
		ratioWindowForBox,
		slopeForRatio
	} from '$lib/brewing/rays';
	import type { ChartPointData } from './+page.server';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	let beanFilter = $state('');
	let methodFilter = $state('');
	let profileFilter = $state('');
	let range = $state<'all' | '25' | '10'>('all');
	let tintBy = $state<'' | 'grind' | 'temp' | 'ratio' | 'rest'>('');

	let hovered = $state<{ point: ChartPointData; x: number; y: number } | null>(null);
	let pinned = $state<{ point: ChartPointData; x: number; y: number } | null>(null);

	const beanOptions = $derived([...new Set(data.points.map((p) => p.beanName).filter((b): b is string => !!b))]);
	const methodOptions = $derived([...new Set(data.points.map((p) => p.method))]);
	const profileOptions = $derived([...new Set(data.points.map((p) => p.flavorProfile).filter((p): p is string => !!p))]);

	const slice = $derived.by(() => {
		const filtered = data.points.filter(
			(p) =>
				(!beanFilter || p.beanName === beanFilter) &&
				(!methodFilter || p.method === methodFilter) &&
				(!profileFilter || p.flavorProfile === profileFilter)
		);
		if (range === 'all') return filtered;
		return filtered.slice(-Number(range));
	});

	const byId = $derived(new Map(data.points.map((p) => [p.id, p])));

	const TINTS: Record<
		Exclude<typeof tintBy, ''>,
		{ label: string; unit: string; of: (p: ChartPointData) => number | null }
	> = {
		grind: { label: 'Grind', unit: '', of: (p) => p.grindSize },
		temp: { label: 'Temp', unit: '°C', of: (p) => p.tempC },
		ratio: { label: 'Ratio', unit: ':1', of: (p) => p.ratio },
		rest: { label: 'Rest', unit: 'days', of: (p) => p.restDays }
	};

	const tintScale = $derived.by(() => {
		if (tintBy === '') return null;
		const of = TINTS[tintBy].of;
		const values = slice.map(of).filter((v): v is number => v !== null);
		if (values.length < 2) return null;
		const min = Math.min(...values);
		const max = Math.max(...values);
		if (min === max) return null;
		return { min, max, scale: scaleLinear().domain([min, max]).range([18, 100]), of };
	});

	const chartPoints = $derived(
		slice.map((p, i) => ({
			id: p.id,
			ey: p.ey,
			tds: p.tds,
			score: p.overall,
			latest: i === slice.length - 1
		}))
	);

	function tintPercentOf(point: ChartPoint): number | null {
		if (!tintScale) return null;
		const source = byId.get(point.id);
		if (!source) return null;
		const value = tintScale.of(source);
		return value === null ? 20 : tintScale.scale(value);
	}

	function onhover(point: ChartPoint | null, x: number, y: number) {
		if (pinned) return;
		if (!point) {
			hovered = null;
			return;
		}
		const source = byId.get(point.id);
		hovered = source ? { point: source, x, y } : null;
	}

	function onselect(point: ChartPoint) {
		const source = byId.get(point.id);
		if (!source) return;
		pinned = { point: source, x: hovered?.x ?? 200, y: hovered?.y ?? 200 };
		hovered = null;
	}

	// Slice statistics — everything reacts to the filters together.
	const scored = $derived(slice.filter((p) => p.overall !== null));
	const last10 = $derived(slice.slice(-10));
	const prev10 = $derived(slice.slice(-20, -10));
	const hitRate = (cups: ChartPointData[]) =>
		cups.length === 0
			? null
			: Math.round((cups.filter((p) => p.zone === 'Ideal-Ideal').length / cups.length) * 100);
	const hitNow = $derived(hitRate(last10));
	const hitBefore = $derived(hitRate(prev10));
	const avgScore = $derived.by(() => {
		const rated = last10.filter((p) => p.overall !== null);
		if (rated.length === 0) return null;
		return Math.round((rated.reduce((s, p) => s + p.overall!, 0) / rated.length) * 10) / 10;
	});
	const bestCup = $derived.by(() => {
		let best: ChartPointData | null = null;
		for (const p of scored) if (best === null || p.overall! > best.overall!) best = p;
		return best;
	});

	const panelData = (of: (p: ChartPointData) => number | null) =>
		scored
			.filter((p) => of(p) !== null)
			.map((p) => ({ id: p.id, x: of(p)!, y: p.overall! }));

	const profileRows = $derived.by(() => {
		const groups = new Map<string, number[]>();
		for (const p of scored) {
			if (!p.flavorProfile) continue;
			const list = groups.get(p.flavorProfile) ?? [];
			list.push(p.overall!);
			groups.set(p.flavorProfile, list);
		}
		return [...groups.entries()]
			.map(([profile, scores]) => ({
				profile,
				n: scores.length,
				avg: Math.round((scores.reduce((s, v) => s + v, 0) / scores.length) * 10) / 10
			}))
			.sort((a, b) => b.avg - a.avg);
	});

	const trendPath = $derived.by(() => {
		if (scored.length < 2) return null;
		const w = 240;
		const h = 56;
		const min = Math.min(...scored.map((t) => t.overall!));
		const max = Math.max(...scored.map((t) => t.overall!));
		const span = Math.max(0.5, max - min);
		return scored
			.map((t, i) => {
				const px = (i / (scored.length - 1)) * (w - 8) + 4;
				const py = h - 6 - ((t.overall! - min) / span) * (h - 12);
				return `${i === 0 ? 'M' : 'L'}${px.toFixed(1)},${py.toFixed(1)}`;
			})
			.join(' ');
	});

	const highlightId = $derived(pinned?.point.id ?? hovered?.point.id ?? null);

	// --- Iso-ratio rays: every cup lies on TDS = (dose/brew mass) × EY ---

	function median(values: number[]): number | null {
		if (values.length === 0) return null;
		const sorted = [...values].sort((a, b) => a - b);
		const mid = Math.floor(sorted.length / 2);
		return sorted.length % 2 === 1 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
	}

	/** Median measured retention (g water kept per g coffee) across the slice. */
	const sliceLrr = $derived(
		median(
			slice
				.map((p) => liquidRetainedRatio(p.doseG, p.waterG, p.brewMassG))
				.filter((v): v is number => v !== null && v >= 0 && v < 5)
		)
	);

	const guideRays = $derived.by<GuideRay[]>(() => {
		const lrr = sliceLrr ?? 2;
		const rays: GuideRay[] = [];
		for (const ratio of [14, 15, 16, 17, 18, 20]) {
			const slope = slopeForRatio(ratio, lrr);
			if (slope !== null) rays.push({ slope, label: `1:${ratio}` });
		}
		return rays;
	});

	/** The hovered/pinned cup's own ray — exactly TDS/EY, no assumptions. */
	const hoverRaySlope = $derived.by(() => {
		const p = pinned?.point ?? hovered?.point;
		if (!p || p.ey === 0) return null;
		return p.tds / p.ey;
	});

	/** Reachability advisory for the slice's typical recipe. */
	const advisory = $derived.by(() => {
		if (slice.length < 3) return null;
		const slopes = slice.filter((p) => p.ey > 0).map((p) => p.tds / p.ey);
		const typicalSlope = median(slopes);
		const typicalRatio = median(slice.map((p) => p.ratio).filter((r): r is number => r !== null));
		if (typicalSlope === null || typicalRatio === null || sliceLrr === null) return null;
		const verdict = classifyRay(typicalSlope);
		if (verdict === 'through') return null;
		const window = ratioWindowForBox(sliceLrr);
		return {
			verdict,
			typicalRatio: Math.round(typicalRatio * 10) / 10,
			lrr: Math.round(sliceLrr * 100) / 100,
			windowMin: Math.round(window.min * 10) / 10,
			windowMax: Math.round(window.max * 10) / 10
		};
	});
</script>

<svelte:window onkeydown={(e) => e.key === 'Escape' && (pinned = null)} />
<svelte:head><title>The Counter: chart</title></svelte:head>

<div class="head">
	<div>
		<h2 class="label-caps page-title">The chart</h2>
		<p class="micro">{slice.length} of {data.points.length} measured cups</p>
	</div>
</div>

<div class="filters">
	<label><span class="micro">Bean</span>
		<select bind:value={beanFilter} class="micro" aria-label="Filter by bean">
			<option value="">All beans</option>
			{#each beanOptions as bean (bean)}<option value={bean}>{bean}</option>{/each}
		</select>
	</label>
	<label><span class="micro">Method</span>
		<select bind:value={methodFilter} class="micro" aria-label="Filter by method">
			<option value="">All methods</option>
			{#each methodOptions as m (m)}<option value={m}>{methodLabel(m)}</option>{/each}
		</select>
	</label>
	<label><span class="micro">Profile</span>
		<select bind:value={profileFilter} class="micro" aria-label="Filter by flavor profile">
			<option value="">All profiles</option>
			{#each profileOptions as p (p)}<option value={p}>{p}</option>{/each}
		</select>
	</label>
	<label><span class="micro">Range</span>
		<select bind:value={range} class="micro" aria-label="Range">
			<option value="all">Every cup</option>
			<option value="25">Last 25</option>
			<option value="10">Last 10</option>
		</select>
	</label>
	<label><span class="micro">Tint by</span>
		<select bind:value={tintBy} class="micro" aria-label="Tint dots by">
			<option value="">Plain ink</option>
			<option value="grind">Grind</option>
			<option value="temp">Temp</option>
			<option value="ratio">Ratio</option>
			<option value="rest">Rest days</option>
		</select>
	</label>
</div>

<div class="chart-frame">
	<ControlChart
		points={chartPoints}
		connect={beanFilter !== ''}
		{highlightId}
		tintPercentOf={tintScale ? tintPercentOf : null}
		rays={guideRays}
		{hoverRaySlope}
		{onhover}
		{onselect}
	/>
	<div class="chart-foot">
		{#if tintScale && tintBy !== ''}
			<div class="legend" data-testid="tint-legend">
				<span class="num">{Math.round(tintScale.min * 10) / 10}</span>
				<span class="ramp" aria-hidden="true"></span>
				<span class="num">{Math.round(tintScale.max * 10) / 10}</span>
				<span class="micro">{TINTS[tintBy].label}{TINTS[tintBy].unit ? ` ${TINTS[tintBy].unit}` : ''} · pale → dark</span>
			</div>
		{:else}
			<span></span>
		{/if}
		{#if beanFilter}
			<p class="etch-italic journey-note">dial-in path: successive brews of this bag</p>
		{/if}
	</div>
	<p class="micro ray-note">
		Ratio rays use this slice's measured retention ({sliceLrr === null
			? 'assumed 2.0'
			: Math.round(sliceLrr * 100) / 100} g/g). Grind, temp, and time move a cup along its ray;
		only the recipe changes rays.
	</p>
</div>

{#if advisory}
	<div class="advisory num" data-testid="ray-advisory">
		{#if advisory.verdict === 'above'}
			This slice brews near 1:{advisory.typicalRatio} with ~{advisory.lrr} g/g retention.
			The ray passes above the ideal box: no grind or temperature change reaches Ideal-Ideal.
			Reachable between 1:{advisory.windowMin} and 1:{advisory.windowMax}.
		{:else}
			This slice brews near 1:{advisory.typicalRatio}. The ray passes below the ideal box:
			ideal extraction always reads Weak. Reachable between 1:{advisory.windowMin} and 1:{advisory.windowMax}.
		{/if}
	</div>
{/if}

<div class="stats">
	<div class="stat">
		<span class="micro">Ideal-zone hit rate, last 10</span>
		<span class="num big">{hitNow === null ? '—' : `${hitNow}%`}</span>
		{#if hitBefore !== null && hitNow !== null}
			<span class="num delta" class:up={hitNow >= hitBefore}>
				{hitNow >= hitBefore ? '↗' : '↘'} was {hitBefore}%
			</span>
		{/if}
	</div>
	<div class="stat">
		<span class="micro">Average score, last 10</span>
		<span class="num big">{score1(avgScore)}</span>
	</div>
	<div class="stat">
		<span class="micro">Best cup in slice</span>
		{#if bestCup}
			<a class="best" href="/log/{bestCup.id}">
				<span class="num big">{score1(bestCup.overall)}</span>
				<span class="micro">{bestCup.beanName ?? 'unnamed'} · cup {bestCup.id}</span>
			</a>
		{:else}
			<span class="num big">—</span>
		{/if}
	</div>
</div>

<section class="needle">
	<h3 class="micro section">What moves the needle: score vs each variable</h3>
	<div class="panels">
		<VariablePanel title="Grind" points={panelData((p) => p.grindSize)} {highlightId} />
		<VariablePanel title="Temp" unit="°C" points={panelData((p) => p.tempC)} {highlightId} />
		<VariablePanel title="Ratio" unit=":1" points={panelData((p) => p.ratio)} {highlightId} />
		<VariablePanel title="Rest" unit="days" points={panelData((p) => p.restDays)} {highlightId} />
	</div>
</section>

{#if profileRows.length > 0}
	<section>
		<h3 class="micro section">By flavor profile</h3>
		<div class="profiles">
			{#each profileRows as row (row.profile)}
				<div class="profile-row">
					<span class="etch profile-name">{row.profile}</span>
					<span class="track" aria-hidden="true">
						<span class="mark" style:left="{(row.avg / 5) * 100}%"></span>
					</span>
					<span class="num profile-avg">{row.avg.toFixed(1)} <span class="micro">n={row.n}</span></span>
				</div>
			{/each}
		</div>
	</section>
{/if}

<section>
	<h3 class="micro section">Scored cups, oldest → newest</h3>
	<div class="trend">
		{#if trendPath}
			<svg viewBox="0 0 240 56" aria-label="Score trend across the filtered cups">
				<path d={trendPath} fill="none" stroke="var(--roast)" stroke-width="1.5" />
			</svg>
		{:else}
			<span class="micro">Not enough scored cups</span>
		{/if}
		<Squiggle kind="underline" width={110} />
	</div>
</section>

{#if pinned}
	<HoverCard point={pinned.point} x={pinned.x} y={pinned.y} pinned onclose={() => (pinned = null)} />
{:else if hovered}
	<HoverCard point={hovered.point} x={hovered.x} y={hovered.y} />
{/if}

<style>
	.head {
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
		gap: 10px;
		flex-wrap: wrap;
		margin-bottom: 12px;
	}
	.filters label {
		display: flex;
		flex-direction: column;
		gap: 3px;
	}
	select {
		background: var(--paper-bright);
		border: 1px solid var(--line);
		color: var(--ink);
		padding: 6px 8px;
		max-width: 170px;
	}
	.chart-frame {
		border: 2px solid var(--ink);
		background: var(--paper-bright);
		padding: 14px;
	}
	.chart-foot {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 12px;
		margin-top: 8px;
	}
	.legend {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.legend .num {
		font-size: 0.7rem;
		font-weight: 600;
	}
	.ramp {
		width: 90px;
		height: 9px;
		background: linear-gradient(to right, var(--kraft), var(--ink));
		display: inline-block;
	}
	.journey-note {
		margin: 0;
		font-size: 1rem;
		color: var(--roast);
	}
	.ray-note {
		margin: 8px 2px 0;
	}
	.advisory {
		border: 1px solid var(--ochre);
		background: var(--ochre-wash);
		color: var(--ochre-deep);
		font-size: 0.8rem;
		line-height: 1.5;
		padding: 10px 14px;
		margin-top: 12px;
	}
	.stats {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 12px;
		margin-top: 14px;
	}
	.stat {
		border: 1px solid var(--line);
		padding: 12px 14px;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.stat .big {
		font-size: 1.7rem;
		font-weight: 600;
	}
	.delta {
		font-size: 0.75rem;
		color: var(--clay-deep);
	}
	.delta.up {
		color: var(--leaf-deep);
	}
	.best {
		color: inherit;
		text-decoration: none;
		display: flex;
		flex-direction: column;
		gap: 3px;
	}
	.best:hover .micro {
		color: var(--clay-deep);
	}
	section {
		margin-top: 20px;
	}
	.section {
		border-bottom: 1px solid var(--ink);
		padding-bottom: 5px;
		margin: 0 0 10px;
		font-weight: 500;
	}
	.panels {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
		gap: 10px;
	}
	.profiles {
		display: flex;
		flex-direction: column;
		gap: 7px;
		max-width: 520px;
	}
	.profile-row {
		display: flex;
		align-items: center;
		gap: 12px;
	}
	.profile-name {
		width: 130px;
		font-size: 0.95rem;
	}
	.track {
		flex: 1;
		position: relative;
		border-bottom: 2px dotted var(--line-soft);
		height: 10px;
	}
	.mark {
		position: absolute;
		top: 2px;
		width: 10px;
		height: 10px;
		margin-left: -5px;
		border-radius: 50%;
		background: var(--roast);
	}
	.profile-avg {
		font-weight: 600;
		font-size: 0.85rem;
		white-space: nowrap;
	}
	.trend svg {
		width: 100%;
		max-width: 480px;
		height: 56px;
		display: block;
	}
</style>
