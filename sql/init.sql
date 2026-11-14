-- ============================================================================
-- Курсова робота з дисципліни «Веб-технології та веб-дизайн»
-- Варіант 12: Оренда обладнання з календарем доступності
-- Автор: Сливка Максим Олексійович, група АІ-243
-- Схема реляційної бази даних SQLite (init.sql)
-- ============================================================================

PRAGMA foreign_keys = ON;

-- 1. Таблиця користувачів системи (ролі: CLIENT, MANAGER)
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('CLIENT', 'MANAGER')),
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- 2. Таблиця тарифних планів
CREATE TABLE IF NOT EXISTS tariffs (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name TEXT NOT NULL,
    billing_unit TEXT NOT NULL CHECK (billing_unit IN ('HOUR', 'DAY')),
    rate_minor INTEGER NOT NULL CHECK (rate_minor >= 0),
    deposit_minor INTEGER NOT NULL CHECK (deposit_minor >= 0),
    late_fee_per_hour_minor INTEGER NOT NULL CHECK (late_fee_per_hour_minor >= 0),
    min_units INTEGER NOT NULL CHECK (min_units >= 1),
    max_units INTEGER NOT NULL CHECK (max_units >= min_units)
);

-- 3. Таблиця типів обладнання (товарних позицій каталогу)
CREATE TABLE IF NOT EXISTS equipment_types (
    id TEXT PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE COLLATE NOCASE,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    brand_model TEXT NOT NULL,
    description TEXT NOT NULL,
    specs_json TEXT NOT NULL,
    tariff_id TEXT NOT NULL,
    maintenance_buffer_hours INTEGER NOT NULL CHECK (maintenance_buffer_hours >= 0 AND maintenance_buffer_hours <= 72),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    image_tag TEXT NOT NULL,
    FOREIGN KEY (tariff_id) REFERENCES tariffs(id) ON DELETE RESTRICT
);

-- 4. Таблиця фізичних екземплярів обладнання
CREATE TABLE IF NOT EXISTS equipment_units (
    id TEXT PRIMARY KEY,
    equipment_type_id TEXT NOT NULL,
    inventory_code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    serial_number TEXT NOT NULL UNIQUE COLLATE NOCASE,
    condition_status TEXT NOT NULL CHECK (condition_status IN ('AVAILABLE', 'IN_MAINTENANCE', 'RETIRED')),
    warehouse_location TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (equipment_type_id) REFERENCES equipment_types(id) ON DELETE RESTRICT
);

-- 5. Таблиця бронювань (заявок на оренду фізичного екземпляра)
CREATE TABLE IF NOT EXISTS bookings (
    id TEXT PRIMARY KEY,
    booking_number TEXT NOT NULL UNIQUE COLLATE NOCASE,
    unit_id TEXT NOT NULL,
    client_user_id TEXT NOT NULL,
    tariff_id TEXT NOT NULL,
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL,
    buffer_ends_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'CONFIRMED', 'ISSUED', 'RETURNED', 'CANCELLED', 'REJECTED')),
    purpose TEXT NOT NULL,
    rejection_reason TEXT,
    billed_units INTEGER NOT NULL CHECK (billed_units >= 1),
    unit_rate_minor INTEGER NOT NULL CHECK (unit_rate_minor >= 0),
    base_price_minor INTEGER NOT NULL CHECK (base_price_minor >= 0),
    deposit_minor INTEGER NOT NULL CHECK (deposit_minor >= 0),
    late_hours INTEGER NOT NULL DEFAULT 0 CHECK (late_hours >= 0),
    late_fee_minor INTEGER NOT NULL DEFAULT 0 CHECK (late_fee_minor >= 0),
    total_price_minor INTEGER NOT NULL CHECK (total_price_minor >= 0),
    actual_issued_at TEXT,
    actual_returned_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    CHECK (ends_at > starts_at),
    CHECK (buffer_ends_at >= ends_at),
    FOREIGN KEY (unit_id) REFERENCES equipment_units(id) ON DELETE RESTRICT,
    FOREIGN KEY (client_user_id) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (tariff_id) REFERENCES tariffs(id) ON DELETE RESTRICT
);

-- 6. Таблиця подій видачі, повернення та зміни станів бронювання (історія)
CREATE TABLE IF NOT EXISTS rental_events (
    id TEXT PRIMARY KEY,
    booking_id TEXT NOT NULL,
    actor_user_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('CREATED', 'CONFIRMED', 'REJECTED', 'CANCELLED', 'EXTENDED', 'ISSUED', 'RETURNED_ON_TIME', 'RETURNED_LATE')),
    old_status TEXT,
    new_status TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    penalty_added_minor INTEGER NOT NULL DEFAULT 0 CHECK (penalty_added_minor >= 0),
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE RESTRICT
);

-- 7. Таблиця черги очікування (погоджене ускладнення Варіанта 12)
CREATE TABLE IF NOT EXISTS waitlist_entries (
    id TEXT PRIMARY KEY,
    equipment_type_id TEXT NOT NULL,
    preferred_unit_id TEXT,
    client_user_id TEXT NOT NULL,
    desired_starts_at TEXT NOT NULL,
    desired_ends_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('WAITING', 'NOTIFIED', 'CONVERTED', 'CANCELLED')),
    contact_note TEXT NOT NULL,
    notified_at TEXT,
    created_at TEXT NOT NULL,
    CHECK (desired_ends_at > desired_starts_at),
    FOREIGN KEY (equipment_type_id) REFERENCES equipment_types(id) ON DELETE RESTRICT,
    FOREIGN KEY (preferred_unit_id) REFERENCES equipment_units(id) ON DELETE SET NULL,
    FOREIGN KEY (client_user_id) REFERENCES users(id) ON DELETE RESTRICT
);

-- Індекси для пришвидшення перевірки перетину інтервалів, пошуку в каталозі та черги
CREATE INDEX IF NOT EXISTS idx_equipment_types_category ON equipment_types(category, active);
CREATE INDEX IF NOT EXISTS idx_equipment_units_type ON equipment_units(equipment_type_id, condition_status);
CREATE INDEX IF NOT EXISTS idx_bookings_unit_interval ON bookings(unit_id, status, starts_at, buffer_ends_at);
CREATE INDEX IF NOT EXISTS idx_bookings_client ON bookings(client_user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status, starts_at);
CREATE INDEX IF NOT EXISTS idx_rental_events_booking ON rental_events(booking_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_waitlist_type_status ON waitlist_entries(equipment_type_id, status, created_at);
