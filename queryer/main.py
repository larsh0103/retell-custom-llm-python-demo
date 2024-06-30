import os
from astrapy import DataAPIClient
from astrapy.constants import VectorMetric
from astrapy.ids import UUID
from astrapy.exceptions import InsertManyException
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Define the request body structure
class QueryRequest(BaseModel):
    query: str

app = FastAPI()

# LOAD DOTENV FROM FILE .env
from dotenv import load_dotenv

load_dotenv()

@app.post("/query")
def perform_query(request: QueryRequest):
    try:
        client = DataAPIClient(os.environ["ASTRA_TOKEN"])
        database = client.get_database(os.environ["ASTRA_ENDPOINT"])
        caesar = database["caesar2"]
        
        results = caesar.find(
            sort={"$vectorize": request.query},
            limit=5,
            projection={"$vectorize": True},
            include_similarity=True,
        )
    
        documents = [doc for doc in results]
        
        return {"most_similar": documents}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8069)
  

    