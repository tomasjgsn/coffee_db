<script lang="ts">
	let {
		top,
		bottom,
		ringTop = '',
		ringBottom = '',
		color = 'var(--leaf)',
		size = 86,
		rotate = -7
	}: {
		top: string;
		bottom?: string;
		ringTop?: string;
		ringBottom?: string;
		color?: string;
		size?: number;
		rotate?: number;
	} = $props();
</script>

<svg
	width={size}
	height={size}
	viewBox="0 0 96 96"
	style:transform="rotate({rotate}deg)"
	role="img"
	aria-label="{top}{bottom ? ` ${bottom}` : ''} stamp"
>
	<circle cx="48" cy="48" r="44" fill="none" stroke={color} stroke-width="2.5" />
	<circle cx="48" cy="48" r="34" fill="none" stroke={color} stroke-width="1" />
	{#if ringTop}
		<text x="48" y="28" text-anchor="middle" fill={color} class="ring">{ringTop}</text>
	{/if}
	<text x="48" y={bottom ? 44 : 52} text-anchor="middle" fill={color} class="word">{top}</text>
	{#if bottom}
		<text x="48" y="57" text-anchor="middle" fill={color} class="word">{bottom}</text>
	{/if}
	{#if ringBottom}
		<text x="48" y="72" text-anchor="middle" fill={color} class="ring">{ringBottom}</text>
	{/if}
</svg>

<style>
	.word {
		font-family: var(--font-label);
		font-weight: 700;
		font-size: 11px;
		letter-spacing: 1.5px;
		text-transform: uppercase;
	}
	.ring {
		font-family: var(--font-mono);
		font-size: 8px;
		letter-spacing: 1px;
		text-transform: uppercase;
	}
</style>
