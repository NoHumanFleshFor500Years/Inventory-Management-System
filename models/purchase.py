# models/purchase.py
# 采购入库模型 - 记录每次进货信息

from models import db
from datetime import datetime

class Purchase(db.Model):
    """
        采购类 - 对应数据库中的 Purchase 表
        记录每次采购入库的信息
        """
    __tablename__ = 'purchase'

    # ── 字段定义 ──

    # id：主键，自增ID
    id = db.Column(db.Integer, primary_key=True)

    # product_id: 关联的商品ID，外键
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

    # quantity: 采购数量
    quantity = db.Column(db.Integer, nullable=False)

    # unit_cost: 采购单价（元）
    unit_cost = db.Column(db.Float, nullable=False)

    # total_cost: 总价 = 数量 × 单价
    total_cost = db.Column(db.Float, nullable=False)

    # supplier: 供应商名称
    # supplier: 供应商名称（文本）
    supplier = db.Column(db.String(100), nullable=True)
    # supplier_id: 供应商ID（外键）
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=True)

    # purchase_date: 采购日期
    purchase_date = db.Column(db.Date, nullable=False)

    # created_at: 记录创建时间
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # 操作员ID（记录是谁入库的）
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # serial_numbers: 序列号列表（JSON格式）
    # 例如入库10条内存，可以记录 ["SN001", "SN002", ..., "SN010"]
    serial_numbers = db.Column(db.Text, nullable=True)

    # ── 关系定义 ──

    # 关联到 Product 表，方便查询商品信息
    product = db.relationship('Product', backref='purchases')
    # 建立两个表之间的关系，可以通过 purchase.product 直接获取商品信息
    # 表示可以在 Product 对象上用 .purchases 反向查询采购记录

    # 关联到 User 表，获取操作员信息
    operator = db.relationship('User', foreign_keys=[operator_id])

    def to_dict(self):
        """ 转字典，方便前端显示 """
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None ,  # 商品名称
            'quantity': self.quantity,
            'unit_cost': self.unit_cost,
            'total_cost': self.total_cost,
            'supplier': self.supplier,
            'purchase_date': self.purchase_date.strftime('%Y-%m-%d') if self.purchase_date else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'serial_numbers': self.serial_numbers,
            'supplier': self.supplier.name if self.supplier else None
        }







