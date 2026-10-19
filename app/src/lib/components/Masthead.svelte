<script lang="ts">
	import Chrome from '$lib/light/Chrome.svelte';

	let { cups = null }: { cups?: number | null } = $props();

	const today = new Date().toLocaleDateString('en-GB', {
		weekday: 'short',
		day: '2-digit',
		month: 'short'
	});
</script>

<header>
	<div class="row">
		<div class="mark">
			<h1>The Counter</h1>
			<span class="dot" aria-hidden="true"></span>
		</div>
		<span class="meta micro">
			{cups === null ? 'field notes on extraction' : `${cups} cups`}, {today.toLowerCase()}
		</span>
	</div>
	<div class="rail" role="presentation">
		<Chrome shape="rule" />
	</div>
</header>

<style>
	header {
		padding-top: 6px;
	}
	/* On a narrow screen the meta folds under the mark; the mark never breaks. */
	.row {
		display: flex;
		flex-wrap: wrap;
		justify-content: space-between;
		align-items: baseline;
		gap: 4px 16px;
		padding-bottom: 12px;
	}
	.mark {
		display: flex;
		align-items: baseline;
		gap: 9px;
	}
	h1 {
		margin: 0;
		font-size: 1.45rem;
		font-weight: 600;
		letter-spacing: -0.02em;
		line-height: 1;
		white-space: nowrap;
	}
	.dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--field-solar);
		transform: translateY(-1px);
	}
	/* The chrome rail: static ramp underneath, live reflection on top. */
	.rail {
		position: relative;
		height: 3px;
		background: var(--chrome-line);
		overflow: hidden;
	}
</style>
