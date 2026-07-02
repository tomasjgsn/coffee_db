<script lang="ts">
	import Steam from '$lib/components/ink/Steam.svelte';
</script>

<div class="placeholder">
	<Steam size={56} />
	<p class="etch-italic">Today's menu arrives in phase 5.</p>
	<p class="micro">Until then — <a href="/design">the design system</a></p>
</div>

<style>
	.placeholder {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 8px;
		padding: 56px 0;
		text-align: center;
	}
	.placeholder .etch-italic {
		font-size: 1.25rem;
		margin: 0;
		color: var(--roast);
	}
	.placeholder a {
		color: var(--clay-deep);
	}
</style>
