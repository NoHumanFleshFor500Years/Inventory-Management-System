# models/attribute_template.py
# 商品属性模板模型
from models import db


class AttributeTemplate(db.Model):
    __tablename__ = 'product_attribute_template'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    fields = db.Column(db.Text)  # JSON格式的字段列表
    created_by = db.Column(db.Integer)

    def __repr__(self):
        return f'<AttributeTemplate {self.name}>'