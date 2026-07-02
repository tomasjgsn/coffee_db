<script lang="ts">
	let { size = 76, onDark = false }: { size?: number; onDark?: boolean } = $props();
</script>

<svg
	width={size}
	height={size * 0.86}
	viewBox="0 0 84 72"
	role="img"
	aria-label="V60 brush drawing"
	style:--accent={onDark ? 'var(--paper)' : 'var(--clay)'}
>
	<path
		d="M13,12 C22,8 60,7 71,11 L53,42 C49,47 36,47 32,42 Z"
		fill="none"
		stroke="var(--ink)"
		stroke-width="5.5"
		stroke-linejoin="round"
		stroke-linecap="round"
	/>
	<path d="M25,19 L57,18 M31,27 L51,26" stroke="var(--ink)" stroke-width="3.5" stroke-linecap="round" />
	<ellipse cx="42" cy="51" rx="3" ry="4" fill="var(--accent)" />
	<path d="M22,62 C32,57 53,58 62,61 C60,68 25,69 22,62 Z" fill="var(--ink)" />
</svg>
