import { and, desc, eq } from 'drizzle-orm';
import type { Db } from '$lib/server/db';
import { brews, type Brew } from '$lib/server/db/schema';
import { METHODS, type MethodId } from '$lib/domain/methods';
import { templateFor, type PourPlan } from '$lib/domain/templates';

export interface Prefill {
	doseG: number;
	waterG: number;
	tempC: number;
	grindSize: number | null;
	grinder: string | null;
	iceG: number | null;
	hotWaterG: number | null;
	mugWeightG: number | null;
	plan: PourPlan;
	/** Where this recipe came from — shown as "same as Tuesday" context. */
	source: { kind: 'same-method' | 'same-bean' | 'template'; brewId: number | null; brewedAt: string | null };
}

/**
 * The recipe card starts as the last brew of this bean + method; failing
 * that, the last brew of the bean on any method; failing that, the method
 * template. Only complete brews count as precedent.
 */
export function prefillFor(db: Db, beanId: number, method: MethodId): Prefill {
	const sameMethod = lastBrew(db, beanId, method);
	const sameBean = sameMethod ?? lastBrew(db, beanId, null);
	const template = templateFor(method);

	const source: Prefill['source'] = sameMethod
		? { kind: 'same-method', brewId: sameMethod.id, brewedAt: sameMethod.brewedAt }
		: sameBean
			? { kind: 'same-bean', brewId: sameBean.id, brewedAt: sameBean.brewedAt }
			: { kind: 'template', brewId: null, brewedAt: null };

	const base = sameMethod ?? sameBean;

	return {
		doseG: base?.doseG ?? template.doseG,
		waterG: base?.waterG ?? template.waterG,
		tempC: base?.tempC ?? template.tempC,
		grindSize: base?.grindSize ?? template.grindSize,
		grinder: base?.grinder ?? lastGrinder(db),
		iceG: sameMethod?.iceG ?? template.iceG,
		hotWaterG: sameMethod?.hotWaterG ?? template.hotWaterG,
		mugWeightG: lastMugWeight(db),
		plan: planOf(sameMethod) ?? scaledTemplatePlan(template.plan, base?.waterG ?? template.waterG, template.waterG, base?.doseG ?? template.doseG),
		source
	};
}

function lastBrew(db: Db, beanId: number, method: MethodId | null): Brew | undefined {
	const conditions = method
		? and(eq(brews.beanId, beanId), eq(brews.method, method), eq(brews.status, 'complete'))
		: and(eq(brews.beanId, beanId), eq(brews.status, 'complete'));
	return db
		.select()
		.from(brews)
		.where(conditions)
		.orderBy(desc(brews.brewedAt), desc(brews.id))
		.limit(1)
		.get();
}

function planOf(brew: Brew | undefined): PourPlan | null {
	if (!brew?.methodParams) return null;
	try {
		const params = JSON.parse(brew.methodParams) as { plan?: PourPlan };
		if (params.plan?.pours?.length) return params.plan;
	} catch {
		return null;
	}
	return null;
}

/** Rescale a template plan's water targets when the base recipe uses a different total. */
function scaledTemplatePlan(plan: PourPlan, waterG: number, templateWaterG: number, doseG: number): PourPlan {
	if (waterG === templateWaterG) return plan;
	const factor = waterG / templateWaterG;
	return {
		pours: plan.pours.map((pour, i) => ({
			...pour,
			targetG:
				i === 0 && pour.label === 'Bloom'
					? Math.round(doseG * 3)
					: Math.min(waterG, Math.round(pour.targetG * factor))
		}))
	};
}

function lastGrinder(db: Db): string | null {
	const row = db
		.select({ grinder: brews.grinder })
		.from(brews)
		.orderBy(desc(brews.brewedAt), desc(brews.id))
		.limit(1)
		.get();
	return row?.grinder ?? null;
}

function lastMugWeight(db: Db): number | null {
	const rows = db
		.select({ mug: brews.mugWeightG })
		.from(brews)
		.orderBy(desc(brews.brewedAt), desc(brews.id))
		.limit(10)
		.all();
	return rows.find((r) => r.mug !== null)?.mug ?? null;
}

/** Every pickable method id, for validation. */
export const PICKABLE_METHOD_IDS = new Set(METHODS.map((m) => m.id));
