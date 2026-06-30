PRAGMA foreign_keys = ON;

-- =====================
-- Shared Accounts
-- =====================
CREATE TABLE IF NOT EXISTS shared_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- =====================
-- Users
-- =====================
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT UNIQUE,
    is_admin INTEGER DEFAULT 0 CHECK (is_admin IN (0,1)),
    shared_account_id INTEGER,
    login_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    last_login TEXT,
    FOREIGN KEY (shared_account_id)
        REFERENCES shared_accounts(id)
        ON DELETE SET NULL
);

-- =====================
-- Expense Categories
-- =====================
CREATE TABLE IF NOT EXISTS expense_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    color TEXT NOT NULL,
    created_by INTEGER,  -- NULL = ברירת מחדל מערכת
    UNIQUE(name, created_by),
    FOREIGN KEY (created_by)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

-- =====================
-- Default Expense Categories (System)
-- =====================
INSERT OR IGNORE INTO expense_types (name, color, created_by) VALUES
('מזון', '#FF6384', NULL),
('תחבורה', '#36A2EB', NULL),
('דיור', '#FFCE56', NULL),
('בידור', '#4BC0C0', NULL),
('אחר', '#9966FF', NULL);

-- =====================
-- Income Categories
-- =====================
CREATE TABLE IF NOT EXISTS income_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    color TEXT NOT NULL,
    created_by INTEGER,
    UNIQUE(name, created_by),
    FOREIGN KEY (created_by)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

-- =====================
-- Default Income Categories (System)
-- =====================
INSERT OR IGNORE INTO income_types (name, color, created_by) VALUES
('משכורת', '#4CAF50', NULL),
('עסק', '#2196F3', NULL),
('השקעות', '#9C27B0', NULL),
('מתנה', '#FF9800', NULL),
('קצבה', '#795548', NULL),
('אחר', '#9966FF', NULL);

-- =====================
-- Expenses
-- =====================
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    shared_account_id INTEGER,
    created_by INTEGER,
    amount REAL NOT NULL CHECK (amount > 0),
    description TEXT,
    date TEXT NOT NULL,
    type_id INTEGER NOT NULL,
    expense_nature TEXT NOT NULL DEFAULT 'משתנה'
        CHECK (expense_nature IN ('קבועה','משתנה')),
    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,
    FOREIGN KEY (created_by)
        REFERENCES users(user_id)
        ON DELETE SET NULL,
    FOREIGN KEY (shared_account_id)
        REFERENCES shared_accounts(id)
        ON DELETE CASCADE,
    FOREIGN KEY (type_id)
        REFERENCES expense_types(id)
);

-- =====================
-- Incomes
-- =====================
CREATE TABLE IF NOT EXISTS incomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    shared_account_id INTEGER,
    created_by INTEGER,
    amount REAL NOT NULL CHECK (amount > 0),
    description TEXT,
    date TEXT NOT NULL,
    type_id INTEGER NOT NULL,
    income_nature TEXT NOT NULL DEFAULT 'משתנה'
        CHECK (income_nature IN ('קבועה','משתנה')),
    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,
    FOREIGN KEY (created_by)
        REFERENCES users(user_id)
        ON DELETE SET NULL,
    FOREIGN KEY (shared_account_id)
        REFERENCES shared_accounts(id)
        ON DELETE CASCADE,
    FOREIGN KEY (type_id)
        REFERENCES income_types(id)
);

DROP VIEW IF EXISTS combined_transactions_view;

CREATE VIEW combined_transactions_view AS

SELECT
    e.id,
    e.user_id,
    e.shared_account_id,
    e.created_by,
    e.amount,
    e.description,
    e.date,
    et.name AS category,
    et.color AS color,
    e.expense_nature AS nature,
    'expense' AS transaction_type
FROM expenses e
JOIN expense_types et ON e.type_id = et.id

UNION ALL

SELECT
    i.id,
    i.user_id,
    i.shared_account_id,
    i.created_by,
    i.amount,
    i.description,
    i.date,
    it.name AS category,
    it.color AS color,
    i.income_nature AS nature,
    'income' AS transaction_type
FROM incomes i
JOIN income_types it ON i.type_id = it.id;

CREATE INDEX IF NOT EXISTS idx_expenses_user ON expenses(user_id);
CREATE INDEX IF NOT EXISTS idx_expenses_shared ON expenses(shared_account_id);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);
CREATE INDEX IF NOT EXISTS idx_expenses_type ON expenses(type_id);

CREATE INDEX IF NOT EXISTS idx_incomes_user ON incomes(user_id);
CREATE INDEX IF NOT EXISTS idx_incomes_shared ON incomes(shared_account_id);
CREATE INDEX IF NOT EXISTS idx_incomes_date ON incomes(date);
CREATE INDEX IF NOT EXISTS idx_incomes_type ON incomes(type_id);

CREATE INDEX IF NOT EXISTS idx_users_shared ON users(shared_account_id);