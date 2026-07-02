<script lang="ts">
	/** Perforated milestone token — a dashed-circle keepsake. */
	let {
		lines,
		color = 'var(--roast)',
		size = 62
	}: { lines: string[]; color?: string; size?: number } = $props();
</script>

<span class="token num" style:width="{size}px" style:height="{size}px" style:border-color={color} style:color>
	{#each lines as line (line)}
		<span>{line}</span>
	{/each}
</span>

<style>
	.token {
		display: inline-flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		border: 1.5px dashed;
		border-radius: 50%;
		font-size: 0.5625rem;
		letter-spacing: 0.08em;
		line-height: 1.3;
		text-transform: uppercase;
		text-align: center;
	}
</style>
