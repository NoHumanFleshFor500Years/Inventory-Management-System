# models/product.py
# 商品模型 - 定义数据库中 product 表的结构

import json
from models import db
from datetime import datetime

# 定义了一个商品类，继承自 db.Model

# models/product.py
# 商品模型 - 定义数据库中 product 表的结构

import json
from models import db
from datetime import datetime

class Product(db.Model):
    """
       商品类 - 对应数据库中的 product 表
       用于存储手机/电脑的商品信息
       """
    __tablename__ = 'product'

    # ── 字段定义 ──

    # id: 主键，自增ID，用来唯一标识每个商品
    id = db.Column(db.Integer, primary_key=True)

    # name: 商品名称，如 "iPhone 15 Pro"，不能为空
    name = db.Column(db.String(100), nullable=False)

    # category: 商品类别，如 "phone"、"laptop"、"tablet"
    category = db.Column(db.String(50), nullable=False)

    # brand: 品牌，如 "Apple"、"Huawei"
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=True)
    brand = db.relationship('Brand')

    # sku: 货号，唯一标识，不能重复，如 "APL-IP15P-256"
    sku = db.Column(db.String(50), unique=True, nullable=False)

    # cost_price: 采购成本价（元），默认0
    cost_price = db.Column(db.Float, nullable=False, default=0)

    # sell_price: 销售售价（元），默认0
    sell_price = db.Column(db.Float, nullable=False, default=0)

    # stock: 当前库存数量，默认0
    stock = db.Column(db.Integer, nullable=False, default=0)

    # low_stock_threshold: 低库存预警阈值，默认5件
    low_stock_threshold = db.Column(db.Integer, nullable=False, default=5)

    # created_at: 创建时间，默认当前时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # custom_fields: 自定义属性（JSON格式），如序列号、内存容量等
    custom_fields = db.Column(db.Text, nullable=True)

    # ── 辅助方法 ──

    def get_custom_field(self, key):
        """获取某个自定义属性的值"""
        if not self.custom_fields:
            return None
        fields = json.loads(self.custom_fields)
        return fields.get(key)

    def set_custom_field(self, key, value):
        """设置单个自定义属性"""
        if not self.custom_fields:
            self.custom_fields = '{}'
        fields = json.loads(self.custom_fields)
        fields[key] = value
        self.custom_fields = json.dumps(fields, ensure_ascii=False)

    def get_all_custom_fields(self):
        """获取所有自定义属性"""
        if not self.custom_fields:
            return {}
        return json.loads(self.custom_fields)

    def to_dict(self):
        """将商品对象转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'brand': self.brand,
            'sku': self.sku,
            'cost_price': self.cost_price,
            'sell_price': self.sell_price,
            'stock': self.stock,
            'low_stock_threshold': self.low_stock_threshold,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'custom_fields': self.get_all_custom_fields()  # ← 添加这一行
        }

    """ 以上是新方案2026.8.26改，以下是旧方案 """

# class Product(db.Model):
#     """
#        商品类 - 对应数据库中的 product 表
#        用于存储手机/电脑的商品信息
#        """
#     __tablename__ = 'product'
#
#     # ── 字段定义 ──
#
#     # id: 主键，自增ID，用来唯一标识每个商品
#     id = db.Column(db.Integer, primary_key=True)
#
#     # name: 商品名称，如 "iPhone 15 Pro"，不能为空
#     name = db.Column(db.String(100), nullable=False)
#
#     # category: 商品类别，如 "phone"、"laptop"、"tablet"
#     category = db.Column(db.String(50), nullable=False)
#
#     # brand: 品牌，如 "Apple"、"Huawei"
#     brand = db.Column(db.String(50), nullable=False)
#
#     # sku: 货号，唯一标识，不能重复，如 "APL-IP15P-256"
#     sku = db.Column(db.String(50), unique=True, nullable=False)
#
#     # cost_price: 采购成本价（元），默认0
#     cost_price = db.Column(db.Float, nullable=False, default=0)
#
#     # sell_price: 销售售价（元），默认0
#     sell_price = db.Column(db.Float, nullable=False, default=0)
#
#     # stock: 当前库存数量，默认0
#     stock = db.Column(db.Integer, nullable=False, default=0)
#
#     # low_stock_threshold: 低库存预警阈值，默认5件
#     # 当库存低于这个值时，系统会显示预警
#     low_stock_threshold = db.Column(db.Integer, nullable=False, default=5)
#
#     # created_at: 创建时间，默认当前时间
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#
#     #  db.Column()定义数据库列，每个参数说明字段的类型和约束
#
#     # ── 方法定义 ──
#
#     def to_dict(self):  #  把对象转成字典，方便前端显示
#         """
#         将商品对象转换为字典格式
#         方便在前端页面显示和API接口返回数据
#         """
#         return {
#             'id': self.id,                      # 商品ID
#             'name': self.name,                  # 商品名称
#             'category': self.category,          # 类别
#             'brand': self.brand,                # 品牌
#             'sku': self.sku,                    # 货号
#             'cost_price': self.cost_price,      # 成本价
#             'sell_price': self.sell_price,      # 售价
#             'stock': self.stock,                # 库存
#             'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,  # 创建时间
#             'stock': self.stock,
#             'low_stock_threshold': self.low_stock_threshold,
#             'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None  # 创建时间
#         }