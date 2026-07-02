<script lang="ts">
	/** Drawn marks: a wavy underline or a scribbled pointing arrow. */
	let {
		kind = 'underline',
		color = 'var(--clay)',
		width = 128
	}: { kind?: 'underline' | 'arrow'; color?: string; width?: number } = $props();
</script>

{#if kind === 'underline'}
	<svg {width} height="10" viewBox="0 0 128 10" preserveAspectRatio="none" aria-hidden="true">
		<path
			d="M3,5 C16,1 26,9 40,5 C54,1 64,9 78,5 C92,1 102,9 116,5 L125,4"
			fill="none"
			stroke={color}
			stroke-width="3"
			stroke-linecap="round"
		/>
	</svg>
{:else}
	<svg width="56" height="34" viewBox="0 0 56 34" aria-hidden="true">
		<path
			d="M4,26 C14,30 22,12 32,14 C39,15 41,22 48,18 M48,18 l-7,-4 M48,18 l-3,7"
			fill="none"
			stroke={color}
			stroke-width="4"
			stroke-linecap="round"
		/>
	</svg>
{/if}
