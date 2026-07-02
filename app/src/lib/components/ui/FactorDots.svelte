<script lang="ts">
	/**
	 * Half-step 0–5 rating as five dots; each dot has a left (half) and right
	 * (full) hit zone. Renders ● ◐ ○ in ink.
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

	function set(index: number, half: boolean) {
		const next = index + (half ? 0.5 : 1);
		value = value === next ? null : next;
	}
</script>

<div class="factor">
	<span class="micro">{label}</span>
	<span class="dots" role="radiogroup" aria-label="{label} score">
		{#each { length: 5 } as _, i (i)}
			<span class="dot">
				<button
					type="button"
					class="half left"
					aria-label="{label} {i + 0.5}"
					onclick={() => set(i, true)}
				></button>
				<button
					type="button"
					class="half right"
					aria-label="{label} {i + 1}"
					onclick={() => set(i, false)}
				></button>
				<span aria-hidden="true">{glyph(i)}</span>
			</span>
		{/each}
	</span>
	<span class="num readout">{value === null ? '—' : value.toFixed(1)}</span>
	<input type="hidden" {name} value={value ?? ''} />
</div>

<style>
	.factor {
		display: flex;
		align-items: baseline;
		gap: 12px;
	}
	.factor .micro {
		width: 90px;
	}
	.dots {
		display: inline-flex;
		gap: 6px;
		font-size: 1.25rem;
		line-height: 1;
	}
	.dot {
		position: relative;
		display: inline-block;
	}
	.half {
		position: absolute;
		top: 0;
		bottom: 0;
		width: 50%;
		background: none;
		border: none;
		cursor: pointer;
		padding: 0;
	}
	.half.left {
		left: 0;
	}
	.half.right {
		right: 0;
	}
	.readout {
		font-weight: 600;
		width: 34px;
		text-align: right;
	}
</style>
