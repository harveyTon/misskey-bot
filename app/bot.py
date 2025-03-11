"""
Telegram 机器人主模块
"""
from loguru import logger
import sys
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# 导入自定义模块
from app.config.settings import TELEGRAM_BOT_TOKEN, INVITE_CODE_EXPIRY_DAYS, INSTANCE_NAME
from app.utils import captcha_generator as captcha
from app.services import database as db
from app.services import misskey_api as misskey

# 配置 loguru 日志
logger.remove()
logger.add(sys.stderr, level="INFO")  # 控制台输出
logger.add("logs/info.log", rotation="1 week", retention="1 month", level="INFO")  # 信息日志
logger.add("logs/error.log", rotation="1 week", retention="1 month", level="ERROR")  # 错误日志
logger.add("logs/debug.log", rotation="1 week", retention="1 month", level="DEBUG")  # 调试日志
logger.add("logs/all.log", rotation="1 week", retention="1 month")  # 所有日志

# 用户状态
USER_STATES = {}
# 状态常量
STATE_IDLE = 'idle'
STATE_WAITING_FOR_CAPTCHA = 'waiting_for_captcha'

# 命令处理函数
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /start 命令"""
    user = update.effective_user
    
    # 保存用户信息
    db.save_user(
        user.id, 
        user.username, 
        user.first_name, 
        user.last_name
    )
    
    # 检查是否为管理员
    is_admin = db.is_admin(user.id)
    
    # 基本欢迎消息
    welcome_text = (
        f"你好，{user.first_name}！👋\n\n"
        f"我是 {INSTANCE_NAME} 邀请码机器人。我可以帮你获取 {INSTANCE_NAME} 实例的邀请码。\n\n"
        "可用命令：\n"
        "/invite - 获取邀请码\n"
        "/history - 查看邀请码历史\n"
        "/help - 查看帮助信息\n"
        "/info - 查看用户信息"
    )
    
    # 只向管理员显示管理员相关信息
    if is_admin:
        admin_text = (
            "\n\n🔑 管理员功能\n"
            "你是管理员，可以使用以下额外命令：\n"
            "/admin - 管理员菜单\n"
            "/stats - 查看邀请码统计"
        )
        welcome_text += admin_text
    
    # 创建内联键盘
    keyboard = [
        [InlineKeyboardButton("🌐 访问实例", url=misskey.get_instance_url())],
        [InlineKeyboardButton("📋 获取邀请码", callback_data="get_invite")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # 发送欢迎消息
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /help 命令"""
    user_id = update.effective_user.id
    is_admin = db.is_admin(user_id)
    
    # 基本帮助信息 - 所有用户都可以看到
    help_text = (
        "📚 帮助信息 📚\n\n"
        "可用命令:\n"
        "/start - 开始使用机器人\n"
        f"/invite - 获取 {INSTANCE_NAME} 邀请码\n"
        "/history - 查看你的邀请码历史\n"
        "/info - 查看你的用户信息\n"
        "/help - 显示此帮助信息\n\n"
    )
    
    # 获取邀请码流程 - 根据用户类型显示不同内容
    if is_admin:
        # 管理员额外命令 - 只有管理员可以看到
        help_text += (
            "管理员命令:\n"
            "/admin - 管理员菜单\n"
            "/stats - 查看邀请码统计\n\n"
            
            "获取邀请码流程 (管理员):\n"
            "1. 发送 /invite 命令\n"
            "2. 直接获取邀请码 (无需验证码)\n\n"
            "注意:\n"
            "- 管理员生成的邀请码永久有效\n"
            "- 管理员不受每周获取次数限制\n"
        )
    else:
        # 普通用户流程 - 只有普通用户可以看到
        help_text += (
            "获取邀请码流程:\n"
            "1. 发送 /invite 命令\n"
            "2. 输入验证码\n"
            "3. 获取邀请码\n\n"
            "注意:\n"
            "- 每个用户每周只能获取一次邀请码\n"
            f"- 邀请码有效期为 {INVITE_CODE_EXPIRY_DAYS} 天\n"
        )
    
    await update.message.reply_text(help_text)

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /info 命令 - 显示用户信息"""
    user = update.effective_user
    user_data = db.get_user(user.id) or {}
    
    # 获取注册时间
    registered_at = "未知"
    if user_data and 'registered_at' in user_data:
        try:
            registered_at = datetime.fromisoformat(user_data['registered_at']).strftime('%Y-%m-%d %H:%M')
        except (ValueError, TypeError):
            pass
    
    # 检查是否为管理员
    is_admin = db.is_admin(user.id)
    
    # 构建用户信息消息
    info_text = (
        "👤 用户信息 👤\n\n"
        f"用户ID: {user.id}\n"
        f"用户名: {user.username or '未设置'}\n"
        f"姓名: {user.first_name}"
    )
    
    if user.last_name:
        info_text += f" {user.last_name}"
    
    info_text += f"\n注册时间: {registered_at}\n"
    
    # 只向管理员显示管理员状态
    if is_admin:
        info_text += "管理员: ✅ 是\n\n"
    else:
        info_text += "\n"
    
    # 获取邀请码历史统计
    history = db.get_user_invite_history(user.id)
    total_invites = len(history)
    
    # 计算有效邀请码数量
    valid_invites = 0
    for record in history:
        if record.get('expires_at') is None:  # 永久有效
            valid_invites += 1
        elif datetime.now() < datetime.fromisoformat(record['expires_at']):
            valid_invites += 1
    
    # 添加邀请码统计信息
    info_text += (
        "邀请码统计:\n"
        f"总计: {total_invites} 个\n"
        f"有效: {valid_invites} 个\n"
        f"已过期: {total_invites - valid_invites} 个\n"
    )
    
    await update.message.reply_text(info_text)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /admin 命令 - 仅管理员可用"""
    user_id = update.effective_user.id
    
    # 检查是否为管理员
    if not db.is_admin(user_id):
        await update.message.reply_text("⚠️ 你不是管理员，无法使用此命令。")
        return
    
    # 创建管理员菜单
    keyboard = [
        [InlineKeyboardButton("📊 查看统计", callback_data="admin_stats")],
        [InlineKeyboardButton("🔑 生成永久邀请码", callback_data="admin_invite")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👑 管理员菜单 👑\n\n"
        "请选择操作：",
        reply_markup=reply_markup
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /stats 命令 - 查看邀请码统计"""
    user_id = update.effective_user.id
    
    # 检查是否为管理员
    if not db.is_admin(user_id):
        await update.message.reply_text("⚠️ 你不是管理员，无法使用此命令。")
        return
    
    # 获取统计数据
    days = 7
    if context.args and context.args[0].isdigit():
        days = min(int(context.args[0]), 30)  # 最多显示30天
    
    stats = db.get_invite_stats(days)
    
    # 生成统计报告
    stats_text = f"📊 最近 {days} 天的邀请码统计 📊\n\n"
    
    # 总计
    total_invites = sum(day['total_invites'] for day in stats)
    admin_invites = sum(day['admin_invites'] for day in stats)
    user_invites = sum(day['user_invites'] for day in stats)
    
    stats_text += (
        "总计:\n"
        f"总邀请码数量: {total_invites}\n"
        f"管理员生成: {admin_invites}\n"
        f"普通用户生成: {user_invites}\n\n"
        "每日统计:\n"
    )
    
    # 每日统计
    for day in stats:
        date = day['date']
        total = day['total_invites']
        admin = day['admin_invites']
        user = day['user_invites']
        
        if total > 0:
            stats_text += f"{date}: 总计 {total} (管理员: {admin}, 用户: {user})\n"
    
    # 如果统计信息太长，可能需要分多条消息发送
    if len(stats_text) > 4000:
        await update.message.reply_text("⚠️ 统计信息太长，只显示总计信息。")
        await update.message.reply_text(stats_text.split("每日统计:")[0])
    else:
        await update.message.reply_text(stats_text)

async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /invite 命令"""
    user_id = update.effective_user.id
    is_admin = db.is_admin(user_id)
    
    # 检查用户是否可以请求邀请码
    if not is_admin and not db.can_request_invite_code(user_id):
        await update.message.reply_text(
            "⚠️ 你已经在本周内获取过邀请码了，请等待下周再试。\n\n"
            "使用 /history 命令查看你的邀请码历史。"
        )
        return
    
    # 管理员直接获取邀请码，无需验证码
    if is_admin:
        await update.message.reply_text(f"👑 管理员正在生成 {INSTANCE_NAME} 邀请码...")
        await generate_invite_code(update, user_id, is_admin=True)
        return
    
    # 普通用户需要验证码
    # 生成验证码
    captcha_text, captcha_image = captcha.generate_captcha()
    
    # 保存验证码到数据库
    db.save_captcha(user_id, captcha_text)
    
    # 更新用户状态
    USER_STATES[user_id] = STATE_WAITING_FOR_CAPTCHA
    
    # 发送验证码图片
    await update.message.reply_photo(
        photo=captcha_image,
        caption=f"请输入上图中的验证码以获取 {INSTANCE_NAME} 邀请码。\n验证码有效期为5分钟。"
    )

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /history 命令"""
    user_id = update.effective_user.id
    is_admin = db.is_admin(user_id)
    
    # 获取用户的邀请码历史
    history = db.get_user_invite_history(user_id)
    
    if not history:
        await update.message.reply_text("你还没有获取过邀请码。")
        return
    
    # 构建历史记录消息
    history_text = "📜 你的邀请码历史 📜\n\n"
    
    for i, record in enumerate(history, 1):
        requested_at = datetime.fromisoformat(record['requested_at'])
        
        # 处理过期时间
        if record.get('expires_at'):
            expires_at = datetime.fromisoformat(record['expires_at'])
            # 检查是否已过期
            is_expired = datetime.now() > expires_at
            status = "❌ 已过期" if is_expired else "✅ 有效"
            expiry_info = f"过期时间: {expires_at.strftime('%Y-%m-%d %H:%M')}\n"
        else:
            # 永久有效的邀请码
            status = "✅ 永久有效"
            expiry_info = "过期时间: 永不过期\n"
        
        # 添加管理员标记 - 只有管理员可以看到
        admin_mark = ""
        if is_admin and record.get('is_admin_generated'):
            admin_mark = " 👑"
        
        history_text += (
            f"{i}. 邀请码: {record['invite_code']}{admin_mark}\n"
            f"获取时间: {requested_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"{expiry_info}"
            f"状态: {status}\n\n"
        )
    
    await update.message.reply_text(history_text)

async def handle_captcha_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理用户输入的验证码"""
    user_id = update.effective_user.id
    
    # 检查用户是否在等待验证码状态
    if user_id not in USER_STATES or USER_STATES[user_id] != STATE_WAITING_FOR_CAPTCHA:
        return
    
    captcha_text = update.message.text.strip()
    
    # 验证验证码
    if db.verify_captcha(user_id, captcha_text):
        # 验证成功，创建邀请码
        await update.message.reply_text("✅ 验证码正确！正在为你生成邀请码...")
        await generate_invite_code(update, user_id)
    else:
        # 验证失败
        await update.message.reply_text(
            "❌ 验证码错误或已过期，请重新获取。\n\n"
            "使用 /invite 命令重新获取验证码。"
        )
    
    # 重置用户状态
    USER_STATES[user_id] = STATE_IDLE

async def generate_invite_code(update, user_id, is_admin=False):
    """生成邀请码并发送给用户"""
    # 调用 Misskey API 创建邀请码
    invite_data = misskey.create_invite_code(is_admin=is_admin)
    
    if invite_data and 'code' in invite_data:
        # 记录邀请码请求
        record = db.record_invite_code_request(
            user_id, 
            invite_data['code'], 
            INVITE_CODE_EXPIRY_DAYS if not is_admin else None
        )
        
        # 获取邀请链接
        invite_url = misskey.get_invite_code_url(invite_data['code'])
        
        # 构建邀请码消息
        invite_message = "🎉 邀请码生成成功 🎉\n\n"
        
        # 添加管理员标记
        if is_admin:
            invite_message += "👑 管理员生成的永久邀请码\n\n"
        
        invite_message += f"邀请码: {invite_data['code']}\n\n"
        
        # 处理过期时间
        if invite_data.get('expires_at'):
            expires_at = datetime.fromisoformat(invite_data['expires_at'])
            invite_message += f"过期时间: {expires_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        else:
            invite_message += "过期时间: 永不过期\n\n"
        
        invite_message += f"注册链接: {invite_url}\n\n"
        invite_message += "请在过期前使用此邀请码。" if invite_data.get('expires_at') else "此邀请码永不过期。"
        
        # 创建内联键盘
        keyboard = [
            [InlineKeyboardButton("📋 复制邀请码", callback_data=f"copy_{invite_data['code']}")],
            [InlineKeyboardButton("🔗 打开注册链接", url=invite_url)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            invite_message,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            "❌ 生成邀请码时出错，请稍后再试或联系管理员。"
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理按钮回调"""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    # 处理复制邀请码按钮
    if query.data.startswith("copy_"):
        invite_code = query.data.split("_")[1]
        await query.edit_message_text(
            text=f"邀请码: {invite_code}\n\n请复制上面的邀请码。"
        )
    # 处理获取邀请码按钮
    elif query.data == "get_invite":
        await query.message.reply_text("请使用 /invite 命令获取邀请码。")
    # 处理管理员统计按钮
    elif query.data == "admin_stats" and db.is_admin(user_id):
        stats = db.get_invite_stats(7)  # 获取最近7天的统计
        
        # 生成简短的统计报告
        stats_text = "📊 最近 7 天的邀请码统计 📊\n\n"
        
        # 总计
        total_invites = sum(day['total_invites'] for day in stats)
        admin_invites = sum(day['admin_invites'] for day in stats)
        user_invites = sum(day['user_invites'] for day in stats)
        
        stats_text += (
            f"总邀请码数量: {total_invites}\n"
            f"管理员生成: {admin_invites}\n"
            f"普通用户生成: {user_invites}\n\n"
            "使用 /stats 命令查看详细统计"
        )
        
        await query.edit_message_text(text=stats_text)
    # 处理管理员生成邀请码按钮
    elif query.data == "admin_invite" and db.is_admin(user_id):
        await query.edit_message_text(text="👑 管理员正在生成邀请码...")
        
        # 创建新的更新对象，因为回调查询不能直接用于发送新消息
        new_update = Update(update.update_id, message=query.message)
        await generate_invite_code(new_update, user_id, is_admin=True)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理错误"""
    logger.error(f"更新 {update} 导致错误 {context.error}")

def main() -> None:
    """启动机器人"""
    # 创建应用
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # 添加命令处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("invite", invite_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # 添加消息处理器
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_captcha_response))
    
    # 添加回调查询处理器
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # 添加错误处理器
    application.add_error_handler(error_handler)
    
    # 启动机器人
    logger.info("启动机器人")
    application.run_polling() 