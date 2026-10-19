<script lang="ts">
	import '@fontsource/ibm-plex-sans/400.css';
	import '@fontsource/ibm-plex-sans/400-italic.css';
	import '@fontsource/ibm-plex-sans/500.css';
	import '@fontsource/ibm-plex-sans/600.css';
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
		{ href: '/', label: 'today' },
		{ href: '/brew', label: 'brew' },
		{ href: '/log', label: 'log' },
		{ href: '/chart', label: 'chart' },
		{ href: '/shelf', label: 'shelf' }
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
			<a href={item.href} class="hit" class:active={isActive(item.href)}>{item.label}</a>
		{/each}
	</nav>
	<main>
		{#key page.url.pathname}
			<div class="page" in:fade={{ duration: 160 }}>
				{@render children()}
			</div>
		{/key}
	</main>
</div>

<style>
	:global(html) {
		background: var(--bone);
	}
	:global(body) {
		margin: 0;
		color: var(--graphite);
		font-family: var(--font-sans);
		font-weight: 400;
		-webkit-font-smoothing: antialiased;
	}
	.frame {
		max-width: 960px;
		margin: 0 auto;
		padding: 26px 24px 64px;
	}
	nav {
		display: flex;
		gap: 20px;
		padding: 10px 2px;
	}
	nav a {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		color: var(--graphite-soft);
		text-decoration: none;
		padding-bottom: 3px;
		border-bottom: 2px solid transparent;
	}
	nav a.active {
		color: var(--graphite);
		border-bottom-color: var(--solar);
	}
	nav a:hover {
		color: var(--graphite);
	}
	main {
		padding-top: 24px;
	}
</style>
