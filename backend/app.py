import os
from dataclasses import dataclass

import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: str
    name: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> "DatabaseSettings":
        return cls(
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432"),
            name=os.getenv("DB_NAME", "appdb"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
        )


def get_db_connection():
    settings = DatabaseSettings.from_env()
    return psycopg2.connect(
        host=settings.host,
        port=settings.port,
        database=settings.name,
        user=settings.user,
        password=settings.password,
    )


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    cur.close()
    conn.close()


class ItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    completed: bool = False


class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    completed: bool | None = None


app = FastAPI(title="Local CRUD App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/api/health")
def health():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        return {"status": "ok", "database": "connected", "env": os.getenv("APP_ENV", "dev")}
    except Exception as exc:
        return {
            "status": "error",
            "database": "disconnected",
            "env": os.getenv("APP_ENV", "dev"),
            "error": str(exc),
        }


@app.get("/api/items")
def list_items():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title, description, completed, created_at FROM items ORDER BY id ASC"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "completed": row[3],
            "created_at": row[4].isoformat() if row[4] else None,
        }
        for row in rows
    ]


@app.get("/api/items/{item_id}")
def get_item(item_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title, description, completed, created_at FROM items WHERE id = %s",
        (item_id,),
    )
    row = cur.fetchone()
    cur.close(); conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Item not found")

    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "completed": row[3],
        "created_at": row[4].isoformat() if row[4] else None,
    }


@app.post("/api/items", status_code=201)
def create_item(item: ItemCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO items (title, description, completed) VALUES (%s, %s, %s) RETURNING id, title, description, completed, created_at",
        (item.title, item.description, item.completed),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close(); conn.close()

    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "completed": row[3],
        "created_at": row[4].isoformat() if row[4] else None,
    }


@app.put("/api/items/{item_id}")
def update_item(item_id: int, item: ItemUpdate):
    conn = get_db_connection()
    cur = conn.cursor()

    current = cur.execute(
        "SELECT id FROM items WHERE id = %s",
        (item_id,),
    )
    if current.fetchone() is None:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Item not found")

    updates = []
    values = []

    if item.title is not None:
        updates.append("title = %s")
        values.append(item.title)
    if item.description is not None:
        updates.append("description = %s")
        values.append(item.description)
    if item.completed is not None:
        updates.append("completed = %s")
        values.append(item.completed)

    if not updates:
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")

    values.append(item_id)
    query = f"UPDATE items SET {', '.join(updates)} WHERE id = %s RETURNING id, title, description, completed, created_at"
    cur.execute(query, tuple(values))
    row = cur.fetchone()
    conn.commit()
    cur.close(); conn.close()

    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "completed": row[3],
        "created_at": row[4].isoformat() if row[4] else None,
    }


@app.delete("/api/items/{item_id}")
def delete_item(item_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM items WHERE id = %s RETURNING id", (item_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close(); conn.close()

    if deleted is None:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"message": "Item deleted", "id": item_id}


@app.get("/api/message")
def message():
    return {"message": "Hello from backend", "env": os.getenv("APP_ENV", "dev")} 
