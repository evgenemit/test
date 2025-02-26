import asyncio

from services.db import db


async def create_tables():
    await db.connect()
    try:
        await db.execute('DROP TABLE IF EXISTS users;')
        await db.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL
            );
            """
        )
        await db.execute('DROP TABLE IF EXISTS clients;')
        await db.execute(
            """
            CREATE TABLE clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users (id),
                first_name TEXT NOT NULL
            );
            """
        )
        await db.execute('DROP TABLE IF EXISTS sellers;')
        await db.execute(
            """
            CREATE TABLE sellers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users (id),
                name TEXT NOT NULL,
                about TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        await db.execute('DROP TABLE IF EXISTS points;')
        await db.execute(
            """
            CREATE TABLE points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users (id),
                name TEXT,
                active INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        await db.execute('DROP TABLE IF EXISTS sessions;')
        await db.execute(
            """
            CREATE TABLE sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users (id) UNIQUE,
                token TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now', '+3 hours'))
            );
            """
        )
        await db.execute('DROP TABLE IF EXISTS orders;')
        await db.execute(
            """
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER REFERENCES clients (id) NOT NULL,
                seller_id INTEGER REFERENCES sellers (id) NOT NULL,
                point_id INTEGER REFERENCES points (id) NOT NULL,
                about TEXT NOT NULL,
                status INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        await db.create_admin()
    finally:
        await db.disconnect()


if __name__ == '__main__':
    asyncio.run(create_tables())
