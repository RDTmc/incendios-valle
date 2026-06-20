"""
One-time script to fix user roles in SQLite.
Run on EC2:  docker exec incendios-api python scripts/fix_admin_role.py
Or via deploy: runs automatically in refresh_api.sh
"""
import sqlite3
import os
import sys

DB_PATH = os.environ.get('DB_PATH', '/data/incendios.db')

def fix_admin_role(email: str = "rodrigomunozcatalan@gmail.com"):
    conn = sqlite3.connect(DB_PATH, timeout=5)
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, email, rol FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    if user:
        cursor.execute("UPDATE users SET rol = 'ADMIN' WHERE email = ?", (email,))
        conn.commit()
        print(f"✅ Updated {email}: {user[2]} → ADMIN")
    else:
        print(f"⚠️  User {email} not found in SQLite")

    cursor.execute("SELECT user_id, email, rol FROM users")
    print("\n📋 Current users in SQLite:")
    for row in cursor.fetchall():
        print(f"  {row[0]:<40} {row[1]:<35} {row[2]}")
    conn.close()

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "rodrigomunozcatalan@gmail.com"
    fix_admin_role(email)
