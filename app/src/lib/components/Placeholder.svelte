<script lang="ts">
	import type { Component } from 'svelte';
	import type { InkProps } from '$lib/components/ink';

	let {
		illustration,
		note,
		phase
	}: { illustration: Component<InkProps>; note: string; phase: number } = $props();

	const Ink = $derived(illustration);
</script>

<div class="placeholder">
	<Ink size={72} />
	<p class="etch-italic">{note}</p>
	<p class="micro">Arrives in phase {phase}</p>
</div>

<style>
	.placeholder {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 8px;
		padding: 56px 0;
		text-align: center;
	}
	.placeholder .etch-italic {
		font-size: 1.25rem;
		margin: 0;
		color: var(--roast);
	}
	.placeholder .micro {
		margin: 0;
	}
</style>
