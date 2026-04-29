from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from database import get_conn
from auth_utils import hash_password, verify_password, create_token
from dependencies import get_current_user

router = APIRouter()

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/register", status_code=201)
def register(body: RegisterRequest):
    conn = get_conn()
    existing = conn.execute(
        "SELECT id FROM users WHERE username = ? OR email = ?",
        (body.username, body.email)
    ).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Username or email already taken.")
    hashed = hash_password(body.password)
    conn.execute(
        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
        (body.username, body.email, hashed)
    )
    conn.commit()
    conn.close()
    return {"message": f"User '{body.username}' registered successfully!"}

@router.post("/login")
def login(body: LoginRequest):
    conn = get_conn()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (body.username,)
    ).fetchone()
    conn.close()
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password.")
    token = create_token(user["id"], user["username"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user["id"], "username": user["username"], "email": user["email"]}
    }

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user