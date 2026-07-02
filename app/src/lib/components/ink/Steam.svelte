<script lang="ts">
	let { size = 56, onDark = false }: { size?: number; onDark?: boolean } = $props();
</script>

<svg
	width={size}
	height={size * 0.74}
	viewBox="0 0 70 52"
	aria-hidden="true"
	style:--stroke={onDark ? 'var(--paper)' : 'var(--ink)'}
>
	<path
		d="M14,46 C10,38 20,34 16,26 C12,18 22,14 18,6 M34,48 C30,40 40,36 36,28 C32,20 42,16 38,8 M54,46 C50,38 60,34 56,26 C52,18 62,14 58,6"
		fill="none"
		stroke="var(--stroke)"
		stroke-width="4"
		stroke-linecap="round"
	/>
</svg>
