
import requests
import json

TASK_ID = "41c84359-41f4-4eed-8367-1faac6c19bce"

def get_task_id():
    """
    从文本文件获取任务ID
    """
    try:
        with open('task_id.txt', 'r') as f:
            # 读取第一个非空行作为默认任务ID
            for line in f:
                task_id = line.strip()
                if task_id:
                    return task_id
            
            # 如果文件为空，写入默认任务ID
            with open('task_id.txt', 'w') as f:
                f.write(TASK_ID)
            return TASK_ID
    except Exception as e:
        # 出错时返回默认任务ID
        print(f"读取 task_id.txt 文件时出错: {str(e)}")
        return TASK_ID

def update_cookie_in_env():
    """
    获取新的cookie并更新到.env文件
    """
    url = "https://api.tripo3d.ai/v2/web/account/email/login/password"
    #用固定的账号登陆
    payload = json.dumps({
       "email": "3d123321@pdjjq.org",
       "password": "YQsK++uB8OS2qYC3H8a/j0roQp6mneSZP2fMwpRQWr9v5kMAGE3qGd6r7yZ+kcrGQZL/Sb0qw178vQ1ZzzqE75OpbLaA+ojh+pyFkUtjlwuzlxIp8iURyiQcaCJaRm+jK4uAc17j2LjaZOPiQQnBk9bA5W6708LcCzsH8yCrVTk="
    })
    headers = {
       'priority': 'u=1, i',
       'use-language': 'zh',
       'x-client-id': 'web',
       'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
       'content-type': 'application/json',
       'Accept': '*/*',
       'Host': 'api.tripo3d.ai',
       'Connection': 'keep-alive'
    }

    response = requests.post(url, headers=headers, data=payload)

    # 提取cookie
    cookies = response.cookies.get_dict()
    cookie_str = "; ".join([f"{key}={value}" for key, value in cookies.items()])

    print("Cookies:", cookie_str)

    # 清理旧的cookie并写入新的cookie到.env文件
    env_file = '.env'
    new_lines = []
    with open(env_file, 'r') as f:
        for line in f:
            if not line.startswith("TRIPO_API_COOKIE="):
                new_lines.append(line)

    new_lines.append(f"TRIPO_API_COOKIE={cookie_str}\n")

    with open(env_file, 'w') as f:
        f.writelines(new_lines)

    print(f"Cookies已更新到 {env_file}")