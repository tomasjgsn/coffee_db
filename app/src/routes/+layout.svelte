<script lang="ts">
	import '@fontsource-variable/archivo/wdth.css';
	import '@fontsource-variable/fraunces/full.css';
	import '@fontsource-variable/fraunces/full-italic.css';
	import '@fontsource/ibm-plex-mono/400.css';
	import '@fontsource/ibm-plex-mono/500.css';
	import '@fontsource/ibm-plex-mono/600.css';
	import '$lib/styles/tokens.css';
	import favicon from '$lib/assets/favicon.svg';
	import Masthead from '$lib/components/Masthead.svelte';
	import { page } from '$app/state';
	import { fade } from 'svelte/transition';

	let { data, children } = $props();

	const nav = [
		{ href: '/', label: 'Today' },
		{ href: '/brew', label: 'Brew' },
		{ href: '/log', label: 'The log' },
		{ href: '/chart', label: 'The chart' },
		{ href: '/shelf', label: 'The shelf' }
	];

	function isActive(href: string): boolean {
		if (href === '/') return page.url.pathname === '/';
		return page.url.pathname.startsWith(href);
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>The Counter</title>
</svelte:head>

<div class="frame">
	<Masthead cups={data.cups} />
	<nav aria-label="Primary">
		{#each nav as item (item.href)}
			<a href={item.href} class="label-caps" class:active={isActive(item.href)}>{item.label}</a>
		{/each}
	</nav>
	<main>
		{#key page.url.pathname}
			<div class="page" in:fade={{ duration: 180 }}>
				{@render children()}
			</div>
		{/key}
	</main>
</div>

<style>
	:global(html) {
		background: var(--paper);
	}
	:global(body) {
		margin: 0;
		color: var(--ink);
		font-family: var(--font-label);
		font-weight: 400;
		-webkit-font-smoothing: antialiased;
	}
	.frame {
		max-width: 960px;
		margin: 0 auto;
		padding: 28px 24px 64px;
	}
	nav {
		display: flex;
		gap: 22px;
		padding: 12px 2px;
		border-bottom: 1px solid var(--ink);
	}
	nav a {
		font-size: 0.75rem;
		font-weight: 700;
		color: var(--ink-soft);
		text-decoration: none;
		padding-bottom: 2px;
	}
	nav a.active {
		color: var(--ink);
		border-bottom: 3px solid var(--clay);
	}
	nav a:hover {
		color: var(--ink);
	}
	main {
		padding-top: 26px;
	}
</style>
