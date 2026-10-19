<script lang="ts">
	import { enhance } from '$app/forms';
	import { countLabel, score1, weekdayDay } from '$lib/format';
	import { Mark, BeanBranch } from '$lib/components/engravings';
	import type { PageProps } from './$types';

	let { data, form }: PageProps = $props();

	const active = $derived(data.shelf.filter((i) => !i.bean.archived));
	const finished = $derived(data.shelf.filter((i) => i.bean.archived));

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
						<option value="">unknown</option>
						{#each ['Washed', 'Natural', 'Honey', 'Semi-Washed', 'Anaerobic', 'Other'] as p (p)}
							<option value={p}>{p}</option>
						{/each}
					</select>
				</label>
				<label><span class="micro">Roast level</span>
					<select name="roastLevel">
						<option value="">unknown</option>
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
		<Mark size={72} label="bean branch"><BeanBranch /></Mark>
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
				<div><dt class="micro">Roast</dt><dd>{item.bean.roastDate ?? 'unknown'}</dd></div>
				<div><dt class="micro">Brews</dt><dd>{item.brewCount}</dd></div>
				<div><dt class="micro">Best</dt><dd>{score1(item.bestScore)}</dd></div>
				<div><dt class="micro">Avg</dt><dd>{score1(item.avgOverall)}</dd></div>
			</dl>
			{#if item.bean.bagSizeG}
				<div class="level" title="{remaining(item)}g left of {item.bean.bagSizeG}g">
					<span class="gauge">
						<span
							class="fill"
							style:width="{Math.max(0, Math.min(100, ((remaining(item) ?? 0) / item.bean.bagSizeG) * 100))}%"
						></span>
					</span>
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
				<span class="label-caps country">{item.bean.originCountry ?? 'Origin unknown'}</span>
				<h3 class="etch name">{item.bean.name}</h3>
				<p class="micro">{countLabel(item.brewCount, 'brew')}{item.bestScore === null ? '' : ` · best ${score1(item.bestScore)}`}</p>
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
		font-size: 0.8rem;
		font-weight: 600;
		cursor: pointer;
		background: var(--field-solar);
		color: #fff6f3;
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
		background: var(--bone);
		border: 1px solid var(--line-strong);
		padding: 16px;
		margin-top: 6px;
		box-shadow: 4px 5px 0 color-mix(in srgb, var(--graphite) 10%, transparent);
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
		color: var(--graphite);
		font-family: var(--font-sans);
		padding: 4px 2px;
	}
	.bag-form textarea {
		border: 1px solid var(--line);
		font-family: var(--font-sans);
		font-style: italic;
		padding: 6px 8px;
	}
	.bag-form input:focus,
	.bag-form select:focus,
	.bag-form textarea:focus {
		outline: none;
		border-color: var(--graphite);
	}
	.notes-field {
		margin-top: 10px;
	}
	.form-error {
		color: var(--ember);
		margin: 8px 0 0;
	}
	.form-ok {
		color: var(--graphite);
		margin: 8px 0 0;
	}
	.put-up {
		background: var(--graphite);
		color: var(--bone);
		border: none;
		font-size: 0.8rem;
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
		font-size: 0.95rem;
		color: var(--graphite-soft);
	}
	.archive-form {
		margin-top: 10px;
		text-align: right;
	}
	.archive-btn {
		background: none;
		border: none;
		color: var(--graphite-soft);
		text-decoration: underline;
		cursor: pointer;
	}
	.finished-head {
		border-bottom: 1px solid var(--line-strong);
		padding-bottom: 5px;
		margin: 24px 0 10px;
	}
	.bag.retired {
		opacity: 0.62;
		background: var(--bone-warm);
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
		gap: 14px;
	}
	.bag {
		background: var(--bone);
		border: 1px solid var(--line);
		padding: 16px;
	}
	.bag-head {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 8px;
	}
	.country {
		font-size: 0.8rem;
		color: var(--graphite-soft);
	}
	/* Process is a label on the bag, not a zone: ink, not olive. */
	.process {
		border: 1px solid var(--line-strong);
		color: var(--graphite-soft);
		font-family: var(--font-mono);
		font-size: 0.625rem;
		text-transform: lowercase;
		padding: 3px 6px;
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
		border-top: 1px solid var(--line);
		margin: 12px 0;
	}
	/* The roast date takes the room it needs so it never breaks mid-date. */
	.stats {
		display: grid;
		grid-template-columns: auto repeat(3, 1fr);
		gap: 6px 12px;
		margin: 0;
	}
	.stats dd {
		margin: 2px 0 0;
		font-size: 0.8rem;
		font-weight: 600;
		white-space: nowrap;
	}
	.level {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-top: 12px;
	}
	.gauge {
		flex: 1;
		height: 4px;
		background: var(--chrome-line);
		position: relative;
		overflow: hidden;
	}
	.gauge .fill {
		position: absolute;
		inset: 0 auto 0 0;
		background: var(--graphite);
	}
	.level .left {
		flex: none;
	}
	.last {
		margin: 10px 0 0;
	}
	.bag-notes {
		font-size: 0.9rem;
		color: var(--graphite-soft);
		margin: 10px 0 0;
		line-height: 1.3;
	}
</style>
