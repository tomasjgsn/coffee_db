<script lang="ts">
	/**
	 * Extraction/strength zone chip. Ideal is a solid olive block; under and
	 * over are outlined corrections. Solar red is never a zone: over is ember.
	 */
	let { zone }: { zone: 'under' | 'ideal' | 'over' | 'weak' | 'strong' } = $props();

	const styles = {
		under: { color: 'var(--amber-deep)', border: 'var(--amber)', bg: 'transparent' },
		ideal: { color: 'var(--bone)', border: 'var(--olive)', bg: 'var(--olive)' },
		over: { color: 'var(--ember)', border: 'var(--ember)', bg: 'transparent' },
		weak: { color: 'var(--graphite-soft)', border: 'var(--line-strong)', bg: 'transparent' },
		strong: { color: 'var(--graphite)', border: 'var(--graphite)', bg: 'transparent' }
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
		padding: 3px 8px;
	}
</style>
