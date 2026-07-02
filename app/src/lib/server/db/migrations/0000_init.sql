CREATE TABLE IF NOT EXISTS beans (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL,
	origin_country TEXT,
	origin_region TEXT,
	variety TEXT,
	process TEXT,
	roast_date TEXT,
	roast_level TEXT,
	purchase_date TEXT,
	bag_size_g REAL,
	notes TEXT,
	archived INTEGER NOT NULL DEFAULT 0,
	created_at TEXT NOT NULL,
	updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS brews (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	bean_id INTEGER REFERENCES beans(id),
	brewed_at TEXT NOT NULL,
	method TEXT NOT NULL,
	status TEXT NOT NULL DEFAULT 'complete',
	archived INTEGER NOT NULL DEFAULT 0,
	grinder TEXT,
	grind_size REAL,
	dose_g REAL,
	water_g REAL,
	temp_c REAL,
	hot_water_g REAL,
	ice_g REAL,
	mug_weight_g REAL,
	final_combined_weight_g REAL,
	brew_mass_g REAL,
	tds_percent REAL,
	total_time_s REAL,
	score_complexity REAL,
	score_bitterness REAL,
	score_mouthfeel REAL,
	flavor_profile TEXT,
	tasting_notes TEXT,
	notes TEXT,
	method_params TEXT,
	legacy TEXT,
	created_at TEXT NOT NULL,
	updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS brew_events (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	brew_id INTEGER NOT NULL REFERENCES brews(id) ON DELETE CASCADE,
	elapsed_ms INTEGER NOT NULL,
	type TEXT NOT NULL,
	water_g REAL,
	note TEXT
);

CREATE INDEX IF NOT EXISTS idx_brews_bean_id ON brews(bean_id);
CREATE INDEX IF NOT EXISTS idx_brews_brewed_at ON brews(brewed_at);
CREATE INDEX IF NOT EXISTS idx_brew_events_brew_id ON brew_events(brew_id);
