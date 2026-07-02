import type { Component } from 'svelte';
import type { InkKey } from './keys';
import V60 from './V60.svelte';
import HarioSwitch from './HarioSwitch.svelte';
import Aeropress from './Aeropress.svelte';
import Chemex from './Chemex.svelte';
import Beans from './Beans.svelte';
import Kettle from './Kettle.svelte';
import Steam from './Steam.svelte';

export { V60, HarioSwitch, Aeropress, Chemex, Beans, Kettle, Steam };
export { INK_KEYS, type InkKey } from './keys';

export type InkProps = { size?: number; onDark?: boolean };

/** Keyed by BrewMethod.illustration — every pickable method must resolve here. */
export const ILLUSTRATIONS: Record<InkKey, Component<InkProps>> = {
	v60: V60,
	switch: HarioSwitch,
	aeropress: Aeropress,
	chemex: Chemex
};
