<script lang="ts">
	let { size = 76, onDark = false }: { size?: number; onDark?: boolean } = $props();
</script>

<svg
	width={size}
	height={size * 0.86}
	viewBox="0 0 84 72"
	role="img"
	aria-label="Coffee beans brush drawing"
	style:--accent={onDark ? 'var(--paper)' : 'var(--clay)'}
>
	<path d="M8,42 L76,36" stroke="var(--ink)" stroke-width="4.5" stroke-linecap="round" />
	<ellipse cx="24" cy="39" rx="11" ry="13" transform="rotate(-14 24 39)" fill="var(--ink)" />
	<path d="M20,30 C26,35 25,44 21,48" stroke="var(--accent)" stroke-width="3.5" fill="none" stroke-linecap="round" />
	<ellipse cx="45" cy="37" rx="11" ry="13" transform="rotate(8 45 37)" fill="var(--ink)" />
	<path d="M42,28 C48,33 47,42 43,46" stroke="var(--accent)" stroke-width="3.5" fill="none" stroke-linecap="round" />
	<ellipse cx="65" cy="35" rx="11" ry="13" transform="rotate(-10 65 35)" fill="var(--ink)" />
	<path d="M61,26 C67,31 66,40 62,44" stroke="var(--accent)" stroke-width="3.5" fill="none" stroke-linecap="round" />
</svg>
