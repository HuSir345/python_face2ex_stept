from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from main import app as main_app

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 将主应用的所有路由复制到新的应用
app.mount("/", main_app) 