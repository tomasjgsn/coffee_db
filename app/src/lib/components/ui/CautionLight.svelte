<script lang="ts">
	import type { Snippet } from 'svelte';

	/** An advisory as an instrument caution light: lit indicator, terse text. */
	let { label = 'caution', children }: { label?: string; children: Snippet } = $props();
</script>

<div class="caution" role="status">
	<span class="lamp" aria-hidden="true"></span>
	<div class="body">
		<span class="micro caution-label">{label}</span>
		<div class="text num">{@render children()}</div>
	</div>
</div>

<style>
	.caution {
		display: flex;
		gap: 12px;
		align-items: flex-start;
		border: 1px solid var(--line);
		border-left: 2px solid var(--amber);
		background: var(--bone);
		padding: 10px 14px;
	}
	.lamp {
		flex: none;
		width: 10px;
		height: 10px;
		border-radius: 50%;
		margin-top: 4px;
		background: radial-gradient(circle at 35% 30%, #ffe9c4, var(--amber) 55%, var(--amber-deep));
	}
	.caution-label {
		display: block;
		color: var(--amber-deep);
	}
	.text {
		font-size: 0.8rem;
		line-height: 1.5;
		color: var(--graphite);
		margin-top: 2px;
	}
</style>
