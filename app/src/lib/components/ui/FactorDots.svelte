<script lang="ts">
	import { scoreForKey, tapDot } from '$lib/domain/factor-score';

	/**
	 * Half-step 0–5 rating as five dots. Each dot is one wet-hand target:
	 * a tap sets it full, a second tap takes the half, a third clears. A
	 * focused factor also takes 1 to 5, 0, and the arrows. Renders ● ◐ ○ in ink.
	 */
	let {
		name,
		label,
		value = $bindable(null)
	}: { name: string; label: string; value?: number | null } = $props();

	function glyph(index: number): string {
		if (value === null) return '○';
		const filled = value - index;
		if (filled >= 1) return '●';
		if (filled >= 0.5) return '◐';
		return '○';
	}

	function onkeydown(e: KeyboardEvent) {
		if (e.metaKey || e.ctrlKey || e.altKey) return;
		const next = scoreForKey(value, e.key);
		if (next === undefined) return;
		e.preventDefault();
		value = next;
	}
</script>

<div class="factor">
	<span class="micro">{label}</span>
	<span
		class="dots"
		role="slider"
		tabindex="0"
		aria-label="{label} score"
		aria-valuemin={0}
		aria-valuemax={5}
		aria-valuenow={value ?? 0}
		aria-valuetext={value === null ? 'unscored' : value.toFixed(1)}
		{onkeydown}
	>
		{#each { length: 5 } as _, i (i)}
			<button
				type="button"
				class="dot"
				tabindex="-1"
				aria-label="{label} {i + 1}"
				onclick={() => (value = tapDot(value, i))}
			>
				<span aria-hidden="true">{glyph(i)}</span>
			</button>
		{/each}
	</span>
	<span class="num readout">{value === null ? '—' : value.toFixed(1)}</span>
	<input type="hidden" {name} value={value ?? ''} />
</div>

<style>
	.factor {
		display: flex;
		align-items: center;
		gap: 12px;
	}
	.factor .micro {
		width: 90px;
	}
	.dots {
		display: inline-flex;
		gap: 2px;
		font-size: 1.25rem;
		line-height: 1;
	}
	/* One target per dot, sized for a wet thumb. */
	.dot {
		width: 34px;
		height: 34px;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		background: none;
		border: none;
		padding: 0;
		color: inherit;
		font: inherit;
		cursor: pointer;
	}
	.readout {
		font-weight: 600;
		width: 34px;
		text-align: right;
	}
</style>
