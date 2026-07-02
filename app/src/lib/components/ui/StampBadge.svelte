<script lang="ts">
	let {
		text,
		color = 'var(--clay)',
		rotate = -3
	}: { text: string; color?: string; rotate?: number } = $props();
</script>

<span class="badge" style:border-color={color} style:color style:transform="rotate({rotate}deg)">
	{text}
</span>

<style>
	.badge {
		display: inline-block;
		border-style: double;
		border-width: 4px;
		font-family: var(--font-label);
		font-weight: 800;
		font-size: 0.625rem;
		letter-spacing: 0.18em;
		text-transform: uppercase;
		padding: 4px 8px;
	}
</style>
