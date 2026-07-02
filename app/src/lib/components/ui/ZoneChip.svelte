<script lang="ts">
	/**
	 * Extraction/strength zone chip. Ideal is a solid leaf block (the one you
	 * want to collect); everything else is an outlined correction note.
	 */
	let { zone }: { zone: 'under' | 'ideal' | 'over' | 'weak' | 'strong' } = $props();

	const styles = {
		under: { color: 'var(--ochre-deep)', border: 'var(--ochre)', bg: 'transparent' },
		ideal: { color: 'var(--paper)', border: 'var(--leaf)', bg: 'var(--leaf)' },
		over: { color: 'var(--clay-deep)', border: 'var(--clay)', bg: 'transparent' },
		weak: { color: 'var(--ink-soft)', border: 'var(--line-soft)', bg: 'transparent' },
		strong: { color: 'var(--roast)', border: 'var(--roast)', bg: 'transparent' }
	} as const;

	const s = $derived(styles[zone]);
</script>

<span
	class="chip num"
	style:color={s.color}
	style:border-color={s.border}
	style:background={s.bg}>{zone}</span
>

<style>
	.chip {
		display: inline-block;
		border: 1px solid;
		font-size: 0.625rem;
		font-weight: 600;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		padding: 3px 8px;
	}
</style>
