from fastapi import FastAPI


app = FastAPI(title="Babysitting API gateway")

@app.get("/")
async def root():
    return {"message": "API Gateway"}