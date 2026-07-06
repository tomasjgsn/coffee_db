/**
 * The brew methods Tomas actually uses. Only these appear in pickers.
 * Legacy methods (French Press, Espresso) remain readable in history but
 * are never offered for new brews.
 */

export type MethodId =
	| 'v60'
	| 'v60-ceramic'
	| 'hario-switch'
	| 'aeropress'
	| 'aeropress-iced'
	| 'chemex';

export type MethodCategory = 'pour-over' | 'hybrid' | 'immersion';

export interface BrewMethod {
	id: MethodId;
	label: string;
	shortLabel: string;
	category: MethodCategory;
	/** Which engraved miniature to render (see $lib/components/engravings). */
	illustration: 'v60' | 'switch' | 'aeropress' | 'chemex';
	/** Legacy brew_device values from cups_of_coffee.csv that map to this method. */
	legacyDevices: string[];
	/** Iced methods split water into hot water + ice; totals feed ratio and EY. */
	iced: boolean;
}

export const METHODS: readonly BrewMethod[] = [
	{
		id: 'v60',
		label: 'V60',
		shortLabel: 'V60',
		category: 'pour-over',
		illustration: 'v60',
		legacyDevices: ['V60', 'Hoffman top up'],
		iced: false
	},
	{
		id: 'v60-ceramic',
		label: 'V60 ceramic',
		shortLabel: 'V60c',
		category: 'pour-over',
		illustration: 'v60',
		legacyDevices: ['V60 ceramic'],
		iced: false
	},
	{
		id: 'hario-switch',
		label: 'Hario Switch',
		shortLabel: 'Switch',
		category: 'hybrid',
		illustration: 'switch',
		legacyDevices: ['Hario Switch'],
		iced: false
	},
	{
		id: 'aeropress',
		label: 'Aeropress',
		shortLabel: 'Aero',
		category: 'immersion',
		illustration: 'aeropress',
		legacyDevices: ['Aeropress'],
		iced: false
	},
	{
		id: 'aeropress-iced',
		label: 'Aeropress flash iced',
		shortLabel: 'Aero iced',
		category: 'immersion',
		illustration: 'aeropress',
		legacyDevices: [],
		iced: true
	},
	{
		id: 'chemex',
		label: 'Chemex',
		shortLabel: 'Chemex',
		category: 'pour-over',
		illustration: 'chemex',
		legacyDevices: ['Chemex'],
		iced: false
	}
] as const;

/** Legacy devices kept out of pickers but still shown in history views. */
export const RETIRED_DEVICES = ['French Press', 'Espresso'] as const;

export function methodById(id: string): BrewMethod | undefined {
	return METHODS.find((m) => m.id === id);
}

export function methodForLegacyDevice(device: string): BrewMethod | undefined {
	return METHODS.find((m) => m.legacyDevices.includes(device));
}

/** Display labels for methods that exist only in history. */
const HISTORIC_LABELS: Record<string, { label: string; shortLabel: string }> = {
	'french-press': { label: 'French press', shortLabel: 'Press' },
	espresso: { label: 'Espresso', shortLabel: 'Esp' },
	unknown: { label: 'Unrecorded', shortLabel: '—' }
};

export function methodLabel(id: string): string {
	return methodById(id)?.label ?? HISTORIC_LABELS[id]?.label ?? id;
}

export function methodShortLabel(id: string): string {
	return methodById(id)?.shortLabel ?? HISTORIC_LABELS[id]?.shortLabel ?? id;
}
