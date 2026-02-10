#!/usr/bin/env python3
"""
言葉AI (Kotoba AI) 启动脚本
"""
import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.backend.models.database import Database

def init_database():
    """初始化数据库"""
    print("🗄️  正在初始化数据库...")
    db_path = os.path.join(project_root, 'data', 'japanese_learning.db')
    Database.init_db(db_path)
    Database.init_phonetics(db_path)
    print("✅ 数据库初始化完成")

def main():
    """主函数"""
    print("🌸 欢迎使用 言葉AI (Kotoba AI)")
    print("=" * 50)
    
    # 初始化数据库（不依赖 Flask 上下文）
    init_database()
    
    # 导入并创建 Flask 应用
    from src.backend.app import create_app
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    # 获取配置
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"\n🚀 启动服务...")
    print(f"📍 访问地址: http://{host}:{port}")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
    print("\n按 Ctrl+C 停止服务\n")
    
    # 启动应用
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )

if __name__ == '__main__':
    main()
