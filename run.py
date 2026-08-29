# run.py
# 项目启动入口文件

from app import create_app

# 创建 Flask 应用实例
app = create_app()

# 程序从这里开始运行
if __name__ == '__main__':
    # debug=True 开启调试模式，代码修改后自动重启
    # host='0.0.0.0' 允许局域网访问
    # port=5000 使用 5000 端口
    app.run(debug=True, host='0.0.0.0', port=5000)
