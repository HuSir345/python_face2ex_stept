from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
import requests
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import base64
from pathlib import Path
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 获取当前文件的目录
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建上传目录
UPLOAD_DIR = BASE_DIR / "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# 静态文件服务
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# 配置模板
templates = Jinja2Templates(directory="templates")

# Coze API配置
COZE_API_URL = "https://api.coze.cn/v1/workflow/run"
COZE_API_KEY = "pat_0OjgQdYOMeEPHi3wUdDvZCLjaLOgbS87dDYMVdoxFQO9iYWuaamgn5pqrHKhlig2"
WORKFLOW_ID = "7435930213924306978"

# ImgBB API配置
IMGBB_API_KEY = "c29b0e93329c7d478fc186bf56deff3a"  # 已更新为你提供的 API key
IMGBB_API_URL = "https://api.imgbb.com/1/upload"

# 添加根路由
@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_images(pic1: UploadFile = File(...), pic2: UploadFile = File(...)):
    try:
        logger.info("开始处理图片上传请求")
        
        # 直接读取图片内容并上传到ImgBB
        pic1_content = await pic1.read()
        pic2_content = await pic2.read()
        
        # 上传图片1到ImgBB
        logger.info("开始上传图片1到ImgBB...")
        pic1_base64 = base64.b64encode(pic1_content).decode('utf-8')
        imgbb_payload1 = {
            'key': IMGBB_API_KEY,
            'image': pic1_base64,
            'name': f'pic1_{datetime.now().strftime("%Y%m%d%H%M%S")}'
        }
        imgbb_response1 = requests.post(IMGBB_API_URL, data=imgbb_payload1)
        if imgbb_response1.status_code != 200:
            raise Exception(f"ImgBB上传图片1失败: {imgbb_response1.text}")
        pic1_url = imgbb_response1.json()['data']['url']
        logger.info(f"图片1上传成功，URL: {pic1_url}")
        
        # 上传图片2到ImgBB
        logger.info("开始上传图片2到ImgBB...")
        pic2_base64 = base64.b64encode(pic2_content).decode('utf-8')
        imgbb_payload2 = {
            'key': IMGBB_API_KEY,
            'image': pic2_base64,
            'name': f'pic2_{datetime.now().strftime("%Y%m%d%H%M%S")}'
        }
        imgbb_response2 = requests.post(IMGBB_API_URL, data=imgbb_payload2)
        if imgbb_response2.status_code != 200:
            raise Exception(f"ImgBB上传图片2失败: {imgbb_response2.text}")
        pic2_url = imgbb_response2.json()['data']['url']
        logger.info(f"图片2上传成功，URL: {pic2_url}")
        
        # 调用Coze API
        headers = {
            "Authorization": f"Bearer {COZE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "workflow_id": WORKFLOW_ID,
            "parameters": {
                "face_image": pic1_url,
                "base_image": pic2_url
            }
        }
        
        # 详细记录请求信息
        logger.info("==================== Coze API 请求详情 ====================")
        logger.info(f"请求URL: {COZE_API_URL}")
        logger.info("请求头:")
        for header_name, header_value in headers.items():
            if header_name.lower() == "authorization":
                logger.info(f"  {header_name}: Bearer ****{header_value[-8:]}")
            else:
                logger.info(f"  {header_name}: {header_value}")
        
        logger.info("请求体:")
        logger.info(f"  工作流ID: {payload['workflow_id']}")
        logger.info("  参数:")
        logger.info(f"    face_image: {payload['parameters']['face_image']}")
        logger.info(f"    base_image: {payload['parameters']['base_image']}")
        
        # 发送请求
        logger.info("开始发送请求...")
        response = requests.post(COZE_API_URL, headers=headers, json=payload)
        
        # 详细记录响应信息
        logger.info("==================== Coze API 响应详情 ====================")
        logger.info(f"响应状态码: {response.status_code}")
        logger.info("响应头:")
        for header_name, header_value in response.headers.items():
            logger.info(f"  {header_name}: {header_value}")
        
        logger.info("响应体:")
        response_json = response.json()
        logger.info(f"  原始响应: {response.text}")
        logger.info(f"  解析后的JSON: {response_json}")
        
        if response.status_code == 200:
            logger.info("请求成功完成")
        else:
            logger.warning(f"请求返回非200状态码: {response.status_code}")
            
        logger.info("================ Coze API 请求-响应周期结束 ================")
        
        return {
            "status": "success",
            "pic1_url": pic1_url,
            "pic2_url": pic2_url,
            "coze_response": response_json
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API调用时发生网络错误: {str(e)}")
        return {"status": "error", "message": f"网络请求错误: {str(e)}"}
    except Exception as e:
        logger.error(f"处理过程中发生错误: {str(e)}")
        return {"status": "error", "message": str(e)}

# 在应用启动时添加日志
@app.on_event("startup")
async def startup_event():
    logger.info("应用启动")
    logger.info(f"Python 版本: {sys.version}")
    logger.info(f"FastAPI 版本: {fastapi.__version__}")
    logger.info(f"当前工作目录: {os.getcwd()}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "working_directory": os.getcwd()
    }

if __name__ == "__main__":
    logger.info(f"服务启动于: http://localhost:8000")
    logger.info(f"图片上传目录: {os.path.abspath(UPLOAD_DIR)}")
    uvicorn.run("main:app", host="127.0.0.1", port=8000) 