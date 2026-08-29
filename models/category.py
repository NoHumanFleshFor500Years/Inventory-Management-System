# models/category.py
# 商品类别模型 - 定义数据库中 category 表的结构

from models import db

class Category(db.Model):
    """
       商品类别类 - 对应数据库中的 category 表
       用于管理商品的分类信息，支持自定义添加
       """
    __tablename__ = 'category'

    # ── 字段定义 ──

    # id: 主键，自增ID
    id = db.Column(db.Integer, primary_key=True)

    # name: 类别中文名称，如 "手机"、"DIY配件"
    name = db.Column(db.String(50), nullable=False)

    # slug: 类别英文标识，如 "phone"、"diy_accessory"
    # 用于数据库查询，唯一且不能重复
    slug = db.Column(db.String(50), unique=True, nullable=False)

    # 添加二级分类支持
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    parent = db.relationship('Category', remote_side=[id], backref='children')

    # ── 方法定义 ──

    def __repr__(self):
        """
        返回类别的字符串表示
        用于调试和日志输出
        """
        return f'<Category {self.name}>'