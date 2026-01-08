-- Regalos Colectivos (Groups + Invites + Expenses/Debts) + Birthday + Email logs
-- Target DB: PostgreSQL

-- 1) Users: add birthday (nullable for backward compatibility)
ALTER TABLE IF EXISTS users
  ADD COLUMN IF NOT EXISTS birthday DATE;

-- 2) Groups
CREATE TABLE IF NOT EXISTS groups (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  created_by_user_id TEXT NOT NULL REFERENCES users(id),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 3) Invites
CREATE TABLE IF NOT EXISTS group_invites (
  id TEXT PRIMARY KEY,
  group_id TEXT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
  token TEXT NOT NULL UNIQUE,
  created_by_user_id TEXT NOT NULL REFERENCES users(id),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMP NULL,
  max_uses INTEGER NULL,
  uses_count INTEGER NOT NULL DEFAULT 0,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_group_invites_token ON group_invites(token);
CREATE INDEX IF NOT EXISTS idx_group_invites_group_id ON group_invites(group_id);

-- 4) Members
CREATE TABLE IF NOT EXISTS group_members (
  id TEXT PRIMARY KEY,
  group_id TEXT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role TEXT NOT NULL DEFAULT 'MEMBER',
  joined_at TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(group_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_group_members_group_id ON group_members(group_id);
CREATE INDEX IF NOT EXISTS idx_group_members_user_id ON group_members(user_id);

-- 5) Expenses
CREATE TABLE IF NOT EXISTS group_gift_expenses (
  id TEXT PRIMARY KEY,
  group_id TEXT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
  birthday_user_id TEXT NOT NULL REFERENCES users(id),
  paid_by_user_id TEXT NOT NULL REFERENCES users(id),
  amount DOUBLE PRECISION NOT NULL,
  currency TEXT NOT NULL DEFAULT 'UYU',
  payment_account TEXT NOT NULL,
  note TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_group_gift_expenses_group_id ON group_gift_expenses(group_id);
CREATE INDEX IF NOT EXISTS idx_group_gift_expenses_birthday_user_id ON group_gift_expenses(birthday_user_id);

-- 6) Debts
CREATE TABLE IF NOT EXISTS group_gift_debts (
  id TEXT PRIMARY KEY,
  expense_id TEXT NOT NULL REFERENCES group_gift_expenses(id) ON DELETE CASCADE,
  owed_by_user_id TEXT NOT NULL REFERENCES users(id),
  owed_to_user_id TEXT NOT NULL REFERENCES users(id),
  amount DOUBLE PRECISION NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING',
  paid_at TIMESTAMP NULL,
  UNIQUE(expense_id, owed_by_user_id)
);
CREATE INDEX IF NOT EXISTS idx_group_gift_debts_expense_id ON group_gift_debts(expense_id);
CREATE INDEX IF NOT EXISTS idx_group_gift_debts_owed_by ON group_gift_debts(owed_by_user_id);

-- 7) Email notification logs (anti-duplicate)
CREATE TABLE IF NOT EXISTS email_notification_logs (
  id TEXT PRIMARY KEY,
  notification_type TEXT NOT NULL,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  group_id TEXT NULL REFERENCES groups(id) ON DELETE CASCADE,
  target_user_id TEXT NULL REFERENCES users(id) ON DELETE CASCADE,
  target_date DATE NOT NULL,
  sent_at TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(notification_type, user_id, group_id, target_user_id, target_date)
);
CREATE INDEX IF NOT EXISTS idx_email_logs_type_date ON email_notification_logs(notification_type, target_date);
CREATE INDEX IF NOT EXISTS idx_email_logs_user ON email_notification_logs(user_id);
