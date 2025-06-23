from fastapi import APIRouter, HTTPException, Depends, Request
from .models import UserRegister, UserLogin, UserInDB
from .utils import hash_password, verify_password, create_access_token, decode_access_token, generate_session_id
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from datetime import timedelta
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Dependency to get MongoDB users collection
def get_users_collection(request: Request) -> Collection:
    return request.app.mongodb["users"]

@router.post("/register")
def register(user: UserRegister, request: Request, users: Collection = Depends(get_users_collection)):
    if users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = hash_password(user.password)
    session_id = generate_session_id()
    user_doc = {"email": user.email, "hashed_password": hashed, "session_id": session_id}
    try:
        users.insert_one(user_doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Email already registered")
    return {"msg": "User registered successfully"}

@router.post("/login")
def login(user: UserLogin, request: Request, users: Collection = Depends(get_users_collection)):
    user_doc = users.find_one({"email": user.email})
    if not user_doc or not verify_password(user.password, user_doc["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    session_id = generate_session_id()
    users.update_one({"email": user.email}, {"$set": {"session_id": session_id}})
    access_token = create_access_token(
        data={"sub": user.email, "session_id": session_id},
        expires_delta=timedelta(minutes=60)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/protected")
def protected_route(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"msg": "You are authenticated!", "user": payload["sub"], "session_id": payload["session_id"]} 