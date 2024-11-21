from fastapi import FastAPI
from main import app as main_app

app = FastAPI()

# 将主应用的所有路由复制到新的应用
app.mount("/", main_app) 