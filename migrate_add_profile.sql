-- Migration: Add birthday_person_profile field to wishlists table
-- Date: 2026-01-02
-- Description: Adds AI-generated profile field to store personalized birthday person profiles

-- Add the new column
ALTER TABLE wishlists
ADD COLUMN IF NOT EXISTS birthday_person_profile TEXT NULL;

-- Add a comment to the column
COMMENT ON COLUMN wishlists.birthday_person_profile IS 'AI-generated profile describing the birthday person based on their wishlist items';

-- Verify the change
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'wishlists'
AND column_name = 'birthday_person_profile';
