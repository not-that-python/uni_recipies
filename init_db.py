"""One-time setup: creates tables and seed data in the Postgres database
pointed to by DATABASE_URL. Run once after provisioning the database:

    DATABASE_URL=<external database url> python init_db.py
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def init_db():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    with open('schema.sql', 'r') as f:
        cur.execute(f.read())
    conn.commit()
    cur.close()
    conn.close()
    print('Database initialized.')

if __name__ == '__main__':
    init_db()
