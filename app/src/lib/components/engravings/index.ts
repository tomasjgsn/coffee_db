import type { Component } from 'svelte';
import type { InkKey } from './keys';
import Plate from './Plate.svelte';
import Mark from './Mark.svelte';
import Medallion from './Medallion.svelte';
import Pour from './Pour.svelte';
import Switch from './Switch.svelte';
import Press from './Press.svelte';
import Hourglass from './Hourglass.svelte';
import Eye from './Eye.svelte';
import Prism from './Prism.svelte';
import Drop from './Drop.svelte';
import Kettle from './Kettle.svelte';
import BeanBranch from './BeanBranch.svelte';
import Vessel from './Vessel.svelte';
import Habitat from './Habitat.svelte';

export {
	Plate,
	Mark,
	Medallion,
	Pour,
	Switch,
	Press,
	Hourglass,
	Eye,
	Prism,
	Drop,
	Kettle,
	BeanBranch,
	Vessel,
	Habitat
};

/** Method illustration keys resolve to engraved miniatures ( <g> content for Plate/Mark). */
export const ENGRAVINGS: Record<InkKey, Component> = {
	v60: Pour,
	switch: Switch,
	aeropress: Press,
	chemex: Hourglass
};

/** Plate captions, numbered as in the brand book. */
export const PLATE_CAPTIONS: Record<string, string> = {
	pour: 'plate i · the pour',
	switch: 'plate ii · the switch',
	press: 'plate iii · the press',
	hourglass: 'plate iv · the hourglass',
	eye: 'plate v · the eye',
	prism: 'plate vi · decomposition',
	drop: 'plate vii · the drop',
	kettle: 'plate viii · the kettle',
	beanBranch: 'plate ix · the bean branch',
	vessel: 'plate x · the vessel',
	habitat: 'plate xi · the habitat'
};
