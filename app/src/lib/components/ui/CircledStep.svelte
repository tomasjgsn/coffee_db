<script lang="ts">
	/** A step number inside a rough hand-drawn double circle. */
	let {
		n,
		color = 'var(--clay)',
		size = 46
	}: { n: string | number; color?: string; size?: number } = $props();
</script>

<svg width={size} height={size} viewBox="0 0 46 46" role="img" aria-label="Step {n}">
	<path
		d="M23,4 C34,3 43,11 42,22 C41,34 33,42 22,42 C11,42 4,33 4,22 C4,12 12,5 23,4 M25,3 C36,5 44,13 42,24"
		fill="none"
		stroke={color}
		stroke-width="3"
		stroke-linecap="round"
	/>
	<text x="23" y="29" text-anchor="middle" fill="var(--ink)">{n}</text>
</svg>

<style>
	text {
		font-family: var(--font-mono);
		font-weight: 600;
		font-size: 15px;
	}
</style>
