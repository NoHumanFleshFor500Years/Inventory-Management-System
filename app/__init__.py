# app/__init__.py
# Flask 应用Web函数 - 创建并配置 Flask 应用

from flask import Flask
from models import db, User
from flask_login import LoginManager  # 导入 Flask-Login，用于用户登录管理
def create_app():  # 应用Web模式，Flask 推荐的做法
    """
        应用Web函数
        每次调用都会创建一个新的 Flask 应用实例
        方便测试和多环境配置
        """
    # 指定模板文件夹路径（相对于项目根目录）
    app = Flask(__name__, template_folder='../templates')
    app.config.from_object('config')  # 从 config.py 读取配置

    # 设置密钥，用于 Session（保存登录状态、提示信息等）
    # 需要是一个随机字符串，每次启动都一样
    app.secret_key = 'your-secret-key-here-change-in-production'

    # 初始化数据库，把 db 和 app 关联起来
    db.init_app(app)

    # ── 初始化 Flask-Login ──

    # LoginManager 是 Flask-Login 的核心对象
    # login_view: 指定登录页面的路由，未登录时会被重定向到这里
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'  # 登录页面路由是 /login
    login_manager.login_message = '请先登录再访问'  # 登录提示消息（中文）
    login_manager.exempt_view = 'admin_setup'  # 跳过登录检查的路由

    # 这个回调函数告诉 Flask-Login 如何从数据库加载用户
    # session_id 就是用户的 username
    @login_manager.user_loader
    def load_user(session_id):
        """
        根据用户名从数据库加载用户对象
        Flask-Login 在每次请求时调用这个函数来恢复登录状态
        """
        return User.query.filter_by(id=session_id).first()

    # ── 创建数据库表 ──

    # 导入模型（避免循环导入）
    from models.product import Product
    from models.purchase import Purchase
    from models.sales import Sales
    from models.user import User

    # 在应用上下文中创建所有表
    with app.app_context():
        db.create_all()  # 如果表不存在自动创建所有数据库表

    # ── 注册路由 ──

    # 暂时不导入路由，后续步骤再添加
    from app.routes import register_routes
    register_routes(app)

    return app
