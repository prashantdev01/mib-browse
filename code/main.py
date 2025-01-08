from fastapi import FastAPI
from code.routes import router as api_router

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI project!"}


app.include_router(api_router)
if __name__ == '__main__':
    uvicorn.run("main:app", host='localhost', port=8000, log_level="error", reload = True)
    print("running")
