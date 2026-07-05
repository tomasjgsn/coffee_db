<script lang="ts">
	import type { Snippet } from 'svelte';

	/** A service medal: gold rim, engraved inner ring, miniature content. */
	let {
		label,
		sub = '',
		size = 84,
		children
	}: { label: string; sub?: string; size?: number; children?: Snippet } = $props();
</script>

<figure style:width="{size + 20}px">
	<svg viewBox="0 0 96 96" width={size} height={size} role="img" aria-label={label}>
		<circle cx="48" cy="48" r="45" fill="none" stroke="var(--gold)" stroke-width="1.6" />
		<circle cx="48" cy="48" r="41" fill="none" stroke="var(--gold)" stroke-width="0.5" />
		<circle cx="48" cy="48" r="37.5" fill="none" stroke="var(--graphite)" stroke-width="0.4" />
		{#if children}
			{@render children()}
		{/if}
	</svg>
	<figcaption>
		<span class="medal-label num">{label}</span>
		{#if sub}<span class="micro">{sub}</span>{/if}
	</figcaption>
</figure>

<style>
	figure {
		margin: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 5px;
		text-align: center;
	}
	svg {
		display: block;
	}
	figcaption {
		display: flex;
		flex-direction: column;
		gap: 1px;
	}
	.medal-label {
		font-size: 0.7rem;
		font-weight: 600;
	}
</style>
