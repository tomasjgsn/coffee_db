-- 001_initial_schema.sql
-- Initial database schema for coffee tracking system

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Coffee beans table
CREATE TABLE IF NOT EXISTS coffee_beans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    roaster VARCHAR(255),
    origin VARCHAR(255),
    altitude INTEGER,
    process_type VARCHAR(100),
    roast_type VARCHAR(50),
    roast_date DATE,
    purchase_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Brew methods table
CREATE TABLE IF NOT EXISTS brew_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    method_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    template JSONB NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Coffee cups table (individual brews)
CREATE TABLE IF NOT EXISTS coffee_cups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bean_id UUID REFERENCES coffee_beans(id) ON DELETE CASCADE,
    brew_method_id UUID REFERENCES brew_methods(id) ON DELETE SET NULL,
    brew_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Brew parameters (will vary by method)
    brew_parameters JSONB,
    
    -- Measurements
    pre_brew_mass DECIMAL(6,2),
    post_brew_mass DECIMAL(6,2),
    tds_percentage DECIMAL(4,2),
    
    -- Ratings
    flavor_tags TEXT[],
    rating VARCHAR(20) CHECK (rating IN ('thumbs_down', 'thumbs_up', 'super_cup')),
    notes TEXT,
    
    -- User tracking for future
    user_id UUID
);

-- Indexes for performance
CREATE INDEX idx_cups_bean_id ON coffee_cups(bean_id);
CREATE INDEX idx_cups_brew_date ON coffee_cups(brew_date);
CREATE INDEX idx_cups_rating ON coffee_cups(rating);
CREATE INDEX idx_cups_flavor_tags ON coffee_cups USING GIN(flavor_tags);
CREATE INDEX idx_beans_roaster ON coffee_beans(roaster);
CREATE INDEX idx_beans_origin ON coffee_beans(origin);