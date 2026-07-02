<script lang="ts">
	import V60 from '$lib/components/ink/V60.svelte';

	let { cups = null }: { cups?: number | null } = $props();

	const today = new Date().toLocaleDateString('en-GB', {
		weekday: 'short',
		day: '2-digit',
		month: 'short'
	});
</script>

<header class="rule-press">
	<div class="inner">
		<div class="corners micro">
			<span>{cups === null ? 'Field notes on extraction' : `Nº ${String(cups).padStart(3, '0')} — cups to date`}</span>
			<span>{today} · single user · small batch</span>
		</div>
		<div class="row">
			<div class="title-block">
				<h1 class="label-caps">The<br />Counter</h1>
				<p class="etch-italic tagline">beans, brews &amp; the ideal zone</p>
				<p class="micro">V60 · Switch · Aeropress · Chemex</p>
			</div>
			<div class="clay-block" aria-hidden="true">
				<V60 size={96} onDark />
			</div>
		</div>
	</div>
</header>

<style>
	.inner {
		padding: 10px 2px 14px;
	}
	.corners {
		display: flex;
		justify-content: space-between;
		gap: 12px;
	}
	.row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 20px;
		margin-top: 10px;
	}
	h1 {
		margin: 0;
		font-size: 2.6rem;
		font-stretch: 115%;
		letter-spacing: 0.05em;
		line-height: 0.92;
	}
	.tagline {
		margin: 8px 0 6px;
		font-size: 1.05rem;
		color: var(--roast);
	}
	.title-block p.micro {
		margin: 0;
	}
	.clay-block {
		flex: none;
		width: 108px;
		height: 108px;
		background: var(--clay);
		display: grid;
		place-items: center;
	}
</style>
