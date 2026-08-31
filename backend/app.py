import os
from dataclasses import dataclass

import psycopg2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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


app = FastAPI(title="Production Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/api/message")
def message():
    return {"message": "Hello from backend", "env": os.getenv("APP_ENV", "dev")} 
