-- Migration to add reserved state for items
-- Run this SQL script in your database

-- Add reserved columns to wishlist_items table
ALTER TABLE wishlist_items
ADD COLUMN IF NOT EXISTS is_reserved BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS reserved_by VARCHAR(100);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_wishlist_items_reserved ON wishlist_items(is_reserved);

COMMIT;
