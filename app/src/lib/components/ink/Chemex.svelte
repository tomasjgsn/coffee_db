<script lang="ts">
	let { size = 76, onDark = false }: { size?: number; onDark?: boolean } = $props();
</script>

<svg
	width={size}
	height={size * 0.86}
	viewBox="0 0 84 72"
	role="img"
	aria-label="Chemex brush drawing"
	style:--accent={onDark ? 'var(--paper)' : 'var(--clay)'}
>
	<path
		d="M25,7 C34,4 50,4 59,7 L46,32 L60,58 C50,64 34,64 24,58 L38,32 Z"
		fill="none"
		stroke="var(--ink)"
		stroke-width="5.5"
		stroke-linejoin="round"
		stroke-linecap="round"
	/>
	<path d="M33,29 L51,29 L49,38 L35,38 Z" fill="var(--ink)" />
	<circle cx="55" cy="34" r="3.5" fill="var(--accent)" />
</svg>
