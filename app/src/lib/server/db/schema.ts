import { integer, real, sqliteTable, text } from 'drizzle-orm/sqlite-core';

/** A bag of beans on the shelf. */
export const beans = sqliteTable('beans', {
	id: integer('id').primaryKey({ autoIncrement: true }),
	name: text('name').notNull(),
	originCountry: text('origin_country'),
	originRegion: text('origin_region'),
	variety: text('variety'),
	process: text('process'),
	roastDate: text('roast_date'),
	roastLevel: text('roast_level'),
	purchaseDate: text('purchase_date'),
	bagSizeG: real('bag_size_g'),
	notes: text('notes'),
	archived: integer('archived', { mode: 'boolean' }).notNull().default(false),
	createdAt: text('created_at').notNull(),
	updatedAt: text('updated_at').notNull()
});

/**
 * One cup. Derived values (ratio, extraction yield, zones, overall, brew
 * score) are computed on read by $lib/brewing — never stored. Stored legacy
 * derived values live in `legacy` JSON for golden verification and export.
 */
export const brews = sqliteTable('brews', {
	id: integer('id').primaryKey({ autoIncrement: true }),
	beanId: integer('bean_id').references(() => beans.id),
	brewedAt: text('brewed_at').notNull(),
	/** Wall-clock ISO timestamp when the live timer started; elapsed time is always now − started_at. */
	startedAt: text('started_at'),
	method: text('method').notNull(),
	status: text('status', { enum: ['draft', 'complete'] }).notNull().default('complete'),
	archived: integer('archived', { mode: 'boolean' }).notNull().default(false),

	grinder: text('grinder'),
	grindSize: real('grind_size'),
	doseG: real('dose_g'),
	waterG: real('water_g'),
	tempC: real('temp_c'),
	/** Flash-iced split: hot_water_g + ice_g = water_g (total). */
	hotWaterG: real('hot_water_g'),
	iceG: real('ice_g'),

	mugWeightG: real('mug_weight_g'),
	finalCombinedWeightG: real('final_combined_weight_g'),
	brewMassG: real('brew_mass_g'),
	tdsPercent: real('tds_percent'),
	totalTimeS: real('total_time_s'),

	scoreComplexity: real('score_complexity'),
	scoreBitterness: real('score_bitterness'),
	scoreMouthfeel: real('score_mouthfeel'),
	flavorProfile: text('flavor_profile'),
	tastingNotes: text('tasting_notes'),
	notes: text('notes'),

	methodParams: text('method_params'),
	legacy: text('legacy'),

	createdAt: text('created_at').notNull(),
	updatedAt: text('updated_at').notNull()
});

/**
 * Timeline of a brew: bloom, pours, swirls, valve, press, drawdown. Captured
 * live by the brew companion; schema is forward-compatible with a future
 * smart scale streaming mass samples.
 */
export const brewEvents = sqliteTable('brew_events', {
	id: integer('id').primaryKey({ autoIncrement: true }),
	brewId: integer('brew_id')
		.notNull()
		.references(() => brews.id, { onDelete: 'cascade' }),
	elapsedMs: integer('elapsed_ms').notNull(),
	type: text('type', {
		enum: [
			'bloom_start',
			'pour_start',
			'pour_end',
			'swirl',
			'stir',
			'valve_open',
			'press_start',
			'press_end',
			'drawdown_end'
		]
	}).notNull(),
	waterG: real('water_g'),
	note: text('note')
});

export type Bean = typeof beans.$inferSelect;
export type NewBean = typeof beans.$inferInsert;
export type Brew = typeof brews.$inferSelect;
export type NewBrew = typeof brews.$inferInsert;
export type BrewEvent = typeof brewEvents.$inferSelect;
export type NewBrewEvent = typeof brewEvents.$inferInsert;
