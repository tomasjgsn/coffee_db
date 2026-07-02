<script lang="ts">
	let { size = 76, onDark = false }: { size?: number; onDark?: boolean } = $props();
</script>

<svg
	width={size}
	height={size * 0.86}
	viewBox="0 0 84 72"
	role="img"
	aria-label="Hario Switch brush drawing"
	style:--accent={onDark ? 'var(--paper)' : 'var(--clay)'}
>
	<path
		d="M16,10 C26,7 58,7 68,10 L54,30 C50,34 35,34 31,30 Z"
		fill="none"
		stroke="var(--ink)"
		stroke-width="5.5"
		stroke-linejoin="round"
		stroke-linecap="round"
	/>
	<path
		d="M28,34 C36,31 49,31 56,34 C57,42 55,46 52,48 C44,50 40,50 32,48 C29,45 27,41 28,34 Z"
		fill="var(--ink)"
	/>
	<circle cx="67" cy="42" r="6.5" fill="var(--accent)" />
	<path d="M60,42 L56,42" stroke="var(--accent)" stroke-width="4" stroke-linecap="round" />
	<path d="M24,62 L60,60" stroke="var(--ink)" stroke-width="5" stroke-linecap="round" />
</svg>
