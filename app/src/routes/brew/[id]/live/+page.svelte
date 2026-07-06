<script lang="ts">
	import { onMount } from 'svelte';
	import { enhance } from '$app/forms';
	import { methodLabel } from '$lib/domain/methods';
	import { clock } from '$lib/format';
	import type { BrewEvent } from '$lib/server/db/schema';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	// svelte-ignore state_referenced_locally
	let startedAt = $state<string | null>(data.brew.startedAt);
	// svelte-ignore state_referenced_locally
	let events = $state<BrewEvent[]>([...data.events]);
	let now = $state(Date.now());
	let pendingWaterFor = $state<number | null>(null);
	let waterInput = $state<string | number>('');
	let waterField = $state<HTMLInputElement | null>(null);

	onMount(() => {
		const tick = setInterval(() => (now = Date.now()), 200);
		return () => clearInterval(tick);
	});

	const elapsedMs = $derived(startedAt ? Math.max(0, now - Date.parse(startedAt)) : 0);
	const running = $derived(startedAt !== null && !events.some((e) => e.type === 'drawdown_end'));

	const openPour = $derived.by(() => {
		let open: BrewEvent | null = null;
		for (const e of events) {
			if (e.type === 'bloom_start' || e.type === 'pour_start') open = e;
			if (e.type === 'pour_end') open = null;
		}
		return open;
	});

	const pourCount = $derived(events.filter((e) => e.type === 'bloom_start' || e.type === 'pour_start').length);

	const nextPlanned = $derived.by(() => {
		if (!data.plan) return null;
		return data.plan.pours[pourCount] ?? null;
	});

	async function start() {
		const res = await fetch(`/api/brews/${data.brew.id}/start`, { method: 'POST' });
		if (res.ok) startedAt = (await res.json()).startedAt;
	}

	async function mark(type: BrewEvent['type'], waterG: number | null = null) {
		if (!startedAt) return;
		const res = await fetch(`/api/brews/${data.brew.id}/events`, {
			method: 'POST',
			headers: { 'content-type': 'application/json' },
			body: JSON.stringify({ elapsedMs, type, waterG })
		});
		if (res.ok) {
			const event = (await res.json()) as BrewEvent;
			events.push(event);
			if (type === 'pour_end') {
				pendingWaterFor = event.id;
				waterInput = '';
				setTimeout(() => waterField?.focus(), 10);
			}
		}
	}

	async function undo() {
		const res = await fetch(`/api/brews/${data.brew.id}/events`, { method: 'DELETE' });
		if (res.ok) {
			const { removed } = (await res.json()) as { removed: number | null };
			if (removed !== null) events = events.filter((e) => e.id !== removed);
			if (pendingWaterFor === removed) pendingWaterFor = null;
		}
	}

	async function saveWater() {
		if (pendingWaterFor === null) return;
		const raw = String(waterInput).trim();
		const value = Number(raw);
		if (Number.isFinite(value) && raw !== '') {
			const res = await fetch(`/api/brews/${data.brew.id}/events`, {
				method: 'PATCH',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify({ eventId: pendingWaterFor, waterG: value })
			});
			if (res.ok) {
				const updated = (await res.json()) as BrewEvent;
				events = events.map((e) => (e.id === updated.id ? updated : e));
			}
		}
		pendingWaterFor = null;
	}

	function togglePour() {
		if (openPour) {
			mark('pour_end');
		} else {
			mark(pourCount === 0 ? 'bloom_start' : 'pour_start');
		}
	}

	function onKeydown(e: KeyboardEvent) {
		const target = e.target as HTMLElement;
		if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
			if (e.key === 'Enter' && pendingWaterFor !== null) {
				e.preventDefault();
				saveWater();
			}
			if (e.key === 'Escape') pendingWaterFor = null;
			return;
		}
		// A just-clicked control keeps focus; space must mean "mark pour",
		// never "re-click that button".
		if (target.tagName === 'BUTTON' && e.key === ' ') {
			e.preventDefault();
			target.blur();
		}
		if (!startedAt) {
			if (e.key === ' ' || e.key === 'Enter') {
				e.preventDefault();
				start().then(() => mark('bloom_start'));
			}
			return;
		}
		if (!running) return;
		if (e.key === ' ') {
			e.preventDefault();
			togglePour();
		} else if (e.key === 's') mark('swirl');
		else if (e.key === 't') mark('stir');
		else if (e.key === 'v') mark('valve_open');
		else if (e.key === 'p') mark(events.some((ev) => ev.type === 'press_start') ? 'press_end' : 'press_start');
		else if (e.key === 'd') mark('drawdown_end');
		else if (e.key === 'u') undo();
	}

	const EVENT_LABELS: Record<string, string> = {
		bloom_start: 'Bloom',
		pour_start: 'Pour',
		pour_end: 'Pour end',
		swirl: 'Swirl',
		stir: 'Stir',
		valve_open: 'Valve open',
		press_start: 'Press',
		press_end: 'Press end',
		drawdown_end: 'Drawdown done'
	};
</script>

<svelte:window onkeydown={onKeydown} />
<svelte:head><title>The Counter: brewing cup {data.brew.id}</title></svelte:head>

<div class="head">
	<div>
		<p class="micro">Cup {String(data.brew.id).padStart(3, '0')} · {methodLabel(data.brew.method)}</p>
		<h2 class="etch bean">{data.bean?.name ?? 'Unnamed cup'}</h2>
	</div>
	{#if running}<span class="live micro">Live</span>{/if}
</div>

<div class="stage" class:running>
	<div class="timer num" aria-live="off">{clock(elapsedMs / 1000)}</div>

	{#if !startedAt}
		<button class="begin label-caps" onclick={() => start().then(() => mark('bloom_start'))}>
			Start brew
		</button>
		<p class="micro hint">space: start and bloom</p>
		<a class="micro skip" href="/brew/{data.brew.id}/taste?manual=1">skip timer, type times</a>
	{:else}
		{#if nextPlanned && running}
			<p class="next num" class:due={elapsedMs / 1000 >= nextPlanned.at - 5}>
				Next: {nextPlanned.label} → {nextPlanned.targetG} g at {clock(nextPlanned.at)}
			</p>
		{:else if running}
			<p class="next num">Plan complete. d: drawdown</p>
		{/if}

		<ol class="events num">
			{#each events as event (event.id)}
				<li>
					<span class="at">{clock(event.elapsedMs / 1000)}</span>
					<span class="type" class:accent={event.type === 'bloom_start' || event.type === 'pour_start'}>
						{EVENT_LABELS[event.type] ?? event.type}
					</span>
					{#if event.waterG !== null}
						<span class="water">{event.waterG} g</span>
					{:else if event.id === pendingWaterFor}
						<input
							bind:this={waterField}
							bind:value={waterInput}
							onblur={saveWater}
							type="number"
							step="1"
							placeholder="scale g"
							aria-label="Water at this point, grams"
						/>
					{/if}
				</li>
			{/each}
		</ol>

		{#if running}
			<div class="controls">
				<button onclick={togglePour} class="key">space · {openPour ? 'end pour' : pourCount === 0 ? 'bloom' : 'pour'}</button>
				<button onclick={() => mark('swirl')} class="key">s · swirl</button>
				<button onclick={() => mark('stir')} class="key">t · stir</button>
				{#if data.brew.method === 'hario-switch'}
					<button onclick={() => mark('valve_open')} class="key">v · valve</button>
				{/if}
				{#if data.brew.method.startsWith('aeropress')}
					<button onclick={() => mark(events.some((ev) => ev.type === 'press_start') ? 'press_end' : 'press_start')} class="key">p · press</button>
				{/if}
				<button onclick={() => mark('drawdown_end')} class="key">d · drawdown</button>
				<button onclick={undo} class="key undo">u · undo</button>
			</div>
		{:else}
			<div class="done">
				<form method="POST" action="?/finish" use:enhance>
					<button class="finish label-caps" type="submit">Taste</button>
				</form>
			</div>
		{/if}
	{/if}
</div>

<style>
	.head {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 10px;
	}
	.head p {
		margin: 0 0 4px;
	}
	.bean {
		font-size: 1.6rem;
		font-weight: 600;
		letter-spacing: -0.015em;
		margin: 0;
		line-height: 1;
	}
	.live {
		border: 1px solid var(--solar);
		color: var(--solar);
		font-weight: 600;
		padding: 3px 7px;
	}
	/* The red room: one full Solar Red field with a hard diagonal ember shadow. */
	.stage {
		background:
			linear-gradient(115deg, rgba(92, 14, 6, 0) 52%, rgba(92, 14, 6, 0.28) 52.15%),
			var(--field-solar);
		color: #fff6f3;
		padding: 34px 22px 26px;
		text-align: center;
	}
	.timer {
		width: 230px;
		height: 230px;
		margin: 0 auto;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 4.4rem;
		font-weight: 600;
		letter-spacing: 0.04em;
		border: 7px solid transparent;
		border-radius: 50%;
		background:
			var(--field-solar) padding-box,
			conic-gradient(
					from 210deg,
					var(--chrome-1),
					var(--chrome-2) 22%,
					var(--chrome-3) 47%,
					var(--chrome-4) 74%,
					var(--chrome-5) 92%,
					var(--chrome-1)
				)
				border-box;
	}
	.begin {
		display: block;
		margin: 22px auto 0;
		background: #fff6f3;
		color: var(--ember-deep);
		border: none;
		font-size: 0.85rem;
		font-weight: 600;
		padding: 13px 26px;
		cursor: pointer;
	}
	.begin:hover {
		background: #ffffff;
	}
	.hint {
		margin: 12px 0 0;
		color: rgba(255, 246, 243, 0.75);
	}
	.skip {
		display: inline-block;
		margin-top: 10px;
		color: rgba(255, 246, 243, 0.75);
	}
	.next {
		margin: 14px 0 0;
		font-size: 0.9rem;
		font-weight: 600;
		color: rgba(255, 246, 243, 0.8);
	}
	.next.due {
		color: #ffffff;
	}
	.events {
		list-style: none;
		margin: 16px auto 0;
		padding: 0;
		max-width: 380px;
		text-align: left;
	}
	.events li {
		display: flex;
		align-items: baseline;
		gap: 12px;
		font-size: 0.9rem;
		line-height: 2;
		border-bottom: 1px solid rgba(255, 246, 243, 0.22);
	}
	.events .at {
		width: 44px;
		color: rgba(255, 246, 243, 0.7);
	}
	.events .type {
		flex: 1;
		font-weight: 600;
		color: #fff6f3;
	}
	.events .type.accent {
		color: #ffe1b8;
	}
	.events .water {
		font-weight: 600;
	}
	.events input {
		width: 80px;
		font-family: var(--font-mono);
		color: #fff6f3;
		background: rgba(255, 255, 255, 0.14);
		border: none;
		border-bottom: 2px solid #ffe1b8;
		padding: 2px 4px;
	}
	.events input::placeholder {
		color: rgba(255, 246, 243, 0.6);
	}
	.events input:focus {
		outline: none;
	}
	.controls {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		justify-content: center;
		margin-top: 20px;
	}
	.key {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		background: transparent;
		border: 1px solid rgba(255, 246, 243, 0.55);
		color: #fff6f3;
		padding: 7px 10px;
		cursor: pointer;
	}
	.key:hover {
		border-color: #ffffff;
	}
	.key.undo {
		border-style: dashed;
	}
	.done {
		margin-top: 20px;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 10px;
	}
	.finish {
		background: #fff6f3;
		color: var(--ember-deep);
		border: none;
		font-size: 0.85rem;
		font-weight: 600;
		padding: 13px 24px;
		cursor: pointer;
	}
	.finish:hover {
		background: #ffffff;
	}
</style>
