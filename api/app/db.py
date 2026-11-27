import os

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

pool = ConnectionPool(
    os.environ["DATABASE_URL"],
    min_size=1,
    max_size=10,
    timeout=3,
    kwargs={"row_factory": dict_row, "connect_timeout": 3},
    check=ConnectionPool.check_connection,  # replace dead connections
    open=False,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS menu_items (
    id        INTEGER PRIMARY KEY,
    name      TEXT NOT NULL,
    price     NUMERIC(10,2) NOT NULL,
    available BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TABLE IF NOT EXISTS orders (
    id             SERIAL PRIMARY KEY,
    customer_name  TEXT NOT NULL,
    total          NUMERIC(10,2) NOT NULL,
    status         TEXT NOT NULL DEFAULT 'pending'
                   CHECK (status IN ('pending', 'preparing', 'ready')),
    receipt_status TEXT NOT NULL DEFAULT 'pending'
                   CHECK (receipt_status IN ('pending', 'generated')),
    receipt_url    TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS order_items (
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    item_id  INTEGER NOT NULL REFERENCES menu_items(id),
    quantity INTEGER NOT NULL CHECK (quantity >= 1),
    PRIMARY KEY (order_id, position)
);
INSERT INTO menu_items (id, name, price, available) VALUES
    (1, 'Americano', 45.00, TRUE),
    (2, 'Latte', 60.00, TRUE),
    (3, 'Croissant', 40.00, FALSE),
    (4, 'Capuchino', 55.00, TRUE),
    (5, 'Muffin', 35.00, TRUE)
ON CONFLICT (id) DO NOTHING;
"""


def init_db():
    """Create tables and sample data. Safe to run from several containers."""
    with pool.connection() as conn:
        # The lock stops two API replicas from creating tables at the same time.
        conn.execute("SELECT pg_advisory_xact_lock(4004)")
        conn.execute(SCHEMA)
