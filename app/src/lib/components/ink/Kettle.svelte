<script lang="ts">
	let { size = 76, onDark = false }: { size?: number; onDark?: boolean } = $props();
</script>

<svg
	width={size}
	height={size * 0.86}
	viewBox="0 0 84 72"
	role="img"
	aria-label="Gooseneck kettle brush drawing"
	style:--accent={onDark ? 'var(--paper)' : 'var(--clay)'}
>
	<path
		d="M34,32 C30,30 28,36 28,42 C28,54 34,62 46,62 C58,62 64,54 64,42 C64,34 58,30 52,30 C46,30 38,33 34,32 Z"
		fill="var(--ink)"
	/>
	<path d="M32,38 C20,36 14,28 20,16" fill="none" stroke="var(--ink)" stroke-width="5" stroke-linecap="round" />
	<path d="M17,14 L26,17" stroke="var(--ink)" stroke-width="5" stroke-linecap="round" />
	<path d="M38,26 C42,12 56,12 60,24" fill="none" stroke="var(--ink)" stroke-width="4.5" stroke-linecap="round" />
	<circle cx="48" cy="26" r="4" fill="var(--accent)" />
</svg>
