import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import requests
import logging
import json

from config import get_task_id, TASK_ID, update_cookie_in_env
from selected_tasks import get_selected_tasks, add_selected_tasks, get_unselected_tasks, clear_selected_tasks

load_dotenv()
token = os.getenv('TRIPO_API_TOKEN', 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6ImQwbDJldGdSeEd5Q19FVFZyOGgzRG9LMWxqa3ZCN0puQ1pPbTVwUFRyelkifQ.eyJzdWIiOiI2NzZiYTA2M2RkYTBlMzc2ODAxYWFjMGIiLCJhdWQiOiI2NWIyNTAzMjAxZjQwODZjMDQzZDcxMWYiLCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIHRlbmFudF9pZCIsImlhdCI6MTc0MzA0NTY2OSwiZXhwIjoxNzQ0MjU1MjY5LCJqdGkiOiJQVGlpQTZGQzVQYjZvWWVIMFFPcUlMQTNPN3lGaThHelhuT0s0cDN5QjdkIiwiaXNzIjoiaHR0cHM6Ly90cmlwby13ZWIudXMuYXV0aGluZy5jby9vaWRjIn0.KuMBtdxtx3k6CgDJXHz6YDzIguCxguLs2v-o7tODEzgLOfU8G11p9uJ7w4rH1nhwTGqn9yfKHWIUPiwnmgYOrXof_2Iv51SFBCa0fUMksHGNsh2YQHQ0HrRr5Vs1c2HnXWyFBV2uuWeXxUbFl0xwfN3i06dZD_puMqruE6PXzPTFlvxtWY7FHSt2XbBv10rOo8cNsMxDkqah0OFwpjz6mIiP2X0O_Xed68EA1QRMoDiV_jm4dLZBGgoMU5_9YYucmPViDD49ysvx6QHqfXmYbUgdsXkb3anMMmBDyo3dJNxv0N-VZDfMJMv0SLup5ZY5tAg7ZCOgPckJGU5rZSy2jQ')  # 使用环境变量或默认值

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 确保task_id.txt文件存在
if not os.path.exists('task_id.txt'):
    logger.info(f"创建task_id.txt文件，使用默认任务ID: {TASK_ID}")
    with open('task_id.txt', 'w') as f:
        f.write(TASK_ID)

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
    expose_headers=["*"]  # 暴露所有头部
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="."), name="static")
#登陆
update_cookie_in_env()

def fetch_model(url: str):
    try:
        logger.info(f"正在获取模型，URL: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Origin': 'https://www.tripo3d.ai',
            'Referer': 'https://www.tripo3d.ai/',
            'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Authorization': f'Bearer {token}'
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        logger.info(f"成功获取模型，大小: {len(response.content)} 字节")
        return response.content
    except requests.Timeout as e:
        logger.error(f"请求超时: {str(e)}")
        raise HTTPException(status_code=504, detail="请求超时，请重试")
    except requests.HTTPError as e:
        logger.error(f"HTTP错误: {str(e)}, 状态码: {e.response.status_code}, 响应: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"获取模型失败: {str(e)}")
    except Exception as e:
        logger.error(f"获取模型时出错，URL: {url}, 错误: {str(e)}")
        raise HTTPException(status_code=502, detail=f"获取模型失败: {str(e)}")


@app.get("/proxy/model")
def proxy_model(url: str):
    """
    代理接口，用于获取3D模型文件
    """
    try:
        logger.info(f"代理模型请求: {url}")

        # 使用requests发送请求
        model_data = fetch_model(url)
        logger.info(f"成功获取模型，大小: {len(model_data)} 字节")

        # 返回模型数据
        return StreamingResponse(
            content=iter([model_data]),
            media_type="model/gltf-binary",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Cache-Control": "public, max-age=31536000",
                "Content-Disposition": "inline; filename=model.glb",
                "Content-Length": str(len(model_data))
            }
        )
    except Exception as e:
        logger.error(f"代理模型时出错: {str(e)}")
        raise HTTPException(status_code=502, detail=f"获取模型失败: {str(e)}")


@app.get("/")
def read_root():
    """
    提供前端页面
    """
    return FileResponse('index.html')


@app.get("/api/task/{task_id}")
def get_task(task_id: str):
    """
    获取task_id的详细信息
    """
    try:
        logger.info(f"获取任务信息，任务ID: {task_id}")
        api_url = f"https://api.tripo3d.ai/v2/web/task/{task_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Origin': 'https://www.tripo3d.ai',
            'Referer': 'https://www.tripo3d.ai/',
            'Authorization': f'Bearer {token}',
            'use-language': 'zh',
            'x-client-id': 'web'
        }

        logger.info(f"发送API请求: {api_url}")
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        logger.info(f"API响应: {json.dumps(data, ensure_ascii=False)}")

        if data.get('code') == 0:
            model_url = data['data'].get('model') or data['data'].get('pbr_model')
            
            if model_url:
                logger.info(f"成功获取模型URL: {model_url}")
                return {
                    "code": 0,
                    "data": {
                        "task_id": task_id,
                        "model": model_url,
                        "thumbnail": data['data'].get('thumbnail', ''),
                        "name": data['data'].get('name', '')
                    }
                }
            else:
                error_msg = f"API响应中没有找到模型URL: {json.dumps(data['data'], ensure_ascii=False)[:200]}"
                logger.error(error_msg)
                raise ValueError(error_msg)
        else:
            error_msg = f"API响应无效: {json.dumps(data, ensure_ascii=False)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    except requests.HTTPError as e:
        error_msg = f"HTTP错误: {str(e)}, 状态码: {e.response.status_code}, 响应: {e.response.text}"
        logger.error(error_msg)
        return {"code": 1, "message": error_msg}
    except Exception as e:
        error_msg = f"获取任务信息时出错: {str(e)}"
        logger.error(error_msg)
        return {"code": 1, "message": error_msg}


@app.get("/api/default-task")
def get_default_task():
    try:
        task_id = get_task_id()
        logger.info(f"使用默认任务ID: {task_id}")
        return get_task(task_id)
    except Exception as e:
        logger.error(f"获取默认任务时出错: {str(e)}")
        return {"code": 1, "message": str(e)}


def fetch_task_details(task_id, headers):
    try:
        api_url = f"https://api.tripo3d.ai/v2/web/task/{task_id}"
        logger.info(f"获取任务详情，任务ID: {task_id}, URL: {api_url}")
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        logger.info(f"任务详情响应: {json.dumps(data, ensure_ascii=False)[:200]}...")
        
        if data.get('code') == 0:
            # 尝试获取不同类型的模型URL
            model_url = data['data'].get('model') or data['data'].get('pbr_model')
            
            if model_url:
                logger.info(f"成功获取模型URL: {model_url}")
                return {
                    "task_id": task_id,
                    "model": model_url,
                    "thumbnail": data['data'].get('thumbnail', ''),
                    "name": data['data'].get('name', '')
                }
            else:
                logger.error(f"任务详情中没有找到模型URL: {json.dumps(data['data'], ensure_ascii=False)[:200]}")
        else:
            logger.error(f"任务详情响应无效: {json.dumps(data, ensure_ascii=False)}")
    except Exception as e:
        logger.error(f"获取任务详情失败，任务ID: {task_id}, 错误: {str(e)}")
    return None


@app.get("/api/tasks")
def get_tasks(page: int = 1, page_size: int = 10):
    try:
        logger.info(f"获取任务列表，页码: {page}, 每页数量: {page_size}")
        
        # 每次请求时清空已选择的任务ID
        clear_selected_tasks()
        logger.info("已重置选择状态")
        
        # 确保文件存在
        if not os.path.exists('task_id.txt'):
            with open('task_id.txt', 'w') as f:
                f.write(TASK_ID)
            logger.info(f"创建task_id.txt文件，使用默认任务ID: {TASK_ID}")
            task_ids = [TASK_ID]
        else:
            with open('task_id.txt', 'r') as f:
                file_content = f.read()
            logger.info(f"task_id.txt 文件内容:\n{file_content}")
            
            # 处理文件内容，支持多种格式：每行一个ID或逗号分隔的ID，以及带引号的ID
            task_ids = []
            
            # 首先按行分割
            lines = [line.strip() for line in file_content.splitlines() if line.strip()]
            for line in lines:
                # 检查行内是否有逗号
                if ',' in line:
                    # 按逗号分割并添加每个ID
                    for id_part in line.split(','):
                        id_part = id_part.strip()
                        # 去除引号
                        id_part = id_part.strip('"\'')
                        if id_part:
                            task_ids.append(id_part)
                else:
                    # 整行作为一个ID，去除引号
                    line = line.strip('"\'')
                    task_ids.append(line)
            
            logger.info(f"解析后的任务ID列表: {task_ids}")
            # todo：刷新页面后，taskID会变少，需要解决 t：集合去重，记录已选择过的任务ID，每次刷新页面时，已选择的任务ID数为0
            # 去除重复项但保持顺序
            seen = set()
            task_ids = [x for x in task_ids if not (x in seen or seen.add(x))]
            logger.info(f"去重后的任务ID列表: {task_ids}")
            
            # 如果文件为空，使用默认任务ID
            if not task_ids:
                task_ids = [TASK_ID]
                with open('task_id.txt', 'w') as f:
                    f.write(TASK_ID)
                logger.info(f"task_id.txt为空，使用默认任务ID: {TASK_ID}")

        # 获取未选择的任务ID
        unselected_tasks = get_unselected_tasks(task_ids)
        logger.info(f"未选择的任务ID: {len(unselected_tasks)} 个")
        
        # 计算总数和分页
        total = len(unselected_tasks)
        start, end = (page - 1) * page_size, min(page * page_size, total)
        
        # 选择当前页的任务ID
        selected_task_ids = unselected_tasks[start:end]
        logger.info(f"选择 {len(selected_task_ids)} 个任务ID: {', '.join(selected_task_ids)}")
        
        # 记录已选择的任务ID
        add_selected_tasks(selected_task_ids)

        headers = {
            'Authorization': f'Bearer {token}',
            'Origin': 'https://www.tripo3d.ai',
            'Referer': 'https://www.tripo3d.ai/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'use-language': 'zh',
            'x-client-id': 'web'
        }

        tasks = [fetch_task_details(task_id, headers) for task_id in selected_task_ids]
        tasks = [t for t in tasks if t]
        logger.info(f"成功获取 {len(tasks)} 个任务详情")

        return {
            "code": 0,
            "data": {
                "items": tasks,
                "total": total,
                "page": page,
                "page_size": page_size,
                "selected_count": 0,
                "total_tasks": len(task_ids)
            }
        }
    except Exception as e:
        logger.error(f"获取任务列表时出错: {str(e)}")
        return {"code": 1, "message": str(e)}


# 添加一个路由来处理404错误，避免前端报错
@app.route("/hybridaction/{path:path}")
@app.get("/hybridaction/{path:path}")
async def handle_hybrid_action(path: str):
    """
    处理hybridaction请求，返回空对象以避免404错误
    """
    return JSONResponse(content={})


@app.get("/api/reset-selection")
def reset_selection():
    """重置任务选择状态"""
    try:
        clear_selected_tasks()
        logger.info("已重置选择状态")
        return {"code": 0, "message": "已重置选择状态"}
    except Exception as e:
        logger.error(f"重置选择状态时出错: {str(e)}")
        return {"code": 1, "message": str(e)}


if __name__ == "__main__":
    import uvicorn

    logger.info("启动服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8005)
