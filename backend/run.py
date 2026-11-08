"""启动脚本：python run.py"""
import uvicorn

from app import config

if __name__ == "__main__":
    print(f"服务启动：http://127.0.0.1:{config.PORT}")
    uvicorn.run("app.main:app", host="127.0.0.1", port=config.PORT, reload=False)
