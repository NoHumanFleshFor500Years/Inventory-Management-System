# models/return.py
# 退货记录模型

from models import db
from datetime import datetime

class Return(db.Model):
    """
    退货记录表
    记录每次退货的详细信息
    """
    __tablename__ = 'return_record'

    id = db.Column(db.Integer, primary_key=True)  # 退货ID
    sales_id = db.Column(db.Integer, db.ForeignKey('sales.id'))  # 关联的销售记录ID
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))  # 关联的商品ID
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'))  # 操作员ID

    # 退货序列号（从销售记录中退回来的）
    return_serial = db.Column(db.String(100), nullable=True)

    # 退货原因
    reason = db.Column(db.Text, nullable=True)

    # 退货数量
    quantity = db.Column(db.Integer, default=1)

    # 退货金额（按销售时的价格）
    refund_amount = db.Column(db.Float, default=0)

    # 退货日期
    return_date = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联关系
    sales = db.relationship('Sale', backref='return')
    product = db.relationship('Product')
    operator = db.relationship('User')

    def __repr__(self):
        return f'<Return {self.id}>'