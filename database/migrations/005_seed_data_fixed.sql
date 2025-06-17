-- 005_seed_data_fixed.sql
-- Fixed seed data that works with the current schema

-- Insert brew methods (if they don't exist)
INSERT INTO brew_methods (slug, method_type, name, display_name, template)
SELECT * FROM (VALUES
    ('v60-hoffman', 'V60', 'Hoffman V60 Method', 'Hoffman V60 Method',
     '{"ratio": "1:16", "water_temp": 93, "grind": "medium-fine", "steps": [
        {"time": 0, "action": "bloom", "water": 50, "notes": "Gentle swirl after pouring"},
        {"time": 45, "action": "pour", "water": 100, "notes": "Pour in circles"},
        {"time": 75, "action": "pour", "water": 100, "notes": "Keep water level consistent"},
        {"time": 105, "action": "pour", "water": 50, "notes": "Final center pour"}
     ]}'::jsonb),
    
    ('v60-4-6', 'V60', 'Kasuya 4:6 Method', 'Kasuya 4:6 Method',
     '{"ratio": "1:15", "water_temp": 90, "grind": "coarse", "notes": "Adjust first two pours for acidity/sweetness balance"}'::jsonb),
    
    ('espresso-standard', 'Espresso', 'Standard Espresso', 'Standard Espresso',
     '{"dose": 18, "yield": 36, "time": 28, "temperature": 93, "grind": "fine"}'::jsonb),
    
    ('chemex-standard', 'Chemex', 'Chemex Standard', 'Chemex Standard',
     '{"ratio": "1:15", "water_temp": 96, "grind": "medium-coarse", "total_time": 240}'::jsonb),
    
    ('french-press', 'French Press', 'French Press Immersion', 'French Press Immersion',
     '{"ratio": "1:15", "water_temp": 95, "grind": "coarse", "steep_time": 240}'::jsonb)
) AS v(slug, method_type, name, display_name, template)
WHERE NOT EXISTS (
    SELECT 1 FROM brew_methods WHERE slug = v.slug
);

-- Insert sample coffee beans (optional - only if table is empty)
INSERT INTO coffee_beans (slug, name, roaster, origin, altitude, process_type, roast_type, roast_date, notes, display_name)
SELECT * FROM (VALUES
    ('bb-ethiopia-2024-03', 'Ethiopia Yirgacheffe', 'Blue Bottle', 'Ethiopia', 1850, 'Washed', 'Light', '2024-03-15'::date,
     'Floral and bright with notes of lemon and bergamot', 'Blue Bottle - Ethiopia Yirgacheffe (Mar 2024)'),
    
    ('onyx-colombia-2024-03', 'Colombia Geisha', 'Onyx', 'Colombia', 2000, 'Natural', 'Light', '2024-03-18'::date,
     'Complex and sweet with tropical fruit notes', 'Onyx - Colombia Geisha (Mar 2024)')
) AS v(slug, name, roaster, origin, altitude, process_type, roast_type, roast_date, notes, display_name)
WHERE NOT EXISTS (
    SELECT 1 FROM coffee_beans WHERE slug = v.slug
);