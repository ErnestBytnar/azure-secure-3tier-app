import urllib.parse
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from azure.monitor.opentelemetry import configure_azure_monitor

try:
    configure_azure_monitor()
except Exception:
    pass # Ignorujemy błędy lokalnie

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

app = FastAPI()

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

def get_db_connection_string():
    """Pobiera hasło z Key Vault i tworzy Connection String do SQL"""
    print("Pobieranie sekretu z Key Vault...")
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

def init_db():
    """Inicjalizuje połączenie i tworzy tabelę jeśli nie istnieje"""
    global db_session
    try:
        conn_str = get_db_connection_string()
        engine = create_engine(conn_str)
        
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db_session = SessionLocal()
        print("Connected to DB and created a table!")
    except Exception as e:
        print(f" DB error: {e}")

init_db()


@app.get("/")
def read_root():
    return {"message": "API działa! Baza danych podpięta."}

@app.get("/todos", response_model=List[TodoResponse])
def get_todos():
    if not db_session:
        raise HTTPException(status_code=500, detail="Brak połączenia z bazą")
    todos = db_session.query(TodoItem).all()
    return todos

@app.post("/todos", response_model=TodoResponse)
def create_todo(todo: TodoCreate):
    if not db_session:
        raise HTTPException(status_code=500, detail="Brak połączenia z bazą")
    
    db_item = TodoItem(title=todo.title)
    db_session.add(db_item)
    db_session.commit()
    db_session.refresh(db_item)
    return db_item