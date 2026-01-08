-- Add title/name to group gift expenses (for existing databases)
ALTER TABLE IF EXISTS group_gift_expenses
  ADD COLUMN IF NOT EXISTS title TEXT;
