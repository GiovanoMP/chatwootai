from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import uvicorn
import motor.motor_asyncio
import os

app = FastAPI()

# Get MongoDB URI from environment variable or use default
mongodb_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/config_service")
api_key = os.environ.get("API_KEY", "development-api-key")

# Connect to MongoDB
client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
db = client.get_default_database()

class YAMLContent(BaseModel):
    yaml_content: str

async def get_api_key(x_api_key: str = Header(None)):
    if x_api_key != api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

@app.post("/company-services/{account_id}/metadata")
async def receive_metadata(account_id: str, content: YAMLContent, api_key: str = Depends(get_api_key)):
    # Store the YAML content in MongoDB
    await db[account_id].update_one(
        {"_id": "metadata"},
        {"$set": {"yaml_content": content.yaml_content}},
        upsert=True
    )
    print(f"Received data for account {account_id}")
    return {"success": True, "message": "Data received successfully"}

@app.get("/")
async def root():
    return {"message": "MongoDB Webhook API is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
