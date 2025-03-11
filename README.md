# misskey-bot

这是一个 Telegram 机器人，用于为用户提供 Misskey 实例的邀请码。示例： https://t.me/urweibo_bot

## 功能

- 通过 API 获取 Misskey 实例的邀请码
- 设置邀请码有效期
- 用户获取邀请码需要输入验证码
- 每个用户每周只允许获取一次邀请码
- 管理员功能：无需验证码、生成永久邀请码、不受频率限制
- 邀请码统计功能
- 用户信息查询功能

## 项目结构

```
.
├── app/                    # 应用主目录
│   ├── __init__.py         # 包初始化文件
│   ├── bot.py              # 机器人主模块
│   ├── config/             # 配置目录
│   │   ├── __init__.py
│   │   └── settings.py     # 配置设置
│   ├── services/           # 服务目录
│   │   ├── __init__.py
│   │   ├── database.py     # 数据库服务
│   │   └── misskey_api.py  # Misskey API 服务
│   └── utils/              # 工具目录
│       ├── __init__.py
│       └── captcha_generator.py  # 验证码生成器
├── main.py                 # 入口文件
├── requirements.txt        # 依赖项
├── .env.example           # 环境变量示例
├── .gitignore            # Git 忽略文件配置
├── .dockerignore         # Docker 忽略文件配置
├── Dockerfile            # Docker 配置
├── docker-compose.yml    # Docker Compose 配置
├── run.sh               # 运行脚本
├── LICENSE              # 许可证文件
└── README.md            # 项目说明
```

## 安装与运行

### 方法一：直接运行

1. 克隆此仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 创建 `.env` 文件并设置环境变量（参考 `.env.example`）
4. 运行机器人：`python main.py`

### 方法二：使用 Docker

1. 克隆此仓库
2. 创建 `.env` 文件并设置环境变量（参考 `.env.example`）
3. 使用 Docker Compose 启动：`docker-compose up -d`

## 环境变量

| 变量名                  | 说明                                                          | 默认值                   |
| ----------------------- | ------------------------------------------------------------- | ------------------------ |
| TELEGRAM_BOT_TOKEN      | Telegram 机器人 Token                                         | 必填                     |
| MISSKEY_API_URL         | Misskey 实例的 URL（例如：https://your-misskey-instance.com） | 必填                     |
| MISSKEY_API_TOKEN       | Misskey API Token                                             | 必填                     |
| REDIS_URL               | Redis 连接 URL                                                | redis://localhost:6379/0 |
| INVITE_CODE_EXPIRY_DAYS | 邀请码有效期（天）                                            | 7                        |
| MAX_INVITES_PER_WEEK    | 每周最大邀请码数量                                            | 1                        |
| CAPTCHA_EXPIRY_SECONDS  | 验证码有效期（秒）                                            | 300                      |
| ADMIN_IDS               | 管理员 ID，逗号分隔的 Telegram 用户 ID 列表                   | 在 https://t.me/urweibo_bot 发送 /info 获取                       |
| STATS_RETENTION_DAYS    | 统计数据保留天数                                              | 30                       |
| INSTANCE_NAME           | Misskey 实例名称，用于显示在机器人消息中                       | Misskey                  |

## 使用方法

### 普通用户

1. 在 Telegram 中搜索你的机器人
2. 发送 `/start` 命令开始使用
3. 发送 `/invite` 命令获取邀请码
4. 输入验证码
5. 获取邀请码
6. 使用 `/history` 命令查看邀请码历史
7. 使用 `/info` 命令查看你的用户信息（包括用户 ID）

### 管理员

1. 在 `.env` 文件中设置 `ADMIN_IDS` 环境变量，添加管理员的 Telegram 用户 ID
2. 管理员可以使用 `/admin` 命令访问管理菜单
3. 管理员可以使用 `/stats` 命令查看邀请码统计信息
4. 管理员使用 `/invite` 命令可以直接获取永久邀请码，无需验证码
5. 管理员生成的邀请码不会过期，也不受每周生成次数的限制

## 可用命令

| 命令     | 说明                        | 用户类型 |
| -------- | --------------------------- | -------- |
| /start   | 开始使用机器人              | 所有用户 |
| /help    | 显示帮助信息                | 所有用户 |
| /invite  | 获取邀请码                  | 所有用户 |
| /history | 查看邀请码历史              | 所有用户 |
| /info    | 查看用户信息（包括用户 ID） | 所有用户 |
| /admin   | 访问管理员菜单              | 仅管理员 |
| /stats   | 查看邀请码统计信息          | 仅管理员 |

## 依赖项

- python-telegram-bot
- requests
- python-dotenv
- captcha
- Pillow
- redis

## 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交 Issue 和 Pull Request！


## 鸣谢

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Misskey](https://misskey-hub.net/)
