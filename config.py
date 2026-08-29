# config.py - 系统配置文件
# 所有全局配置放在这里，以后修改只需改这一个文件

import os

# ── 系统名称（修改这里，所有页面自动更新）──
SYSTEM_NAME = "我的ERP系统"  # ← 在这里改名字
SYSTEM_ICON = "📱"         # ← 在这里改图标

# ── 数据库配置 ──
# 数据库文件保存在项目根目录的 data/ 文件夹
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "data", "inventory.db")}'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# ── 安全配置 ──
# 用于加密 Session，必须是一个随机字符串
# 可以用 python -c "import secrets; print(secrets.token_hex(32))" 生成
SECRET_KEY = os.environ.get('SECRET_KEY', 'my-secret-key-change-in-production')

# ── 分页配置 ──
PER_PAGE = 20  # 每页显示多少条数据
