# models/user.py
# 用户模型 - 定义用户登录相关的数据表

from models import db  # 导入数据库对象
from flask_login import UserMixin  # 导入UserMixin，让模型自动具备登录所需的方法

class User(db.Model, UserMixin):
    """
        用户类 - 对应数据库中的 user 表
        UserMixin 让它自动拥有 is_authenticated、is_active 等属性
        Flask-Login 用这些属性判断用户是否已登录
        """
    __tablename__ = 'user'

    # ── 字段定义 ──

    # id: 主键，自增ID
    id = db.Column(db.Integer, primary_key=True)

    # username: 用户名，唯一且不能为空，用来登录
    username = db.Column(db.String(50), unique=True, nullable=False)

    # password_hash: 密码的哈希值（加密后的，不是明文！）
    # 这样即使数据库泄露，攻击者也拿不到真实密码
    password_hash = db.Column(db.String(128), nullable=False)

    # role: 用户角色
    # 'admin' = 管理员（所有权限）
    # 'warehouse' = 仓管（入库、出库、调拨）
    # 'sales' = 销售员（只能销售、退货）
    role = db.Column(db.String(20), nullable=False, default='sales')

    # created_at: 创建时间
    created_at = db.Column(db.DateTime, default=db.func.now())

    # ── 方法定义 ──

    def set_password(self, password):
        """
        设置密码 - 将明文密码加密后存储
        generate_password_hash 是 Werkzeug 提供的安全哈希函数
        用的是 PBKDF2-SHA256 算法，不可逆
        """
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        验证密码 - 用传入的明文密码与存储的哈希值比对
        check_password_hash 会解密哈希然后比对，返回 True/False
        """
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """将用户对象转为字典（不包含密码）"""
        return {
            'id': self.id,
            'username': self.username,
            'is_admin': self.is_admin,
            'role': self.role,
        }
