# models/__init__.py
# models 包的初始化文件

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.product import Product
from models.purchase import Purchase
from models.sales import Sales
from models.user import User
from models.category import Category
from models.return_record import ReturnRecord
from models.exchange_record import ExchangeRecord
from models.brand import Brand
from models.attribute_template import AttributeTemplate
from models.supplier import Supplier
__all__ = ['db', 'Product', 'Purchase', 'Sales', 'User', 'category']
