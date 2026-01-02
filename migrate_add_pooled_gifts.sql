-- Migration to add pooled gift functionality
-- Run this SQL script in your database

-- Step 1: Add new columns to wishlist_items table
ALTER TABLE wishlist_items 
ADD COLUMN IF NOT EXISTS item_type VARCHAR(20) DEFAULT 'normal' NOT NULL,
ADD COLUMN IF NOT EXISTS target_amount FLOAT,
ADD COLUMN IF NOT EXISTS current_amount FLOAT DEFAULT 0.0;

-- Step 2: Create contributions table
CREATE TABLE IF NOT EXISTS contributions (
    id VARCHAR(36) PRIMARY KEY,
    item_id VARCHAR(36) NOT NULL,
    contributor_name VARCHAR(100) NOT NULL,
    amount FLOAT NOT NULL CHECK (amount > 0),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (item_id) REFERENCES wishlist_items(id) ON DELETE CASCADE
);

-- Step 3: Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_contributions_item_id ON contributions(item_id);
CREATE INDEX IF NOT EXISTS idx_wishlist_items_type ON wishlist_items(item_type);

-- Step 4: Ensure product_url is nullable (in case it wasn't already)
ALTER TABLE wishlist_items ALTER COLUMN product_url DROP NOT NULL;

COMMIT;

