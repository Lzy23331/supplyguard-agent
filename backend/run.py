import uvicorn

from app.database import init_db
from app.services.seed_service import seed_suppliers


if __name__ == "__main__":
    init_db()
    seed_suppliers()
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
