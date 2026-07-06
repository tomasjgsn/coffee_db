<script lang="ts">
	import { enhance } from '$app/forms';
	import { score1, weekdayDay } from '$lib/format';
	import { Beans } from '$lib/components/ink';
	import type { PageProps } from './$types';

	let { data, form }: PageProps = $props();

	const active = $derived(data.shelf.filter((i) => !i.bean.archived));
	const finished = $derived(data.shelf.filter((i) => i.bean.archived));

	function bagDots(item: (typeof data.shelf)[number]): { filled: number; total: number } | null {
		const size = item.bean.bagSizeG;
		if (!size) return null;
		const used = Math.min(1, item.dosedGrams / size);
		const total = 8;
		return { filled: Math.round(used * total), total };
	}

	function remaining(item: (typeof data.shelf)[number]): number | null {
		const size = item.bean.bagSizeG;
		if (!size) return null;
		return Math.max(0, Math.round(size - item.dosedGrams));
	}
</script>

<svelte:head><title>The Counter: shelf</title></svelte:head>

<div class="shelf-head">
	<div>
		<h2 class="label-caps page-title">The shelf</h2>
		<p class="micro subtitle">{active.length} open bags</p>
	</div>
	<details class="new-bag">
		<summary class="label-caps">+ New bag</summary>
		<form method="POST" action="?/add" use:enhance class="bag-form">
			<div class="form-grid">
				<label><span class="micro">Name</span><input name="name" required placeholder="Hamararo" /></label>
				<label><span class="micro">Country</span><input name="originCountry" placeholder="Ethiopia" /></label>
				<label><span class="micro">Region</span><input name="originRegion" placeholder="Guji zone" /></label>
				<label><span class="micro">Variety</span><input name="variety" /></label>
				<label><span class="micro">Process</span>
					<select name="process">
						<option value="">—</option>
						{#each ['Washed', 'Natural', 'Honey', 'Semi-Washed', 'Anaerobic', 'Other'] as p (p)}
							<option value={p}>{p}</option>
						{/each}
					</select>
				</label>
				<label><span class="micro">Roast level</span>
					<select name="roastLevel">
						<option value="">—</option>
						{#each ['Light', 'Light-Medium', 'Medium', 'Medium-Dark', 'Dark'] as r (r)}
							<option value={r}>{r}</option>
						{/each}
					</select>
				</label>
				<label><span class="micro">Roast date</span><input name="roastDate" type="date" /></label>
				<label><span class="micro">Bought</span><input name="purchaseDate" type="date" /></label>
				<label><span class="micro">Bag size g</span><input name="bagSizeG" type="number" step="1" min="1" placeholder="250" /></label>
			</div>
			<label class="notes-field"><span class="micro">Notes</span><textarea name="notes" rows="1" placeholder="preserved lemon, lychee, rose jam"></textarea></label>
			{#if form?.message}<p class="micro form-error">{form.message}</p>{/if}
			{#if form?.added}<p class="micro form-ok">Added</p>{/if}
			<button type="submit" class="label-caps put-up">Add bag</button>
		</form>
	</details>
</div>

{#if active.length === 0}
	<div class="bare">
		<Beans size={72} />
		<p class="etch-italic">No open bags</p>
	</div>
{/if}

<div class="grid">
	{#each active as item (item.bean.id)}
		<article class="bag">
			<div class="bag-head">
				<span class="label-caps country">{item.bean.originCountry ?? 'Origin unknown'}</span>
				{#if item.bean.process}
					<span class="process">{item.bean.process}</span>
				{/if}
			</div>
			<h3 class="etch name">{item.bean.name}</h3>
			{#if item.bean.originRegion}
				<p class="micro region">{item.bean.originRegion}</p>
			{/if}
			<div class="rule" role="presentation"></div>
			<dl class="stats num">
				<div><dt class="micro">Roast</dt><dd>{item.bean.roastDate ?? '—'}</dd></div>
				<div><dt class="micro">Brews</dt><dd>{item.brewCount}</dd></div>
				<div><dt class="micro">Best</dt><dd>{score1(item.bestScore)}</dd></div>
				<div><dt class="micro">Avg</dt><dd>{score1(item.avgOverall)}</dd></div>
			</dl>
			{#if bagDots(item)}
				{@const dots = bagDots(item)!}
				<div class="level" title="{remaining(item)}g left of {item.bean.bagSizeG}g">
					{#each { length: dots.total } as _, i (i)}
						<span class:used={i < dots.filled}></span>
					{/each}
					<span class="micro left">~{remaining(item)}g left</span>
				</div>
			{/if}
			{#if item.lastBrewedAt}
				<p class="micro last">Last brewed {weekdayDay(item.lastBrewedAt)}</p>
			{/if}
			{#if item.bean.notes}
				<p class="etch-italic bag-notes">{item.bean.notes}</p>
			{/if}
			<form method="POST" action="?/archive" use:enhance class="archive-form">
				<input type="hidden" name="beanId" value={item.bean.id} />
				<button type="submit" class="micro archive-btn">Retire bag</button>
			</form>
		</article>
	{/each}
</div>

{#if finished.length > 0}
	<h3 class="micro finished-head">Finished bags</h3>
	<div class="grid finished">
		{#each finished as item (item.bean.id)}
			<article class="bag retired">
				<span class="label-caps country">{item.bean.originCountry ?? '—'}</span>
				<h3 class="etch name">{item.bean.name}</h3>
				<p class="micro">{item.brewCount} brews · best {score1(item.bestScore)}</p>
				<form method="POST" action="?/archive" use:enhance>
					<input type="hidden" name="beanId" value={item.bean.id} />
					<button type="submit" class="micro archive-btn">Restore</button>
				</form>
			</article>
		{/each}
	</div>
{/if}

<style>
	.page-title {
		font-size: 1.4rem;
		margin: 0 0 4px;
	}
	.subtitle {
		margin: 0;
	}
	.shelf-head {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 16px;
		margin-bottom: 18px;
	}
	.new-bag summary {
		font-size: 0.75rem;
		cursor: pointer;
		background: var(--ink);
		color: var(--paper);
		padding: 11px 16px;
		list-style: none;
	}
	.new-bag[open] {
		position: relative;
		z-index: 2;
	}
	.bag-form {
		position: absolute;
		right: 0;
		width: min(520px, 86vw);
		background: var(--paper-bright);
		border: 2px solid var(--ink);
		padding: 16px;
		margin-top: 6px;
	}
	.form-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
		gap: 10px;
	}
	.bag-form label {
		display: flex;
		flex-direction: column;
		gap: 3px;
	}
	.bag-form input,
	.bag-form select,
	.bag-form textarea {
		background: transparent;
		border: none;
		border-bottom: 1.5px solid var(--line);
		color: var(--ink);
		font-family: var(--font-label);
		padding: 4px 2px;
	}
	.bag-form textarea {
		border: 1px solid var(--line);
		font-family: var(--font-etch);
		font-style: italic;
		padding: 6px 8px;
	}
	.bag-form input:focus,
	.bag-form select:focus,
	.bag-form textarea:focus {
		outline: none;
		border-color: var(--ink);
	}
	.notes-field {
		margin-top: 10px;
	}
	.form-error {
		color: var(--clay-deep);
		margin: 8px 0 0;
	}
	.form-ok {
		color: var(--leaf-deep);
		margin: 8px 0 0;
	}
	.put-up {
		background: var(--leaf);
		color: var(--paper);
		border: none;
		font-size: 0.7rem;
		padding: 10px 16px;
		margin-top: 12px;
		cursor: pointer;
	}
	.bare {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 8px;
		padding: 32px 0;
	}
	.bare p {
		margin: 0;
		font-size: 1.2rem;
		color: var(--roast);
	}
	.archive-form {
		margin-top: 10px;
		text-align: right;
	}
	.archive-btn {
		background: none;
		border: none;
		color: var(--ink-soft);
		text-decoration: underline dashed;
		cursor: pointer;
	}
	.finished-head {
		border-bottom: 1px solid var(--ink);
		padding-bottom: 5px;
		margin: 24px 0 10px;
	}
	.bag.retired {
		opacity: 0.65;
		background: var(--paper-bright);
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
		gap: 14px;
	}
	.bag {
		background: var(--kraft-light);
		border: 2px solid var(--ink);
		padding: 16px;
	}
	.bag-head {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 8px;
	}
	.country {
		font-size: 0.95rem;
		letter-spacing: 0.18em;
	}
	.process {
		border: 1.5px solid var(--leaf);
		color: var(--leaf-deep);
		font-weight: 700;
		font-size: 0.5625rem;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		padding: 3px 6px;
		transform: rotate(3deg);
		flex: none;
	}
	.name {
		font-size: 1.35rem;
		font-weight: 470;
		margin: 6px 0 0;
		line-height: 1.05;
	}
	.region {
		margin: 4px 0 0;
	}
	.rule {
		border-top: 1px dashed var(--line-soft);
		margin: 12px 0;
	}
	.stats {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 6px;
		margin: 0;
	}
	.stats dd {
		margin: 2px 0 0;
		font-size: 0.8rem;
		font-weight: 600;
	}
	.level {
		display: flex;
		align-items: center;
		gap: 4px;
		margin-top: 12px;
	}
	.level span:not(.left) {
		width: 9px;
		height: 9px;
		border-radius: 50%;
		border: 1px solid var(--line-soft);
	}
	.level span.used {
		background: var(--roast);
		border-color: var(--roast);
	}
	.level .left {
		margin-left: 6px;
	}
	.last {
		margin: 10px 0 0;
	}
	.bag-notes {
		font-size: 0.95rem;
		color: #3b3227;
		margin: 10px 0 0;
		line-height: 1.3;
	}
</style>
