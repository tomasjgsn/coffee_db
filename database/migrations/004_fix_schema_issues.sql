-- 004_fix_schema_issues.sql
-- Fix issues from previous migrations

-- First, let's check and add display_name as a regular column (not generated)
ALTER TABLE coffee_beans 
ADD COLUMN IF NOT EXISTS display_name VARCHAR(255);

-- Update display_name for existing records
UPDATE coffee_beans 
SET display_name = COALESCE(roaster, '') || ' - ' || name || ' (' || TO_CHAR(roast_date, 'Mon YYYY') || ')'
WHERE display_name IS NULL;

-- Add display_name to brew_methods if it doesn't exist
ALTER TABLE brew_methods 
ADD COLUMN IF NOT EXISTS display_name VARCHAR(255);

-- Fix the days_off_roast column (can't use subquery in generated column)
-- First drop if it exists as generated
ALTER TABLE coffee_cups 
DROP COLUMN IF EXISTS days_off_roast;

-- Add as a regular column
ALTER TABLE coffee_cups 
ADD COLUMN IF NOT EXISTS days_off_roast INTEGER;

-- Create a function to calculate days off roast
CREATE OR REPLACE FUNCTION calculate_days_off_roast() 
RETURNS TRIGGER AS $$
BEGIN
    NEW.days_off_roast := EXTRACT(DAY FROM NEW.brew_date - 
        (SELECT roast_date FROM coffee_beans WHERE id = NEW.bean_id));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-calculate days_off_roast
DROP TRIGGER IF EXISTS update_days_off_roast ON coffee_cups;
CREATE TRIGGER update_days_off_roast 
BEFORE INSERT OR UPDATE ON coffee_cups
FOR EACH ROW EXECUTE FUNCTION calculate_days_off_roast();

-- Update existing records
UPDATE coffee_cups cc
SET days_off_roast = EXTRACT(DAY FROM cc.brew_date - 
    (SELECT roast_date FROM coffee_beans WHERE id = cc.bean_id))
WHERE days_off_roast IS NULL;

-- Create or replace the view (now that display_name exists)
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