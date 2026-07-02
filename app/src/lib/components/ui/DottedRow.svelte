<script lang="ts">
	import type { Snippet } from 'svelte';

	/** A menu line: name on the left, dotted leader, numbers on the right. */
	let { left, right }: { left: Snippet; right: Snippet } = $props();
</script>

<div class="row">
	<span class="left">{@render left()}</span>
	<span class="leader" aria-hidden="true"></span>
	<span class="right num">{@render right()}</span>
</div>

<style>
	.row {
		display: flex;
		align-items: baseline;
		gap: 8px;
	}
	.left,
	.right {
		white-space: nowrap;
	}
	.right {
		font-weight: 600;
		font-size: 0.8125rem;
	}
</style>
