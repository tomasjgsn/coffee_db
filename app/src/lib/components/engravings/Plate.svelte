<script lang="ts">
	import type { Snippet } from 'svelte';

	/**
	 * A framed engraved miniature: double ring, gold compass points, lowercase
	 * mono caption. Children are <g> content on the shared 96 grid.
	 */
	let {
		caption = '',
		size = 120,
		children
	}: { caption?: string; size?: number; children: Snippet } = $props();
</script>

<figure style:width="{size}px">
	<svg viewBox="0 0 96 96" width={size} height={size} role="img" aria-label={caption || 'engraved plate'}>
		<circle cx="48" cy="48" r="45" fill="none" stroke="var(--graphite)" stroke-width="0.8" />
		<circle cx="48" cy="48" r="41.8" fill="none" stroke="var(--graphite)" stroke-width="0.4" />
		<path
			d="M48,1.2 L49.8,5.4 L48,7.6 L46.2,5.4 Z M48,94.8 L49.8,90.6 L48,88.4 L46.2,90.6 Z M1.2,48 L5.4,46.2 L7.6,48 L5.4,49.8 Z M94.8,48 L90.6,46.2 L88.4,48 L90.6,49.8 Z"
			fill="var(--gold)"
		/>
		{@render children()}
	</svg>
	{#if caption}
		<figcaption class="micro">{caption}</figcaption>
	{/if}
</figure>

<style>
	figure {
		margin: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 6px;
	}
	svg {
		display: block;
	}
	figcaption {
		text-align: center;
	}
</style>
