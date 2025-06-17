-- 002_add_human_readable_ids.sql
-- Add human-readable identifiers and calculated fields

-- Add slug columns
ALTER TABLE coffee_beans ADD COLUMN IF NOT EXISTS slug VARCHAR(100) UNIQUE;
ALTER TABLE brew_methods ADD COLUMN IF NOT EXISTS slug VARCHAR(100) UNIQUE;

-- Add display name for coffee beans
ALTER TABLE coffee_beans ADD COLUMN IF NOT EXISTS display_name VARCHAR(255) GENERATED ALWAYS AS 
    (roaster || ' - ' || name || ' (' || TO_CHAR(roast_date, 'Mon YYYY') || ')') STORED;

-- Add display name for brew methods
ALTER TABLE brew_methods ADD COLUMN IF NOT EXISTS display_name VARCHAR(255);

-- Add calculated fields to coffee_cups
ALTER TABLE coffee_cups ADD COLUMN IF NOT EXISTS days_off_roast INTEGER GENERATED ALWAYS AS 
    (EXTRACT(DAY FROM brew_date - (SELECT roast_date FROM coffee_beans WHERE id = bean_id))) STORED;

ALTER TABLE coffee_cups ADD COLUMN IF NOT EXISTS extraction_yield DECIMAL(4,2) GENERATED ALWAYS AS 
    (CASE 
        WHEN tds_percentage IS NOT NULL AND post_brew_mass IS NOT NULL AND pre_brew_mass IS NOT NULL AND pre_brew_mass > 0
        THEN (tds_percentage * post_brew_mass / pre_brew_mass)
        ELSE NULL
    END) STORED;

-- Add unique constraint to prevent duplicate beans
ALTER TABLE coffee_beans ADD CONSTRAINT unique_bean_per_roast UNIQUE (roaster, name, roast_date);

-- Create indexes for slug lookups
CREATE INDEX IF NOT EXISTS idx_beans_slug ON coffee_beans(slug);
CREATE INDEX IF NOT EXISTS idx_methods_slug ON brew_methods(slug);

-- Create a view for easier querying with readable names
CREATE OR REPLACE VIEW readable_coffee_cups AS
SELECT 
    cc.id,
    cb.slug as bean_slug,
    cb.display_name as coffee,
    bm.slug as method_slug,
    bm.display_name as brew_method,
    cc.brew_date,
    cc.days_off_roast,
    cc.extraction_yield,
    cc.tds_percentage,
    cc.rating,
    cc.flavor_tags,
    cc.notes
FROM coffee_cups cc
JOIN coffee_beans cb ON cc.bean_id = cb.id
LEFT JOIN brew_methods bm ON cc.brew_method_id = bm.id;