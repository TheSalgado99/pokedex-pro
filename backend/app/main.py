from fastapi import FastAPI

app = FastAPI(title="PokÃ©ndeX Pro API")

@app.get("/")
async def read_root():
    # Welcome message in English
    return {"message": "Welcome to the PokÃ©ndeX Pro API"}

# Define more endpoints here (e.g., for getting collections)
# @app.get("/collections/{collection_id}") ...
