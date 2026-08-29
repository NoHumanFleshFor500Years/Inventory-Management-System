# models/exchange_record.py
# 换货记录模型

from models import db
from datetime import datetime

class ExchangeRecord(db.Model):
    __tablename__ = 'exchange_record'

    id = db.Column(db.Integer, primary_key=True)
    old_sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    new_sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=True)
    
    old_product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    new_product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    
    old_serial = db.Column(db.String(100), nullable=False)
    new_serial = db.Column(db.String(100), nullable=False)
    
    old_price = db.Column(db.Float, nullable=False)
    new_price = db.Column(db.Float, nullable=False)
    price_diff = db.Column(db.Float, default=0)
    
    exchange_date = db.Column(db.DateTime, default=datetime.utcnow)
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    
    old_sale = db.relationship('Sales', foreign_keys=[old_sale_id])
    new_sale = db.relationship('Sales', foreign_keys=[new_sale_id])
    old_product = db.relationship('Product', foreign_keys=[old_product_id])
    new_product = db.relationship('Product', foreign_keys=[new_product_id])
    operator = db.relationship('User')
