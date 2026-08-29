# models/brand.py
# 品牌-数据库表（可下拉选择）
from models import db

class Brand(db.Model):
    __tablename__ = 'brand'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True)

    def __repr__(self):
        return self.name
