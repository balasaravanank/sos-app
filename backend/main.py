from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load the shared .env file from the project root
load_dotenv(dotenv_path="../.env")

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to SOS App API"}
