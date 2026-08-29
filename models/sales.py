# models/sales.py
from models import db
from datetime import datetime

class Sales(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    customer = db.Column(db.String(100), nullable=False)
    sales_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sales_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    serial_numbers = db.Column(db.Text, nullable=True)
    product = db.relationship('Product', backref='sales_records')
    sales_user = db.relationship('User', foreign_keys=[sales_user_id])
