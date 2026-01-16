import urllib.parse
import logging
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

from azure.monitor.opentelemetry import configure_azure_monitor
try:
    configure_azure_monitor()
except Exception:
    pass

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from sqlalchemy import create_engine, Column, Integer, String, Boolean, text
from sqlalchemy.orm import sessionmaker, declarative_base

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://team1-frontend-g7e3d9duaka0d6fs.polandcentral-01.azurewebsites.net/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

KEY_VAULT_NAME = "team1-key-vault-prz" 
KV_URI = f"https://{KEY_VAULT_NAME}.vault.azure.net"
SECRET_NAME = "AZURE-SQL-CONNECTION-STRING"

Base = declarative_base()

class TodoItem(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100))
    completed = Column(Boolean, default=False)

class TodoCreate(BaseModel):
    title: str

class TodoResponse(BaseModel):
    id: int
    title: str
    completed: bool
    class Config:
        from_attributes = True

db_session = None
last_error = "Nieznany błąd startowy"

def get_connection_string():
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=KV_URI, credential=credential)
    secret = client.get_secret(SECRET_NAME)
    raw_conn_str = secret.value
    
    if "Driver=" not in raw_conn_str:
        raw_conn_str = f"Driver={{ODBC Driver 18 for SQL Server}};{raw_conn_str}"
    
    if "TrustServerCertificate=" not in raw_conn_str:
        raw_conn_str += ";TrustServerCertificate=yes"
        
    params = urllib.parse.quote_plus(raw_conn_str)
    return f"mssql+pyodbc:///?odbc_connect={params}"

def try_connect():
    global db_session, last_error
    try:
        conn_str = get_connection_string()
        engine = create_engine(conn_str)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db_session = SessionLocal()
        logger.info("✅ SUKCES: Połączono z bazą!")
        return True
    except Exception as e:
        last_error = str(e)
        logger.error(f"❌ BŁĄD BAZY: {e}")
        return False

try_connect()


@app.get("/")
def read_root():
    return {"status": "App running", "db_connected": db_session is not None}

@app.post("/todos", response_model=TodoResponse)
def create_todo(todo: TodoCreate):
    if not db_session:
        if not try_connect():
            raise HTTPException(status_code=500, detail=f"BŁĄD BAZY DANYCH: {last_error}")
    
    try:
        db_item = TodoItem(title=todo.title)
        db_session.add(db_item)
        db_session.commit()
        db_session.refresh(db_item)
        return db_item
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"BŁĄD ZAPISU: {str(e)}")

@app.get("/todos", response_model=List[TodoResponse])
def get_todos():
    if not db_session:
         if not try_connect():
            raise HTTPException(status_code=500, detail=f"BŁĄD BAZY DANYCH: {last_error}")
    return db_session.query(TodoItem).all()