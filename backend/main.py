from fastapi import FastAPI
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.monitor.opentelemetry import configure_azure_monitor
import os

configure_azure_monitor()

app = FastAPI()

KEY_VAULT_NAME = "team1-key-vault-prz" 
KV_URI = f"https://{KEY_VAULT_NAME}.vault.azure.net"
SECRET_NAME = "AZURE-SQL-CONNECTION-STRING"

@app.get("/")
def read_root():
    return {"message": "Hello World! Backend dziala i jest gotowy na test Key Vaulta."}

@app.get("/test-kv")
def test_key_vault():
    try:
        credential = DefaultAzureCredential()
        
        client = SecretClient(vault_url=KV_URI, credential=credential)
        
        secret = client.get_secret(SECRET_NAME)
        conn_string = secret.value
        
        preview = conn_string[:30] + "..."
        
        return {
            "status": "SUCCESS ✅", 
            "message": "Połączono z Key Vault i pobrano sekret!",
            "secret_preview": preview
        }
    except Exception as e:
        return {
            "status": "ERROR ❌", 
            "message": "Nie udało się pobrać sekretu.",
            "error_details": str(e)
        }