from fastapi import FastAPI, HTTPException
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
import time

app = FastAPI()

# Налаштування підключення до бази даних
DB_USER = os.getenv('POSTGRES_DB_USER')
DB_PASSWORD = os.getenv('POSTGRES_DB_PASSWORD')
DB_HOST = 'db'
DB_PORT = 5432
DB_NAME = 'database'
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Модель для валідації даних користувача
class User(BaseModel):
    name: str
    email: str

# Функція для ініціалізації таблиці з повторними спробами
def init_db():
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL UNIQUE
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
            print("Database initialized successfully")
            return
        except Exception as e:
            retries -= 1
            print(f"Failed to initialize database: {str(e)}. Retries left: {retries}")
            if retries == 0:
                raise Exception(f"Failed to initialize database after retries: {str(e)}")
            time.sleep(2)

# Ініціалізація таблиці при запуску
try:
    init_db()
except Exception as e:
    print(e)

# Ендпоінт для перевірки з'єднання з базою
@app.get("/")
def read_root():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return {"status": "Database connection successful", "result": result}
    except Exception as e:
        return {"status": "Database connection failed", "error": str(e)}

# Ендпоінт для створення нового користувача
@app.post("/users/")
def create_user(user: User):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id;",
            (user.name, user.email)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return {"id": user_id, "name": user.name, "email": user.email}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create user: {str(e)}")

# Ендпоінт для отримання списку всіх користувачів
@app.get("/users/")
def get_users():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users;")
        users = cur.fetchall()
        cur.close()
        conn.close()
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")

# Ендпоінт для отримання даних конкретного користувача
@app.get("/users/{user_id}")
def get_user(user_id: int):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user: {str(e)}")

# Ендпоінт для видалення користувача
@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = %s RETURNING id;", (user_id,))
        deleted_id = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        if deleted_id is None:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": f"User {user_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")