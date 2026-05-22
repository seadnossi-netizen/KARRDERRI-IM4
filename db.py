
import sqlite3

DB = "store.db"

def con():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def q1(sql, args=()):
    db = con(); r = db.execute(sql, args).fetchone(); db.close()
    return dict(r) if r else None

def qa(sql, args=()):
    db = con(); r = db.execute(sql, args).fetchall(); db.close()
    return [dict(x) for x in r]

def run(sql, args=()):
    db = con(); db.execute(sql, args); db.commit(); db.close()

def init_db():
    db = con()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            login      TEXT PRIMARY KEY,
            password   TEXT NOT NULL,
            is_owner   INTEGER DEFAULT 0,
            balance    REAL DEFAULT 0.0,
            tg_id      INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS categories (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS positions (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            cat_id  INTEGER NOT NULL,
            name    TEXT NOT NULL,
            status  TEXT DEFAULT '',
            FOREIGN KEY (cat_id) REFERENCES categories(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS key_types (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            pos_id     INTEGER NOT NULL,
            name       TEXT NOT NULL,
            price      REAL DEFAULT 0.0,
            init_price REAL DEFAULT 0.0,
            FOREIGN KEY (pos_id) REFERENCES positions(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS keys (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            kt_id   INTEGER NOT NULL,
            value   TEXT NOT NULL,
            is_sold INTEGER DEFAULT 0,
            sold_at TEXT,
            FOREIGN KEY (kt_id) REFERENCES key_types(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS files (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            pos_id  INTEGER NOT NULL,
            file_id TEXT NOT NULL,
            fname   TEXT DEFAULT '',
            is_sold INTEGER DEFAULT 0,
            FOREIGN KEY (pos_id) REFERENCES positions(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS purchases (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            login      TEXT NOT NULL,
            cat_name   TEXT DEFAULT '',
            pos_name   TEXT DEFAULT '',
            kt_name    TEXT DEFAULT '',
            key_val    TEXT,
            file_id    TEXT,
            price      REAL DEFAULT 0.0,
            qty        INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS topups (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            login      TEXT NOT NULL,
            amount     REAL DEFAULT 0.0,
            note       TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS resets (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            key_val    TEXT NOT NULL,
            login      TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    db.commit(); db.close()
    from config import OWNER_LOGIN, OWNER_PASSWORD
    if not get_account(OWNER_LOGIN):
        run("INSERT INTO accounts (login,password,is_owner) VALUES (?,?,1)",
            (OWNER_LOGIN, OWNER_PASSWORD))

def get_account(login):
    return q1("SELECT * FROM accounts WHERE login=?", (login,))

def get_account_by_creds(login, password):
    return q1("SELECT * FROM accounts WHERE login=? AND password=?", (login, password))

def get_all_accounts():
    return qa("SELECT * FROM accounts ORDER BY created_at DESC")

def create_account(login, password):
    try: run("INSERT INTO accounts (login,password) VALUES (?,?)", (login, password)); return True
    except: return False

def delete_account(login):
    run("DELETE FROM accounts WHERE login=?", (login,))

def add_balance(login, amount):
    run("UPDATE accounts SET balance=balance+? WHERE login=?", (amount, login))

def reset_balance(login):
    run("UPDATE accounts SET balance=0 WHERE login=?", (login,))

def set_tg_id(login, tg_id):
    run("UPDATE accounts SET tg_id=? WHERE login=?", (tg_id, login))

def add_topup(login, amount, note=""):
    run("INSERT INTO topups (login,amount,note) VALUES (?,?,?)", (login, amount, note))

def get_topups(login):
    return qa("SELECT * FROM topups WHERE login=? ORDER BY created_at DESC", (login,))

def get_categories():
    return qa("SELECT * FROM categories ORDER BY id")

def get_category(cat_id):
    return q1("SELECT * FROM categories WHERE id=?", (cat_id,))

def create_category(name):
    try: run("INSERT INTO categories (name) VALUES (?)", (name,)); return True
    except: return False

def delete_category(cat_id):
    run("DELETE FROM categories WHERE id=?", (cat_id,))

def get_positions(cat_id):
    return qa("SELECT * FROM positions WHERE cat_id=? ORDER BY id", (cat_id,))

def get_position(pos_id):
    return q1("SELECT * FROM positions WHERE id=?", (pos_id,))

def create_position(cat_id, name):
    run("INSERT INTO positions (cat_id,name) VALUES (?,?)", (cat_id, name))

def delete_position(pos_id):
    run("DELETE FROM positions WHERE id=?", (pos_id,))

def set_position_status(pos_id, status):
    run("UPDATE positions SET status=? WHERE id=?", (status, pos_id))

def get_key_types(pos_id):
    return qa("SELECT * FROM key_types WHERE pos_id=? ORDER BY id", (pos_id,))

def get_key_type(kt_id):
    return q1("SELECT * FROM key_types WHERE id=?", (kt_id,))

def create_key_type(pos_id, name, price):
    run("INSERT INTO key_types (pos_id,name,price) VALUES (?,?,?)", (pos_id, name, price))
    r = q1("SELECT id FROM key_types WHERE pos_id=? ORDER BY id DESC LIMIT 1", (pos_id,))
    return r['id'] if r else None

def update_key_price(kt_id, price):
    run("UPDATE key_types SET price=? WHERE id=?", (price, kt_id))

def update_key_init_price(kt_id, p):
    run("UPDATE key_types SET init_price=? WHERE id=?", (p, kt_id))

def delete_key_type(kt_id):
    run("DELETE FROM key_types WHERE id=?", (kt_id,))

def count_stock(kt_id):
    r = q1("SELECT COUNT(*) as n FROM keys WHERE kt_id=? AND is_sold=0", (kt_id,))
    return r['n'] if r else 0

def add_key(kt_id, value):
    run("INSERT INTO keys (kt_id,value) VALUES (?,?)", (kt_id, value))

def pop_key(kt_id):
    db = con()
    try:
        r = db.execute("SELECT * FROM keys WHERE kt_id=? AND is_sold=0 LIMIT 1", (kt_id,)).fetchone()
        if r:
            db.execute("UPDATE keys SET is_sold=1, sold_at=datetime('now') WHERE id=?", (r['id'],))
            db.commit()
        return dict(r) if r else None
    finally:
        db.close()

def clear_keys(kt_id):
    run("DELETE FROM keys WHERE kt_id=? AND is_sold=0", (kt_id,))

def add_file(pos_id, file_id, fname=""):
    run("INSERT INTO files (pos_id,file_id,fname) VALUES (?,?,?)", (pos_id, file_id, fname))

def count_files(pos_id):
    r = q1("SELECT COUNT(*) as n FROM files WHERE pos_id=? AND is_sold=0", (pos_id,))
    return r['n'] if r else 0

def get_all_files(pos_id):
    return qa("SELECT * FROM files WHERE pos_id=? AND is_sold=0", (pos_id,))

def clear_files(pos_id):
    run("DELETE FROM files WHERE pos_id=? AND is_sold=0", (pos_id,))

def add_purchase(login, cat_name, pos_name, kt_name, key_val, file_id, price, qty=1):
    run("INSERT INTO purchases (login,cat_name,pos_name,kt_name,key_val,file_id,price,qty) VALUES (?,?,?,?,?,?,?,?)",
        (login, cat_name, pos_name, kt_name, key_val, file_id, price, qty))

def get_purchases(login):
    return qa("SELECT * FROM purchases WHERE login=? ORDER BY created_at DESC", (login,))

def get_all_purchases(limit=50):
    return qa("SELECT * FROM purchases ORDER BY created_at DESC LIMIT ?", (limit,))

def total_revenue():
    r = q1("SELECT SUM(price*qty) as t FROM purchases")
    return r['t'] or 0.0

def revenue_since(since_dt):
    r = q1("SELECT SUM(price*qty) as t FROM purchases WHERE created_at >= ?", (since_dt,))
    return r['t'] or 0.0

def top_buyers(limit=10):
    return qa("SELECT login, SUM(price*qty) as spent, COUNT(*) as orders FROM purchases GROUP BY login ORDER BY spent DESC LIMIT ?", (limit,))

def total_users():
    r = q1("SELECT COUNT(*) as n FROM accounts WHERE is_owner=0")
    return r['n'] if r else 0

def get_full_stock():
    result = []
    for cat in get_categories():
        for pos in get_positions(cat['id']):
            kts = get_key_types(pos['id'])
            result.append({
                'cat': cat['name'], 'cat_id': cat['id'],
                'pos': pos['name'], 'pos_id': pos['id'],
                'status': pos['status'],
                'key_types': [{'name': kt['name'], 'count': count_stock(kt['id'])} for kt in kts],
                'files': count_files(pos['id']),
            })
    return result

def count_resets(key_val):
    r = q1("SELECT COUNT(*) as n FROM resets WHERE key_val=?", (key_val,))
    return r['n'] if r else 0

def last_reset_time(key_val):
    r = q1("SELECT created_at FROM resets WHERE key_val=? ORDER BY created_at DESC LIMIT 1", (key_val,))
    return r['created_at'] if r else None

def add_reset(key_val, login):
    run("INSERT INTO resets (key_val, login) VALUES (?,?)", (key_val, login))
