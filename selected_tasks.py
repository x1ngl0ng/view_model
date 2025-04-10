#!/usr/bin/env python
"""
管理已选择的任务ID
"""
import os
import json

SELECTED_TASKS_FILE = 'selected_tasks.json'

def get_selected_tasks():
    """获取已选择的任务ID列表"""
    if not os.path.exists(SELECTED_TASKS_FILE):
        return []
    
    try:
        with open(SELECTED_TASKS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def add_selected_tasks(task_ids):
    """添加任务ID到已选择列表"""
    selected = get_selected_tasks()
    
    # 添加新的任务ID
    for task_id in task_ids:
        if task_id not in selected:
            selected.append(task_id)
    
    # 保存到文件
    with open(SELECTED_TASKS_FILE, 'w') as f:
        json.dump(selected, f, indent=2)
    
    return selected

def clear_selected_tasks():
    """清空已选择的任务ID列表"""
    if os.path.exists(SELECTED_TASKS_FILE):
        os.remove(SELECTED_TASKS_FILE)
    return []

def get_unselected_tasks(all_tasks):
    """获取未选择的任务ID列表"""
    selected = get_selected_tasks()
    return [task for task in all_tasks if task not in selected] 