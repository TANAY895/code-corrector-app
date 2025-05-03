from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./history.db")

# Database setup
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class CorrectionHistory(Base):
    __tablename__ = "corrections"
    id = Column(Integer, primary_key=True, index=True)
    input_code = Column(String)
    corrected_code = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:5173"] for stricter control
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request body model
class CodeRequest(BaseModel):
    code: str

# Routes
@app.get("/")
def root():
    return {"message": "Backend is running ✅"}

@app.post("/correct")
def correct_code(request: CodeRequest):
    try:
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a code fixer."},
                {"role": "user", "content": f"Fix this code:\n{request.code}"}
            ]
        )
        corrected_code = response.choices[0].message.content.strip()

        # Save to DB
        db = SessionLocal()
        history = CorrectionHistory(
            input_code=request.code,
            corrected_code=corrected_code
        )
        db.add(history)
        db.commit()
        db.refresh(history)

        return {"corrected_code": corrected_code}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
def get_history():
    db = SessionLocal()
    history_items = db.query(CorrectionHistory).order_by(CorrectionHistory.timestamp.desc()).all()
    return [
        {
            "id": item.id,
            "input_code": item.input_code,
            "corrected_code": item.corrected_code,
            "timestamp": item.timestamp
        }
        for item in history_items
    ]
