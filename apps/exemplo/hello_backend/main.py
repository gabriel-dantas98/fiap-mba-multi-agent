from fastapi import FastAPI

app = FastAPI(title="Hello Backend")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "hello from backend exemplo"}


@app.get("/ping")
def ping() -> dict[str, bool]:
    return {"ok": True}
