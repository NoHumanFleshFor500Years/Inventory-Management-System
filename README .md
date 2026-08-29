# Inventory Management System

基于 Flask 产品进销存管理系统，支持序列号级精细化管理。

## 功能特性

- **商品管理**：添加、编辑、搜索商品，支持自定义属性（容量/颜色/IMEI 等）
- **采购入库**：记录采购来源、成本价，支持批量输入序列号
- **销售出库**：选择具体序列号开单，自动扣减库存
- **退货处理**：按序列号退货，库存自动恢复
- **换货功能**：记录换货流水，自动计算差价
- **库存预警**：低于阈值自动提醒
- **角色权限**：管理员 / 仓管 / 销售员三级权限控制
- **数据可视化**：首页展示库存概览、今日销售统计

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.11 + Flask |
| 数据库 | SQLite（Flask-SQLAlchemy） |
| 认证 | Flask-Login |
| 前端 | HTML + Jinja2 模板 |

## 快速开始

```bash
cd phone-inventory
python -m venv .venv
.venv\Scripts\activate
pip install flask flask-sqlalchemy flask-login
python run.py