from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import uvicorn

import models, database, auth

# Initialize Database
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="AI Personal Agent API",
    description="Backend API for the AI Personal Agent Workspace",
    version="1.0.0"
)

# CORS configuration for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "AI Personal Agent API is running"}

@app.post("/signup", response_model=auth.UserResponse)
def create_user(user: auth.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/token", response_model=auth.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

from pydantic import BaseModel
from typing import List

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    
    class Config:
        orm_mode = True

import agent

@app.post("/chat", response_model=MessageResponse)
async def send_chat_message(message: MessageCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    # 1. Save user message
    user_msg = models.Message(user_id=current_user.id, role="user", content=message.content)
    db.add(user_msg)
    db.commit()
    
    # 2. Get history
    history = db.query(models.Message).filter(models.Message.user_id == current_user.id).order_by(models.Message.timestamp.asc()).all()
    
    # 3. Call Agent to get reply and extract tasks
    agent_response = await agent.process_chat_message(message.content, history[:-1]) # exclude the user message just added
    
    # 4. Save tasks if any
    for t in agent_response.get("tasks", []):
        new_task = models.Task(user_id=current_user.id, title=t.get("title"), priority=t.get("priority", "Medium"))
        db.add(new_task)
    db.commit()

    # 5. Save and return AI response
    ai_msg = models.Message(user_id=current_user.id, role="ai", content=agent_response.get("reply", "I couldn't process that."))
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)
    
    return ai_msg

@app.get("/history", response_model=List[MessageResponse])
def get_chat_history(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    messages = db.query(models.Message).filter(models.Message.user_id == current_user.id).order_by(models.Message.timestamp.asc()).all()
    return messages

@app.post("/history/clear")
def clear_chat_history(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    db.query(models.Message).filter(models.Message.user_id == current_user.id).delete()
    db.commit()
    return {"message": "History cleared"}

class TaskResponse(BaseModel):
    id: int
    title: str
    priority: str
    status: str

    class Config:
        orm_mode = True

@app.get("/tasks", response_model=List[TaskResponse])
def get_tasks(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    tasks = db.query(models.Task).filter(models.Task.user_id == current_user.id).order_by(models.Task.created_at.desc()).all()
    return tasks

import rag

class RepoIndexRequest(BaseModel):
    repo_url: str

class RepoQueryRequest(BaseModel):
    query: str

@app.post("/repo/index")
async def index_repo(req: RepoIndexRequest, current_user: models.User = Depends(auth.get_current_user)):
    try:
        chunks_indexed = await rag.index_repository(req.repo_url)
        return {"message": f"Successfully indexed repository into {chunks_indexed} chunks."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/repo/query")
async def query_repo(req: RepoQueryRequest, current_user: models.User = Depends(auth.get_current_user)):
    try:
        answer = await rag.query_repository(req.query)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import UploadFile, File
import knowledge

class KnowledgeQueryRequest(BaseModel):
    query: str

@app.post("/knowledge/upload")
async def upload_knowledge(file: UploadFile = File(...), current_user: models.User = Depends(auth.get_current_user)):
    try:
        content = await file.read()
        chunks = await knowledge.process_document(content, file.filename)
        return {"message": f"Successfully indexed {file.filename} into {chunks} chunks."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/knowledge/query")
async def query_knowledge_endpoint(req: KnowledgeQueryRequest, current_user: models.User = Depends(auth.get_current_user)):
    try:
        answer = await knowledge.query_knowledge(req.query)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
