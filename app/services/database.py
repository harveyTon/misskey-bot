"""
数据库服务
"""
import json
import time
from datetime import datetime, timedelta
import redis

from app.config.settings import (
    REDIS_URL, USER_PREFIX, CAPTCHA_PREFIX, INVITE_CODE_PREFIX, STATS_PREFIX,
    CAPTCHA_EXPIRY_SECONDS, MAX_INVITES_PER_WEEK, ADMIN_IDS, STATS_RETENTION_DAYS
)

# 连接到Redis
redis_client = redis.from_url(REDIS_URL)

# 用户相关操作
def save_user(user_id, username, first_name, last_name=None):
    """保存用户信息到Redis"""
    user_data = {
        'username': username,
        'first_name': first_name,
        'last_name': last_name,
        'registered_at': datetime.now().isoformat(),
        'is_admin': user_id in ADMIN_IDS
    }
    redis_client.set(f"{USER_PREFIX}{user_id}", json.dumps(user_data))

def get_user(user_id):
    """从Redis获取用户信息"""
    user_data = redis_client.get(f"{USER_PREFIX}{user_id}")
    if user_data:
        return json.loads(user_data)
    return None

def is_admin(user_id):
    """检查用户是否为管理员"""
    # 首先检查配置中的管理员列表
    if user_id in ADMIN_IDS:
        return True
    
    # 然后检查数据库中的用户信息
    user = get_user(user_id)
    return user and user.get('is_admin', False)

# 验证码相关操作
def save_captcha(user_id, captcha_text, expiry_seconds=None):
    """保存验证码到Redis，默认5分钟过期"""
    if expiry_seconds is None:
        expiry_seconds = CAPTCHA_EXPIRY_SECONDS
    redis_client.setex(f"{CAPTCHA_PREFIX}{user_id}", expiry_seconds, captcha_text)

def verify_captcha(user_id, captcha_text):
    """验证用户输入的验证码"""
    # 管理员无需验证码
    if is_admin(user_id):
        return True
        
    stored_captcha = redis_client.get(f"{CAPTCHA_PREFIX}{user_id}")
    if stored_captcha and stored_captcha.decode('utf-8').lower() == captcha_text.lower():
        redis_client.delete(f"{CAPTCHA_PREFIX}{user_id}")
        return True
    return False

# 邀请码相关操作
def record_invite_code_request(user_id, invite_code, expiry_days=None):
    """记录用户获取邀请码的信息"""
    now = datetime.now()
    
    # 管理员生成的邀请码可以设置为永久有效
    if is_admin(user_id) and expiry_days is None:
        expiry_date = None
        expires_at = None
    else:
        expiry_date = now + timedelta(days=expiry_days)
        expires_at = expiry_date.isoformat()
    
    record = {
        'invite_code': invite_code,
        'requested_at': now.isoformat(),
        'expires_at': expires_at,
        'is_admin_generated': is_admin(user_id)
    }
    
    # 获取用户的邀请码历史记录
    history_key = f"{INVITE_CODE_PREFIX}{user_id}"
    history = redis_client.get(history_key)
    
    if history:
        history_list = json.loads(history)
        history_list.append(record)
    else:
        history_list = [record]
    
    # 保存更新后的历史记录
    redis_client.set(history_key, json.dumps(history_list))
    
    # 更新统计信息
    update_invite_stats(invite_code, user_id, is_admin(user_id))
    
    return record

def can_request_invite_code(user_id):
    """检查用户是否可以请求邀请码（每周限制）"""
    # 管理员不受限制
    if is_admin(user_id):
        return True
        
    history_key = f"{INVITE_CODE_PREFIX}{user_id}"
    history = redis_client.get(history_key)
    
    if not history:
        return True
    
    history_list = json.loads(history)
    
    # 计算一周前的时间
    one_week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    
    # 统计一周内请求的邀请码数量
    recent_requests = sum(1 for record in history_list 
                         if record['requested_at'] > one_week_ago)
    
    return recent_requests < MAX_INVITES_PER_WEEK

def get_user_invite_history(user_id):
    """获取用户的邀请码历史记录"""
    history_key = f"{INVITE_CODE_PREFIX}{user_id}"
    history = redis_client.get(history_key)
    
    if history:
        return json.loads(history)
    return []

# 统计相关操作
def update_invite_stats(invite_code, user_id, is_admin):
    """更新邀请码统计信息"""
    today = datetime.now().strftime('%Y-%m-%d')
    stats_key = f"{STATS_PREFIX}{today}"
    
    # 获取今日统计
    stats = redis_client.get(stats_key)
    if stats:
        stats_data = json.loads(stats)
    else:
        stats_data = {
            'total_invites': 0,
            'admin_invites': 0,
            'user_invites': 0,
            'users': {}
        }
    
    # 更新统计数据
    stats_data['total_invites'] += 1
    if is_admin:
        stats_data['admin_invites'] += 1
    else:
        stats_data['user_invites'] += 1
    
    # 记录用户信息
    user_id_str = str(user_id)
    if user_id_str in stats_data['users']:
        stats_data['users'][user_id_str] += 1
    else:
        stats_data['users'][user_id_str] = 1
    
    # 保存统计数据
    redis_client.set(stats_key, json.dumps(stats_data))
    
    # 设置过期时间（保留30天）
    redis_client.expire(stats_key, STATS_RETENTION_DAYS * 24 * 60 * 60)

def get_invite_stats(days=7):
    """获取最近几天的邀请码统计信息"""
    stats = []
    
    # 获取最近几天的日期
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        stats_key = f"{STATS_PREFIX}{date}"
        
        # 获取该日的统计数据
        stats_data = redis_client.get(stats_key)
        if stats_data:
            day_stats = json.loads(stats_data)
            day_stats['date'] = date
            stats.append(day_stats)
        else:
            # 如果没有数据，添加空记录
            stats.append({
                'date': date,
                'total_invites': 0,
                'admin_invites': 0,
                'user_invites': 0,
                'users': {}
            })
    
    return stats 