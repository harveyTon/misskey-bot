"""
配置设置
"""
import os
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Telegram 配置
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Misskey API 配置
MISSKEY_API_URL = os.getenv('MISSKEY_API_URL')
MISSKEY_API_TOKEN = os.getenv('MISSKEY_API_TOKEN')
INVITE_CODE_EXPIRY_DAYS = int(os.getenv('INVITE_CODE_EXPIRY_DAYS', 7))

# Redis 配置
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# 应用配置
MAX_INVITES_PER_WEEK = int(os.getenv('MAX_INVITES_PER_WEEK', 1))
CAPTCHA_EXPIRY_SECONDS = int(os.getenv('CAPTCHA_EXPIRY_SECONDS', 300))

# Redis 键前缀
USER_PREFIX = 'user:'
CAPTCHA_PREFIX = 'captcha:'
INVITE_CODE_PREFIX = 'invite_code:'
STATS_PREFIX = 'stats:'

# 管理员配置
# 从环境变量中获取管理员ID列表，格式为逗号分隔的数字
ADMIN_IDS = []
admin_ids_str = os.getenv('ADMIN_IDS', '')
if admin_ids_str:
    try:
        ADMIN_IDS = [int(admin_id.strip()) for admin_id in admin_ids_str.split(',') if admin_id.strip()]
    except ValueError:
        print("警告: ADMIN_IDS 格式不正确，应为逗号分隔的数字")

# 统计数据保留天数
STATS_RETENTION_DAYS = int(os.getenv('STATS_RETENTION_DAYS', 30))

# 实例名称配置
INSTANCE_NAME = os.getenv('INSTANCE_NAME', 'Misskey')