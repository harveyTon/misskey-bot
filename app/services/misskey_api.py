"""
Misskey API 服务
"""
import requests
import logging
from datetime import datetime, timedelta

from app.config.settings import (
    MISSKEY_API_URL, MISSKEY_API_TOKEN, INVITE_CODE_EXPIRY_DAYS
)

# 配置日志
logger = logging.getLogger(__name__)

def create_invite_code(is_admin=False):
    """
    通过 Misskey API 创建邀请码
    
    参数:
        is_admin (bool): 是否为管理员创建的邀请码，管理员创建的邀请码可以永久有效
    
    返回:
        dict: 包含邀请码和过期时间的字典
    """
    if not MISSKEY_API_URL or not MISSKEY_API_TOKEN:
        raise ValueError("Misskey API URL 或 Token 未设置")
    
    # 计算过期时间，管理员可以创建永久邀请码
    if is_admin:
        expiry_date = None
    else:
        expiry_date = datetime.now() + timedelta(days=INVITE_CODE_EXPIRY_DAYS)
    
    # 准备请求数据
    # 根据示例代码，使用 /api/invite/create 端点
    # 并使用 count 和 expiresAt 参数
    url = f"{MISSKEY_API_URL}/invite/create"
    
    # 如果 MISSKEY_API_URL 不包含 /api，则添加
    if not url.endswith('/invite/create'):
        if not MISSKEY_API_URL.endswith('/'):
            url = f"{MISSKEY_API_URL}/api/invite/create"
        else:
            url = f"{MISSKEY_API_URL}api/invite/create"
    
    data = {
        "i": MISSKEY_API_TOKEN,  # 认证令牌
        "count": 1,              # 生成一个邀请码
    }
    
    # 只有非管理员才设置过期时间
    if expiry_date:
        data["expiresAt"] = expiry_date.isoformat()
    
    headers = {"Content-Type": "application/json"}
    
    # 发送请求创建邀请码
    try:
        logger.info(f"正在请求邀请码: {url}")
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # 如果请求失败，抛出异常
        
        # 解析响应
        invite_data = response.json()
        logger.info(f"邀请码请求成功: {invite_data}")
        
        # 根据响应格式处理结果
        # 如果返回的是列表（多个邀请码），取第一个
        if isinstance(invite_data, list) and len(invite_data) > 0:
            code = invite_data[0].get('code')
            expires_at = invite_data[0].get('expiresAt')
        else:
            # 如果返回的是单个对象
            code = invite_data.get('code')
            expires_at = invite_data.get('expiresAt')
        
        # 如果是管理员创建的邀请码且没有过期时间，则设置为None
        if is_admin and not expires_at:
            expires_at = None
        elif expires_at is None and expiry_date:
            # 如果API没有返回过期时间但我们设置了过期时间
            expires_at = expiry_date.isoformat()
        
        return {
            'code': code,
            'expires_at': expires_at
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"创建邀请码时出错: {e}")
        return None
    except Exception as e:
        logger.error(f"处理邀请码响应时出错: {e}")
        return None

def get_invite_code_url(code):
    """
    获取邀请码的完整URL
    
    参数:
        code (str): 邀请码
        
    返回:
        str: 邀请码的完整URL
    """
    # 从API URL中提取实例域名
    instance_url = MISSKEY_API_URL
    
    # 移除 /api 部分以获取实例根URL
    if '/api' in instance_url:
        instance_url = instance_url.split('/api')[0]
    
    # 确保没有尾随斜杠
    if instance_url.endswith('/'):
        instance_url = instance_url[:-1]
    
    return f"{instance_url}/?invitation={code}"

def get_instance_url():
    """
    获取 Misskey 实例的 URL
    
    返回:
        str: 实例的完整 URL
    """
    # 从 API URL 中提取实例域名
    instance_url = MISSKEY_API_URL
    
    # 移除 /api 部分以获取实例根 URL
    if '/api' in instance_url:
        instance_url = instance_url.split('/api')[0]
    
    # 确保没有尾随斜杠
    if instance_url.endswith('/'):
        instance_url = instance_url[:-1]
    
    return instance_url 