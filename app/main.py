import uvicorn
from app.db import create_db_and_tables


def main():
    create_db_and_tables()
    uvicorn.run("app.server:app", host="0.0.0.0", port=8000,reload=True)

if __name__ == '__main__':
    main()
