<script lang="ts">
	let { squares = 34, size = 11 }: { squares?: number; size?: number } = $props();
</script>

<div class="strip" aria-hidden="true" style:--sq="{size}px">
	{#each { length: squares } as _, i (i)}
		<span class:ink={i % 2 === 0}></span>
	{/each}
</div>

<style>
	.strip {
		display: flex;
		gap: 2px;
		overflow: hidden;
	}
	.strip span {
		flex: none;
		width: var(--sq);
		height: var(--sq);
	}
	.strip span.ink {
		background: var(--ink);
	}
</style>
