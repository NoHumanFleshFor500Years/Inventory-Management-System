# app/routes.py
# 路由定义文件 - 处理所有页面请求

from flask import render_template, request, redirect, url_for, flash, session, jsonify
import json
from models import db
from models.product import Product
from models.purchase import Purchase
from models.sales import Sales
from models.user import User  # 导入用户模型
from datetime import date, datetime
from flask_login import login_user, logout_user, login_required, current_user  # Flask-Login 核心函数
from functools import wraps  # Python 装饰器工具
from flask import abort  # 用于返回 403 错误
from models.category import Category
from models.brand import Brand
from sqlalchemy.exc import IntegrityError
from models.return_record import ReturnRecord
from models.exchange_record import ExchangeRecord
from models.attribute_template import AttributeTemplate
from models.supplier import Supplier
from collections import defaultdict

# ── 权限装饰器 ──
def role_required(*roles):
    """
   角色权限装饰器
   用法：@role_required('admin', 'warehouse')
   只有角色匹配的用户才能访问该页面
   """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 如果用户未登录，跳转到登录页
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            # 检查用户角色是否在允许的列表中
            if current_user.role not in roles:
                # 权限不足，返回403错误
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_available_serials(product_id):
    """获取某商品当前可用的序列号（在库未售出的）"""
    import json
    purchases = Purchase.query.filter_by(product_id=product_id).all()
    all_serials = []
    for p in purchases:
        if p.serial_numbers:
            try:
                all_serials.extend(json.loads(p.serial_numbers))
            except:
                pass
    sold = Sales.query.filter_by(product_id=product_id).all()
    sold_serials = []
    for s in sold:
        if s.serial_numbers:
            try:
                sold_serials.extend(json.loads(s.serial_numbers))
            except:
                pass
    return [sn for sn in all_serials if sn not in sold_serials]

def register_routes(app):
    """
    注册所有路由到 Flask 应用
    把路由函数绑定到 app 对象上
    """
    # ── 403 错误处理 ──

    @app.errorhandler(403)
    def forbidden(e):
        """权限不足时显示友好页面"""
        return render_template('403.html'), 403

    # ── 登录页面 ──

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """
        登录页面
        GET: 显示登录表单
        POST: 处理登录请求
        """
        # 如果用户已经登录了，直接跳到首页
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        # 检查是否已有用户，如果没有就跳到管理员设置页
        if User.query.first() is None:
            return redirect(url_for('admin_setup'))

        # 如果是 POST 请求（表单提交）
        if request.method == 'POST':
            username = request.form.get('username')  # 获取用户名
            password = request.form.get('password')  # 获取密码

            # 从数据库查找该用户
            user = User.query.filter_by(username=username).first()

            # 检查用户是否存在且密码是否正确
            if user and user.check_password(password):
                # 登录成功：把用户信息存入 Session
                # remember=True 表示"记住我"，7天内免登录
                login_user(user, remember=True)
                flash('登录成功！欢迎回来', 'success')
                if user.role == 'sales':
                    return redirect(url_for('sales_serial'))
                return redirect(url_for('index'))
            else:
                # 登录失败
                flash('用户名或密码错误！', 'error')

        # 渲染登录页面
        return render_template('login.html')

    # ── 退出登录 ──

    @app.route('/logout')
    @login_required  # 必须登录才能访问
    def logout():
        """
        退出登录
        清除 Session 中的用户信息
        """
        logout_user()  # 调用 Flask-Login 的退出函数
        flash('已退出登录', 'info')
        return redirect(url_for('login'))  # 跳回登录页

    # ── 管理员设置（首次创建管理员账号） ──

    @app.route('/admin/setup', methods=['GET', 'POST'])
    def admin_setup():
        """
        首次设置管理员账号
        GET: 显示设置表单
        POST: 创建管理员账号
        注意：只有数据库中没有用户时才能访问此页面
        """
        # 检查是否已有用户存在
        if User.query.first() is not None:
            flash('管理员账号已存在，无法重复创建！', 'error')
            return redirect(url_for('login'))

        # 如果是 POST 请求（表单提交）
        if request.method == 'POST':
            username = request.form.get('username')  # 获取用户名
            password = request.form.get('password')  # 获取密码

            # 验证输入不为空
            if not username or not password:
                flash('用户名和密码不能为空！', 'error')
                return render_template('admin_setup.html')

            # 创建新用户
            user = User(username=username, role='admin')
            # 用 set_password 加密密码后存储
            user.set_password(password)
            # 保存到数据库
            db.session.add(user)
            db.session.commit()

            flash('管理员账号创建成功！请登录', 'success')
            return redirect(url_for('login'))

        # 渲染管理员设置页面
        return render_template('admin_setup.html')

    # ── 首页：显示所有商品 ──

    @app.route('/')
    @login_required  # 必须登录才能访问首页
    def index():
        """
        首页路由：显示商品列表
        支持按类别筛选和关键词搜索
        """
        # 获取搜索关键词
        keyword = request.args.get('keyword', '')

        # 获取类别筛选
        category = request.args.get('category', '')

        # 获取预警筛选参数
        show_low_stock = request.args.get('low_stock') == '1'

        # 构建查询
        query = db.session.query(Product)

        # 如果只显示预警商品
        if show_low_stock:
            query = query.filter(Product.stock < Product.low_stock_threshold)

        # 计算库存预警数量（用于首页显示提醒）
        low_stock_count = Product.query.filter(Product.stock < Product.low_stock_threshold).count()

        low_stock = request.args.get('low_stock')
        if low_stock == '1':
            query = query.filter(Product.stock < Product.low_stock_threshold)

        # 如果有搜索关键词，模糊匹配名称、品牌、货号
        if keyword:
            query = query.filter(
                db.or_(
                    Product.name.like(f'%{keyword}%'),
                    Product.brand.like(f'%{keyword}%'),
                    Product.sku.like(f'%{keyword}%')
                )
            )
        # 如果有类别筛选，只查该类别
        if category:
            query = query.filter(Product.category == category)

        # 执行查询，获取所有商品
        products = query.order_by(Product.id.desc()).all()

        # ── 查询所有类别（用于前端显示中文名称）──
        # 从 category 表中取出所有类别
        categories = Category.query.all()

        # 把 slug（英文标识）映射到 name（中文名）的字典
        # 例如：{'phone': '手机', 'diy_accessory': 'DIY配件'}
        category_map = {cat.slug: cat.name for cat in categories}

        # ── 给每个商品准备可用序列号列表 ──
        # ── 给每个商品准备可用序列号列表 ──
        import json as _json
        serial_data = {}
        # 一次性批量查询所有采购
        all_purchases = Purchase.query.all()
        purchase_serials = defaultdict(list)
        for pr in all_purchases:
            if pr.serial_numbers:
                try:
                    purchase_serials[pr.product_id].extend(_json.loads(pr.serial_numbers))
                except Exception:
                    pass
        # 一次性批量查询所有销售
        all_sales = Sales.query.all()
        sales_serials = defaultdict(list)
        for s in all_sales:
            if s.serial_numbers:
                try:
                    sales_serials[s.product_id].extend(_json.loads(s.serial_numbers))
                except Exception:
                    pass
        for p in products:
            available = purchase_serials.get(p.id, [])
            sold = set(sales_serials.get(p.id, []))
            serial_data[p.id] = [sn for sn in available if sn not in sold]
            p.available_serials = serial_data[p.id]

        # 渲染模板时，额外传递 categories 和 category_map
        return render_template('index.html',
                               products=products,
                               low_stock_count=low_stock_count,
                               categories=categories,
                               category_map=category_map,
                               brands=Brand.query.all(),
                               serial_data=serial_data,
                               templates=AttributeTemplate.query.all(),
                               suppliers=Supplier.query.all())


        # ── 销售序列号选择页面 ──

    @app.route('/sales')
    @login_required
    @role_required('admin', 'sales', 'warehouse')  # 所有角色都能访问
    def sales_serial():
        """
        销售开单页面 - 支持选择具体序列号
        """
        # 获取搜索参数
        keyword = request.args.get('keyword', '')
        category = request.args.get('category', '')

        # 构建查询
        query = db.session.query(Product)

        # 按关键词搜索
        if keyword:
            query = query.filter(
                db.or_(
                    Product.name.like(f'%{keyword}%'),
                    Product.brand.like(f'%{keyword}%'),
                    Product.sku.like(f'%{keyword}%')
                )
            )

        # 按类别筛选
        if category:
            query = query.filter(Product.category == category)

        # 获取所有商品
        products = query.order_by(Product.id.desc()).all()

        # 准备类别映射
        categories = Category.query.all()
        category_map = {cat.slug: cat.name for cat in categories}

        # ── 给每个商品准备可用序列号列表 ──
        import json as _json
        serial_data = {}
        # 一次性批量查询所有采购
        all_purchases = Purchase.query.all()
        purchase_serials = defaultdict(list)
        for pr in all_purchases:
            if pr.serial_numbers:
                try:
                    purchase_serials[pr.product_id].extend(_json.loads(pr.serial_numbers))
                except Exception:
                    pass
        # 一次性批量查询所有销售
        all_sales = Sales.query.all()
        sales_serials = defaultdict(list)
        for s in all_sales:
            if s.serial_numbers:
                try:
                    sales_serials[s.product_id].extend(_json.loads(s.serial_numbers))
                except Exception:
                    pass
        for p in products:
            available = purchase_serials.get(p.id, [])
            sold = set(sales_serials.get(p.id, []))
            serial_data[p.id] = [sn for sn in available if sn not in sold]
            p.available_serials = serial_data[p.id]

        return render_template('sales_serial.html',
                               products=products,
                               categories=categories,
                               category_map=category_map,
                               serial_data=serial_data,
                               product_prices={p.id: p.sell_price for p in products})

    # ── 我的销售记录（销售员专用）──

    @app.route('/sales/my')
    @login_required
    @role_required('sales', 'warehouse', 'admin')  # 管理员也能看
    def my_sales():
        """
        查看销售记录
        - 销售员：只看自己的所有记录
        - 仓管/管理员：看所有记录，可通过 ?view=all 查看
        """
        from datetime import date

        # 获取查看模式：默认看自己的，管理员/仓管可以传 ?view=all 看全部
        view_mode = request.args.get('view', 'mine')  # 'mine' 或 'all'

        # 如果是仓管/管理员且请求查看全部
        if current_user.role in ['admin', 'warehouse'] and view_mode == 'all':
            sales_list = Sales.query.order_by(Sales.sales_date.desc()).all()
            today_revenue = sum(s.total_price for s in sales_list if s.sales_date == date.today())
        else:
            # 销售员只看自己的，或默认模式
            sales_list = Sales.query.filter_by(sales_user_id=current_user.id) \
                .order_by(Sales.sales_date.desc()).all()
            today_revenue = sum(s.total_price for s in sales_list if s.sales_date == date.today())

        return render_template('sales_my.html',
                               sales=sales_list,
                               today_revenue=today_revenue,
                               view_mode=view_mode)

    # ── 销售员查看自己的退货记录 ──

    @app.route('/sales/my_returns')
    @login_required
    @role_required('sales', 'warehouse', 'admin')
    def my_returns():
        """销售员查看自己的退货记录"""
        returns = ReturnRecord.query.filter_by(operator_id=current_user.id) \
            .order_by(ReturnRecord.return_date.desc()).all()
        total_refund = sum(float(r.refund_amount or 0) for r in returns)
        return render_template('sales_my.html',
                               returns=returns,
                               total_refund=total_refund,
                               tab='returns')

    # ── 销售员查看自己的换货记录 ──

    @app.route('/sales/my_exchanges')
    @login_required
    @role_required('sales', 'warehouse', 'admin')
    def my_exchanges():
        """销售员查看自己的换货记录"""
        exchanges = ExchangeRecord.query.filter_by(operator_id=current_user.id) \
            .order_by(ExchangeRecord.exchange_date.desc()).all()
        total_diff = sum(float(e.price_diff or 0) for e in exchanges if e.price_diff > 0)
        return render_template('sales_my.html',
                               exchanges=exchanges,
                               total_diff=total_diff,
                               tab='exchanges')

    

    @app.route('/purchase')
    @login_required
    @role_required('warehouse', 'admin')  # 只有仓管和管理员能看
    def purchase():
        """
        采购记录页面
        显示所有入库记录
        """
        # 查询所有采购记录（按时间倒序）
        purchases = Purchase.query.order_by(Purchase.purchase_date.desc()).all()

        # 计算总采购金额
        total_cost = sum(p.total_cost for p in purchases)

        return render_template('purchase.html',
                               purchases=purchases,
                               total_cost=total_cost)

    # ── 获取商品自定义属性 API（供入库表单联动）──
    @app.route('/product/custom_fields/<int:product_id>')
    @login_required
    def get_product_custom_fields(product_id):
        """返回商品的自定义属性，供入库/销售表单使用"""
        product = Product.query.get_or_404(product_id)
        custom_fields = {}
        if product.custom_fields:
            try:
                custom_fields = json.loads(product.custom_fields)
            except:
                pass
        return jsonify(custom_fields)

    # ── 采购入库 ──

    @app.route('/purchase/add', methods=['POST'])
    @login_required  # 必须登录才能入库
    @role_required('warehouse')  # 只有仓管能入库
    def add_purchase():
        """
        处理采购入库表单提交
        增加商品库存数量
        """
        product_id = int(request.form.get('product_id'))
        quantity = int(request.form.get('quantity'))
        unit_cost = float(request.form.get('unit_cost'))
        supplier_id = request.form.get('supplier_id')
        supplier = Supplier.query.get(int(supplier_id)) if supplier_id else None

        # ── 新增：获取并保存序列号 ──
        serial_numbers_str = request.form.get('serial_numbers', '')
        serial_numbers = None
        if serial_numbers_str:
            # 把逗号分隔的字符串转成列表，例如 "SN001,SN002,SN003" -> ["SN001", "SN002", "SN003"]
            serial_numbers = json.dumps([s.strip() for s in serial_numbers_str.replace('，', ',').split(',') if s.strip()],
                                        ensure_ascii=False)

        # 查询商品
        product = Product.query.get_or_404(product_id)

        # ── 获取自定义属性 ──
        custom_fields = {}
        for key, value in request.form.items():
            if key.startswith('cf_'):
                field_name = key.replace('cf_', '')
                if value:
                    custom_fields[field_name] = value

        # 保存自定义属性到商品的 custom_fields 字段（覆盖更新）
        if custom_fields and product:
            product.custom_fields = json.dumps(custom_fields, ensure_ascii=False)

        # 创建采购记录
        purchase = Purchase(
            product_id=product_id,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=quantity * unit_cost,
            supplier_id=supplier.id if supplier else None,
            purchase_date=date.today(),
            operator_id=current_user.id,
            serial_numbers=serial_numbers
        )

        # 更新商品库存
        product.stock += quantity
        # 如果成本价为0，更新为本次采购成本
        product.cost_price = unit_cost

        # 保存
        db.session.add(purchase)
        db.session.commit()

        flash('采购入库成功！', 'success')
        return redirect(url_for('index'))

    # ── 销售出库 ──

    @app.route('/sales/add', methods=['POST'])
    @login_required  # 必须登录才能出库
    @role_required('sales', 'warehouse')  # 销售员和仓管能出库
    def add_sales():
        """
        处理销售出库表单提交
        减少商品库存数量
        """
        product_id = int(request.form.get('product_id'))
        quantity = int(request.form.get('quantity'))
        unit_price = float(request.form.get('unit_price'))
        customer = request.form.get('customer')

        # 查询商品
        product = Product.query.get_or_404(product_id)

        # 检查库存是否足够
        if product.stock < quantity:
            flash(f'库存不足！当前库存: {product.stock}', 'error')
            return redirect(url_for('index'))

        # 获取序列号
        serial_numbers_str = request.form.get('serial_numbers', '').strip()
        quantity = int(request.form.get('quantity', 1))
        # 如果用户选了序列号，用选的；否则自动从库存分配
        if serial_numbers_str:
            serial_numbers = json.dumps([s.strip() for s in serial_numbers_str.split(',') if s.strip()],
                                        ensure_ascii=False)
        else:
            # 自动分配：按采购时间顺序取最早的序列号（FIFO）
            purchases = Purchase.query.filter_by(product_id=product_id) \
                .order_by(Purchase.purchase_date.asc()).all()
            all_serials = []
            for pr in purchases:
                if pr.serial_numbers:
                    try:
                        all_serials.extend(json.loads(pr.serial_numbers))
                    except:
                        pass
            # 减去已销售的
            sold = Sales.query.filter_by(product_id=product_id).all()
            sold_sn = []
            for s in sold:
                if s.serial_numbers:
                    try:
                        sold_sn.extend(json.loads(s.serial_numbers))
                    except:
                        pass
            available = [sn for sn in all_serials if sn not in sold_sn]
            # 取需要的数量
            needed = available[:quantity]
            if len(needed) < quantity:
                flash(f'库存不足！该商品只有 {len(available)} 个可用序列号', 'error')
                return redirect(url_for('index'))
            serial_numbers = json.dumps(needed, ensure_ascii=False)

        # 创建销售记录
        sales = Sales(
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            total_price=quantity * unit_price,
            customer=customer,
            sales_date=date.today(),
            sales_user_id=current_user.id,
            serial_numbers=serial_numbers
        )

        # 更新商品库存
        product.stock -= quantity

        # 保存
        db.session.add(sales)
        db.session.commit()

        flash('销售出库成功！', 'success')
        return redirect(url_for('sales_serial'))

    # ── 打印销售小票 ──

    @app.route('/sales/receipt/<int:sale_id>')
    @login_required
    def sales_receipt(sale_id):
        """
        打印销售小票
        生成小票页面，支持热敏打印机和针式打印机两种格式
        """
        # 查询销售记录
        sale = Sales.query.get_or_404(sale_id)

        # 销售员只能打印自己的销售记录
        if current_user.role == 'sales' and sale.sales_user_id != current_user.id:
            abort(403)

        return render_template('sales_receipt.html', sale=sale)

    # ── 删除商品 ──

    @app.route('/product/delete/<int:product_id>', methods=['POST'])
    @login_required  # 必须登录才能删除
    @role_required('admin')  # 只有管理员能删除
    def delete_product(product_id):
        """删除商品及其关联记录"""
        product = Product.query.get_or_404(product_id)

        # 先删除关联的采购和销售记录
        Purchase.query.filter_by(product_id=product_id).delete()
        Sales.query.filter_by(product_id=product_id).delete()

        # 删除商品
        db.session.delete(product)
        db.session.commit()

        flash('商品已删除！', 'success')
        return redirect(url_for('index'))

    # ── 统计报表 ──

    @app.route('/report')
    @login_required
    @role_required('admin', 'warehouse', 'sales')
    def report():
        """统计报表 - 正确计算利润"""
        from collections import defaultdict

        # 获取所有销售记录
        all_sales = Sales.query.all()

        # 获取换货记录 - 旧销售和新销售都要排除
        exchanges = ExchangeRecord.query.all()
        exchange_old_ids = {e.old_sale_id for e in exchanges if e.old_sale_id}
        exchange_new_ids = {e.new_sale_id for e in exchanges if e.new_sale_id}

        # 按销售ID分组退货信息
        return_by_sale = defaultdict(list)
        for r in ReturnRecord.query.all():
            if r.sales_id:
                return_by_sale[r.sales_id].append(r)

        # 计算每个产品的净销售和退款
        product_stats = defaultdict(lambda: dict(qty=0, revenue=0))
        for s in all_sales:
            # 排除换货旧销售 和 换货新销售
            if s.id in exchange_old_ids or s.id in exchange_new_ids:
                continue

            # 检查是否完全退货（退款 >= 销售金额）
            returns = return_by_sale.get(s.id, [])
            total_refund = sum(r.refund_amount for r in returns if r.refund_amount)
            if total_refund >= s.total_price:
                continue  # 完全退货，排除

            # 部分退货：减去退款，保留有效销售额
            net_rev = s.total_price - total_refund
            product_stats[s.product_id]["qty"] += s.quantity
            product_stats[s.product_id]["revenue"] += net_rev

        # 统计所有商品
        all_products = Product.query.all()
        stats = []
        net_qty_list = []
        net_revenue_by_product = {}
        net_cost_by_product = {}

        for p in all_products:
            ps = product_stats.get(p.id, dict(qty=0, revenue=0))
            qty = ps["qty"]
            rev = ps["revenue"]
            cost = qty * p.cost_price
            profit = rev - cost
            stats.append(type("Stat", (), dict(
                id=p.id, name=p.name, brand=p.brand,
                total_qty=qty, total_revenue=rev,
                total_cost=cost, profit=profit
            ))())
            net_qty_list.append(qty)
            net_revenue_by_product[p.id] = rev
            net_cost_by_product[p.id] = cost

        total_revenue = sum(nr for nr in net_revenue_by_product.values())
        total_cost = sum(nc for nc in net_cost_by_product.values())
        total_profit = total_revenue - total_cost

        return render_template("report.html",
                               stats=stats,
                               net_qty_list=net_qty_list,
                               total_revenue=total_revenue,
                               total_cost=total_cost,
                               total_profit=total_profit,
                               net_revenue_by_product=net_revenue_by_product,
                               net_cost_by_product=net_cost_by_product)


    @app.route('/product/<int:product_id>')
    @login_required  # 必须登录才能查看
    def product(product_id):
        """
        商品详情页
        显示商品的完整信息：基本信息、采购记录、销售记录
        """
        # 查询商品
        product = Product.query.get_or_404(product_id)

        # 查询该商品的所有采购记录（按时间倒序）
        purchases = Purchase.query.filter_by(product_id=product_id) \
            .order_by(Purchase.purchase_date.desc()).all()

        # 查询该商品的所有销售记录（按时间倒序）
        sales = Sales.query.filter_by(product_id=product_id) \
            .order_by(Sales.sales_date.desc()).all()

        # ── 预处理采购记录的序列号，转成列表方便模板显示 ──
        import json as json_module
        for p in purchases:
            if p.serial_numbers:
                try:
                    p.serial_list = json_module.loads(p.serial_numbers)
                except:
                    p.serial_list = []
            else:
                p.serial_list = []

        # 同样处理销售记录
        for s in sales:
            if s.serial_numbers:
                try:
                    s.serial_list = json_module.loads(s.serial_numbers)
                except:
                    s.serial_list = []
            else:
                s.serial_list = []

        # 计算总采购量和总销售量
        total_purchase_qty = sum(p.quantity for p in purchases)
        total_sales_qty = sum(s.quantity for s in sales)


        # ── 准备类别映射（商品详情页也需要显示中文类别名）──
        categories = Category.query.all()
        category_map = {cat.slug: cat.name for cat in categories}

        return render_template('product_detail.html',
                               product=product,
                               purchases=purchases,
                               sales=sales,
                               total_purchase_qty=total_purchase_qty,
                               total_sales_qty=total_sales_qty,
                               category_map=category_map,
                               suppliers=Supplier.query.all())

    # ──自定义属性区域──

    @app.route('/product/add', methods=['POST'])
    @login_required
    @role_required('admin', 'warehouse')
    def add_product():
        # 读取参数
        name = request.form.get('name')
        category = request.form.get('category')
        brand_id = request.form.get('brand_id')  # 改为获取品牌ID
        sku = request.form.get('sku')
        cost_price = float(request.form.get('cost_price', 0))
        sell_price = float(request.form.get('sell_price', 0))

        # 读取所有自定义属性（名称以 field_ 开头）
        custom_fields = {}
        for key, value in request.form.items():
            if key.startswith('field_'):
                field_name = key.replace('field_', '')
                if value:
                    custom_fields[field_name] = value

        # 创建商品
        product = Product(
            name=name,
            category=category,
            brand_id=int(brand_id) if brand_id else None,  # 使用 brand_id
            sku=sku,
            cost_price=cost_price,
            sell_price=sell_price,
            stock=0
        )

        # 保存自定义属性
        if custom_fields:
            product.custom_fields = json.dumps(custom_fields, ensure_ascii=False)

        try:
            db.session.add(product)
            db.session.commit()
            flash('商品添加成功！', 'success')
            return redirect(url_for('index'))
        except IntegrityError:
            db.session.rollback()  # 回滚数据库
            flash(f'货号 "{sku}" 已存在！请换一个不重复的货号。', 'error')
            flash('货号已存在，请换一个不重复的货号。', 'error'); return redirect(url_for('index'))

    # ── 用户管理页面 ──

    @app.route('/admin/users')
    @role_required('admin')  # 只有管理员能管理用户
    def admin_users():
        """
        用户管理页面
        管理员可以创建新用户、修改角色
        """
        # 查询所有用户（不显示密码）
        users = User.query.all()
        return render_template('admin_users.html', users=users)

    # ── 创建用户 ──

    @app.route('/admin/user/create', methods=['GET', 'POST'])
    @role_required('admin')  # 只有管理员能创建用户
    def create_user():
        """
        创建新用户
        GET: 显示创建表单
        POST: 处理创建请求
        """
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')  # admin / warehouse / sales

            # 验证输入
            if not username or not password or not role:
                flash('请填写所有字段！', 'error')
                return redirect(url_for('create_user'))

            # 检查用户名是否已存在
            if User.query.filter_by(username=username).first():
                flash('用户名已存在！', 'error')
                return redirect(url_for('create_user'))

            # 创建新用户
            user = User(username=username, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash(f'用户 {username} 创建成功！角色：{role}', 'success')
            return redirect(url_for('admin_users'))

        return render_template('admin_create_user.html')

    # ── 修改用户角色 ──

    @app.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
    @role_required('admin')  # 只有管理员能编辑用户
    def edit_user(user_id):
        """
        修改用户角色
        """
        user = User.query.get_or_404(user_id)

        # 不能修改自己的角色（防止自己被踢出管理员）
        if user.id == current_user.id:
            flash('不能修改自己的角色！', 'error')
            return redirect(url_for('admin_users'))

        if request.method == 'POST':
            new_role = request.form.get('role')
            if new_role in ['admin', 'warehouse', 'sales']:
                user.role = new_role
                db.session.commit()
                flash(f'用户 {user.username} 角色已更新为：{new_role}', 'success')
            else:
                flash('无效的角色！', 'error')
            return redirect(url_for('admin_users'))

        return render_template('admin_edit_user.html', user=user)

    # ── 删除用户 ──

    @app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
    @role_required('admin')  # 只有管理员能删除用户
    def delete_user(user_id):
        """
        删除用户（不允许删除自己）
        """
        user = User.query.get_or_404(user_id)

        # 不能删除自己
        if user.id == current_user.id:
            flash('不能删除自己的账号！', 'error')
            return redirect(url_for('admin_users'))

        # 先删除该用户的采购和销售记录
        Purchase.query.filter_by(product_id=user_id).delete()
        Sales.query.filter_by(product_id=user_id).delete()

        # 删除用户
        db.session.delete(user)
        db.session.commit()

        flash(f'用户 {user.username} 已删除', 'success')
        return redirect(url_for('admin_users'))

    # ── 退货功能（销售退回）──

    @app.route('/return/add', methods=['POST'])
    @role_required('sales', 'warehouse')  # 销售员和仓管都能处理退货
    def add_return():
        """
        处理销售退货
        增加库存，记录退货信息
        """
        product_id = int(request.form.get('product_id'))
        quantity = int(request.form.get('quantity'))
        reason = request.form.get('reason', '客户退货')

        # 查询商品
        product = Product.query.get_or_404(product_id)

        # 增加库存
        product.stock += quantity

        # 创建退货记录（复用 Sales 表，用特殊标记区分）
        return_record = Sales(
            product_id=product_id,
            quantity=quantity,
            unit_price=0,  # 退货不产生收入
            total_price=0,
            customer=reason,
            sales_date=date.today(),
        )

        # 保存
        db.session.add(return_record)
        db.session.commit()

        flash(f'退货成功！{product.name} 入库 {quantity} 件', 'success')
        return redirect(url_for('index'))

    # ── 换货功能（销售换货）──

    @app.route('/exchange/submit', methods=['POST'])
    @login_required
    @role_required('admin', 'warehouse', 'sales')
    def submit_exchange():
        old_product_id = request.form.get('old_product_id', '').strip()
        new_product_id = request.form.get('new_product_id', '').strip()
        if not old_product_id or not new_product_id:
            flash('请先选择旧商品和新商品', 'error')
            return redirect(url_for('sales_serial'))
        old_product_id = int(old_product_id)
        new_product_id = int(new_product_id)
        old_serial = request.form.get('old_serial', '').strip()
        new_serial = request.form.get('new_serial', '').strip()
        reason = request.form.get('reason', '')

        if not old_serial or not new_serial:
            flash('请选择旧序列号和新序列号', 'error')
            return redirect(url_for('sales_serial'))

        old_product = Product.query.get_or_404(old_product_id)
        new_product = Product.query.get_or_404(new_product_id)

        # 验证旧序列号是否在已售记录中
        sales_with_old = Sales.query.filter(
            Sales.product_id == old_product_id
        ).filter(Sales.serial_numbers.like(f'%{old_serial}%')).first()
        if not sales_with_old:
            flash('旧序列号未找到有效销售记录', 'error')
            return redirect(url_for('sales_serial'))

        # 验证新序列号是否可用
        available = get_available_serials(new_product_id)
        if new_serial not in available:
            flash('新序列号不在可用库存中', 'error')
            return redirect(url_for('sales_serial'))

        old_price = float(sales_with_old.total_price) / max(int(sales_with_old.quantity), 1)
        new_price = float(new_product.sell_price)
        price_diff = round(new_price - old_price, 2)

        # 处理旧序列号：从销售记录中移除
        try:
            sn_list = json.loads(sales_with_old.serial_numbers)
            if old_serial in sn_list:
                sn_list.remove(old_serial)
            sales_with_old.serial_numbers = json.dumps(sn_list, ensure_ascii=False) if sn_list else None
        except:
            sales_with_old.serial_numbers = None

        # 不同商品时：减少新商品库存
        if old_product_id != new_product_id:
            new_product.stock -= 1

        # 创建新销售记录（换出的商品）
        new_sale = Sales(
            product_id=new_product_id, quantity=1,
            unit_price=new_product.sell_price,
            total_price=new_product.sell_price,
            customer=sales_with_old.customer,
            sales_date=date.today(), sales_user_id=current_user.id,
            serial_numbers=json.dumps([new_serial], ensure_ascii=False),
        )
        db.session.add(new_sale)
        sales_with_old.sales_user_id = current_user.id

        # 记录换货日志
        ex = ExchangeRecord(
            old_sale_id=sales_with_old.id,
            new_sale_id=new_sale.id,
            old_product_id=old_product_id,
            new_product_id=new_product_id,
            old_serial=old_serial,
            new_serial=new_serial,
            old_price=old_price,
            new_price=new_price,
            price_diff=price_diff,
            operator_id=current_user.id,
            reason=reason,
        )
        db.session.add(ex)
        db.session.commit()

        flash(f'换货成功！{old_product.name}({old_serial}) → {new_product.name}({new_serial})，补差 {price_diff:+.2f} 元',
              'success')
        return redirect(url_for('sales_serial'))

    # ── 添加类别 ──

    @app.route('/category/add', methods=['POST'])
    @login_required  # 必须登录才能添加类别
    @role_required('admin')  # 只有管理员能添加类别
    def add_category():
        """
        添加新类别到数据库
        GET: 显示添加表单
        POST: 处理添加请求
        """
        name = request.form.get('name')  # 类别中文名
        slug = request.form.get('slug', '')  # 类别英文标识

        # 如果没填slug，自动生成（用小写+下划线）
        if not slug:
            slug = name.lower().replace(' ', '_')

        # 检查类别是否已存在
        existing = Category.query.filter_by(slug=slug).first()
        if existing:
            flash('类别标识已存在！', 'error')
            return redirect(url_for('index'))

        # 创建新类别
        category = Category(name=name, slug=slug)
        db.session.add(category)
        db.session.commit()

        flash(f'类别 "{name}" 添加成功！', 'success')
        return redirect(url_for('index'))

    # ── 属性模板管理 ──

    @app.route('/template/add', methods=['POST'])
    @login_required
    @role_required('admin')
    def add_template():
        """添加属性模板"""
        name = request.form.get('name')
        fields_json = request.form.get('fields', '[]')  # 已序列化的JSON数组

        template = AttributeTemplate(
            name=name,
            fields=fields_json,
            created_by=current_user.id
        )
        db.session.add(template)
        db.session.commit()
        flash('模板添加成功！', 'success')
        return redirect(url_for('template_list'))

    @app.route('/template/delete/<int:tid>', methods=['POST'])
    @login_required
    @role_required('admin')
    def delete_template(tid):
        """删除属性模板"""
        t = AttributeTemplate.query.get_or_404(tid)
        db.session.delete(t)
        db.session.commit()
        flash('模板已删除', 'success')
        return redirect(url_for('template_list'))

    @app.route('/template/list')
    @login_required
    def template_list():
        """查看所有属性模板"""
        templates = AttributeTemplate.query.all()
        for t in templates:
            if t.fields:
                import json
                try:
                    fields = json.loads(t.fields)
                except:
                    # 尝试清理后再解析
                    try:
                        fields = json.loads(t.fields.replace('\r\n', '').replace('\n', ''))
                    except:
                        fields = []
                t.field_count = len(fields) if isinstance(fields, list) else 0
            else:
                t.field_count = 0
        return render_template('template_list.html', templates=templates)


    @app.route('/template/get/<int:tid>')
    @login_required
    def get_template(tid):
        """获取单个模板详情"""
        t = AttributeTemplate.query.get_or_404(tid)
        try:
            return jsonify({'id': t.id, 'name': t.name, 'fields': json.loads(t.fields or '[]')})
        except Exception:
            return jsonify({'id': t.id, 'name': t.name, 'fields': []})

    # ── 品牌管理 ──

    @app.route('/brand/add', methods=['POST'])
    @login_required
    @role_required('admin')
    def add_brand():
        """添加品牌"""
        name = request.form.get('name')
        if not name:
            flash('品牌名称不能为空', 'error')
            return redirect(url_for('index'))

        slug = name.lower().replace(' ', '_')
        existing = Brand.query.filter_by(slug=slug).first()
        if existing:
            flash('品牌已存在！', 'error')
        else:
            brand = Brand(name=name, slug=slug)
            db.session.add(brand)
            db.session.commit()
            flash(f'品牌 "{name}" 添加成功！', 'success')
        return redirect(url_for('index'))

    # ── 退货记录页面 ──

    @app.route('/returns')
    @login_required
    @role_required('admin', 'warehouse')  # 只有管理员和仓管能看
    def returns():
        """
        显示所有退货记录
        """

        # 查询所有退货记录
        returns = ReturnRecord.query.order_by(ReturnRecord.return_date.desc()).all()
        return render_template('returns.html', returns=returns)

    @app.route('/supplier/list')
    @login_required
    @role_required('admin', 'warehouse')
    def supplier_list():
        suppliers = Supplier.query.all()
        return render_template('supplier_list.html', suppliers=suppliers)

    @app.route('/supplier/add', methods=['POST'])
    @login_required
    @role_required('admin', 'warehouse')
    def add_supplier():
        name = request.form.get('name')
        parent_id = request.form.get('parent_id')
        if not name:
            flash('供应商名称不能为空', 'error')
            return redirect(url_for('index'))
        slug = name.lower().replace(' ', '_')
        existing = Supplier.query.filter_by(slug=slug).first()
        if existing:
            flash('供应商已存在！', 'error')
        else:
            supplier = Supplier(name=name, slug=slug, parent_id=int(parent_id) if parent_id else None)
            db.session.add(supplier)
            db.session.commit()
            flash(f'供应商 "{name}" 添加成功！', 'success')
        return redirect(url_for('supplier_list'))

    @app.route('/supplier/delete/<int:sid>', methods=['POST'])
    @login_required
    @role_required('admin', 'warehouse')
    def delete_supplier(sid):
        s = Supplier.query.get_or_404(sid)
        db.session.delete(s)
        db.session.commit()
        flash('供应商已删除', 'success')
        return redirect(url_for('supplier_list'))


    # ── 获取某商品已销售的序列号（AJAX 用）──
    @app.route('/sales/sold_serials/<int:product_id>')
    @login_required
    def get_sold_serials(product_id):
        """返回该商品所有已销售且未退货的序列号列表"""
        sales_records = Sales.query.filter_by(product_id=product_id).all()
        serials = []
        for s in sales_records:
                try:
                    sn_list = json.loads(s.serial_numbers)
                    serials.extend(sn_list)
                except:
                    pass
        # 去重
        serials = list(set(serials))
        return jsonify({'serials': serials})

    # ── 退货提交 ──
    @app.route('/return/submit', methods=['POST'])
    @login_required
    @role_required('admin', 'warehouse',  'sales')  # 退货由管理员或仓管操作
    def submit_return():
        product_id = int(request.form.get('product_id'))
        serial_numbers_str = request.form.get('serial_numbers', '')
        quantity = int(request.form.get('quantity', 1))
        refund_amount = float(request.form.get('refund_amount', 0))
        reason = request.form.get('reason', '')

        if not serial_numbers_str:
            flash('请选择要退货的序列号', 'error')
            return redirect(url_for('sales_serial'))

        serial_numbers = [s.strip() for s in serial_numbers_str.split(',') if s.strip()]

        # 查询商品
        product = Product.query.get_or_404(product_id)

        # 创建退货记录
        target_sale=None
        for s in Sales.query.filter_by(product_id=product_id).all():
                try:
                    sn_list=json.loads(s.serial_numbers)
                    if any(sn in sn_list for sn in serial_numbers):
                        target_sale=s
                        break
                except:
                    pass
        # 标记目标销售记录为已退货
        if target_sale:
            try:
                sn_list = json.loads(target_sale.serial_numbers)
                for sn in serial_numbers:
                    if sn in sn_list:
                        sn_list.remove(sn)
                target_sale.serial_numbers = json.dumps(sn_list, ensure_ascii=False) if sn_list else None
            except:
                target_sale.serial_numbers = None

        ret = ReturnRecord(
            product_id=product_id,
            sales_id=target_sale.id if target_sale else None,
            operator_id=current_user.id,
            return_serial=', '.join(serial_numbers),
            reason=reason,
            quantity=quantity,
            refund_amount=refund_amount,
        )
        db.session.add(ret)

        # 退还库存（假设退回的序列号重新回到库存）
        product.stock += quantity

        db.session.commit()
        flash(f'退货成功！已退回 {quantity} 件，库存已恢复', 'success')
        return redirect(url_for('sales_serial'))

    # ── 换货提交 ──
    @app.route('/exchanges')
    @login_required
    @role_required('admin', 'warehouse')
    def exchanges():
        """显示所有换货记录"""
        exchanges = ExchangeRecord.query.order_by(ExchangeRecord.exchange_date.desc()).all()
        for e in exchanges:
            e.purchase_amount_old = float(e.old_product.cost_price) if e.old_product else 0
            e.purchase_amount_new = float(e.new_product.cost_price) if e.new_product else 0
        return render_template('exchanges.html', exchanges=exchanges)


