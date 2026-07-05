<script lang="ts">
	import type { Snippet } from 'svelte';

	/** An unframed engraving on the 96 grid, for pickers and inline use. */
	let {
		size = 56,
		label = '',
		children
	}: { size?: number; label?: string; children: Snippet } = $props();
</script>

<svg
	viewBox="0 0 96 96"
	width={size}
	height={size}
	role={label ? 'img' : 'presentation'}
	aria-label={label || undefined}
>
	{@render children()}
</svg>

<style>
	svg {
		display: block;
	}
</style>
