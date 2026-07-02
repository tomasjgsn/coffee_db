import type { MethodId } from './methods';

export interface PlannedPour {
	/** Target start time, seconds from brew start. */
	at: number;
	/** Cumulative water target in grams (for iced: hot water only). */
	targetG: number;
	label: string;
}

export interface PourPlan {
	pours: PlannedPour[];
}

export interface RecipeTemplate {
	doseG: number;
	waterG: number;
	tempC: number;
	grindSize: number | null;
	iceG: number | null;
	hotWaterG: number | null;
	plan: PourPlan;
}

/**
 * Starting recipes for a bean never brewed before. Real prefill always
 * prefers the last brew of the same bean + method.
 */
export function templateFor(method: MethodId): RecipeTemplate {
	switch (method) {
		case 'v60':
		case 'v60-ceramic': {
			const dose = 18;
			const water = 300;
			return {
				doseG: dose,
				waterG: water,
				tempC: 95,
				grindSize: 6,
				iceG: null,
				hotWaterG: null,
				plan: {
					pours: [
						{ at: 0, targetG: dose * 3, label: 'Bloom' },
						{ at: 45, targetG: Math.round(water * 0.6), label: 'Pour 2' },
						{ at: 90, targetG: water, label: 'Pour 3' }
					]
				}
			};
		}
		case 'chemex': {
			const dose = 30;
			const water = 500;
			return {
				doseG: dose,
				waterG: water,
				tempC: 96,
				grindSize: 7,
				iceG: null,
				hotWaterG: null,
				plan: {
					pours: [
						{ at: 0, targetG: dose * 3, label: 'Bloom' },
						{ at: 45, targetG: Math.round(water * 0.4), label: 'Pour 2' },
						{ at: 105, targetG: Math.round(water * 0.7), label: 'Pour 3' },
						{ at: 165, targetG: water, label: 'Pour 4' }
					]
				}
			};
		}
		case 'hario-switch': {
			const dose = 20;
			const water = 300;
			return {
				doseG: dose,
				waterG: water,
				tempC: 90,
				grindSize: 6.5,
				iceG: null,
				hotWaterG: null,
				plan: {
					pours: [
						{ at: 0, targetG: dose * 3, label: 'Bloom' },
						{ at: 40, targetG: water, label: 'Fill' }
					]
				}
			};
		}
		case 'aeropress': {
			const dose = 15;
			const water = 220;
			return {
				doseG: dose,
				waterG: water,
				tempC: 90,
				grindSize: 5,
				iceG: null,
				hotWaterG: null,
				plan: {
					pours: [{ at: 0, targetG: water, label: 'Fill' }]
				}
			};
		}
		case 'aeropress-iced': {
			// Workshop-style flash brew: hot press straight onto ice.
			const dose = 22;
			const water = 250;
			const ice = 100;
			return {
				doseG: dose,
				waterG: water,
				tempC: 95,
				grindSize: 4.5,
				iceG: ice,
				hotWaterG: water - ice,
				plan: {
					pours: [{ at: 0, targetG: water - ice, label: 'Fill' }]
				}
			};
		}
	}
}
