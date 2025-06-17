-- 003_seed_data.sql
-- Optional: Sample data for testing

-- Only insert if tables are empty (for development)
DO $$
BEGIN
    -- Check if we already have data
    IF NOT EXISTS (SELECT 1 FROM brew_methods LIMIT 1) THEN
        -- Insert sample brew methods
        INSERT INTO brew_methods (slug, display_name, method_type, template) VALUES
        ('v60-hoffman', 'Hoffman V60 Method', 'V60', 
         '{"ratio": "1:16", "water_temp": 93, "grind": "medium-fine", "steps": [
            {"time": 0, "action": "bloom", "water": 50, "notes": "Gentle swirl after pouring"},
            {"time": 45, "action": "pour", "water": 100, "notes": "Pour in circles"},
            {"time": 75, "action": "pour", "water": 100, "notes": "Keep water level consistent"},
            {"time": 105, "action": "pour", "water": 50, "notes": "Final center pour"}
         ]}'),
        
        ('v60-4-6', 'Kasuya 4:6 Method', 'V60', 
         '{"ratio": "1:15", "water_temp": 90, "grind": "coarse", "notes": "Adjust first two pours for acidity/sweetness balance"}'),
        
        ('espresso-standard', 'Standard Espresso', 'Espresso', 
         '{"dose": 18, "yield": 36, "time": 28, "temperature": 93, "grind": "fine"}'),
        
        ('chemex-standard', 'Chemex Standard', 'Chemex', 
         '{"ratio": "1:15", "water_temp": 96, "grind": "medium-coarse", "total_time": 240}'),
        
        ('french-press', 'French Press Immersion', 'French Press', 
         '{"ratio": "1:15", "water_temp": 95, "grind": "coarse", "steep_time": 240}');
    END IF;

    -- Check if we already have coffee beans
    IF NOT EXISTS (SELECT 1 FROM coffee_beans LIMIT 1) THEN
        -- Insert sample coffee beans (optional - delete this section if you want to start fresh)
        INSERT INTO coffee_beans (slug, name, roaster, origin, altitude, process_type, roast_type, roast_date, notes) VALUES
        ('bb-ethiopia-2024-03', 'Ethiopia Yirgacheffe', 'Blue Bottle', 'Ethiopia', 1850, 'Washed', 'Light', '2024-03-15', 
         'Floral and bright with notes of lemon and bergamot'),
        
        ('onyx-colombia-2024-03', 'Colombia Geisha', 'Onyx', 'Colombia', 2000, 'Natural', 'Light', '2024-03-18',
         'Complex and sweet with tropical fruit notes');
    END IF;
END $$;