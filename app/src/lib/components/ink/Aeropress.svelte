<script lang="ts">
	let { size = 76, onDark = false }: { size?: number; onDark?: boolean } = $props();
</script>

<svg
	width={size}
	height={size * 0.86}
	viewBox="0 0 84 72"
	role="img"
	aria-label="Aeropress brush drawing"
	style:--accent={onDark ? 'var(--paper)' : 'var(--clay)'}
>
	<path
		d="M26,8 C34,5 50,5 58,8 C59,13 58,16 57,18 L27,18 C26,15 25,11 26,8 Z"
		fill="var(--ink)"
	/>
	<path
		d="M29,18 C29,18 28,48 29,50 L55,50 C56,44 56,24 55,18"
		fill="none"
		stroke="var(--ink)"
		stroke-width="5"
		stroke-linejoin="round"
		stroke-linecap="round"
	/>
	<path d="M33,28 L51,27 M33,36 L51,35" stroke="var(--ink)" stroke-width="3" stroke-linecap="round" />
	<ellipse cx="37" cy="59" rx="2.5" ry="3.5" fill="var(--accent)" />
	<ellipse cx="46" cy="63" rx="2.5" ry="3.5" fill="var(--accent)" />
	<ellipse cx="52" cy="58" rx="2.5" ry="3.5" fill="var(--accent)" />
</svg>
