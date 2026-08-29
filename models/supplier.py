# models/supplier.py
# 供应商-数据库表（可下拉选择）

from models import db

class Supplier(db.Model):
    __tablename__ = 'supplier'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=True)
    parent = db.relationship('Supplier', remote_side=[id], backref='children')

    def __repr__(self):
        return self.name