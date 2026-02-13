from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os
from .config import config

# 导入路由
from .routes.entries import entries_bp
from .routes.phonetics import phonetics_bp
from .routes.practice import practice_bp
from .routes.stats import stats_bp
from .routes.verbs import verbs_bp

def create_app(config_name='default'):
    """应用工厂函数"""
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    frontend_dir = os.path.join(project_root, 'src', 'frontend')
    
    app = Flask(
        __name__,
        static_folder=frontend_dir,
        static_url_path=''
    )
    
    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 启用CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # 注册蓝图
    app.register_blueprint(entries_bp)
    app.register_blueprint(phonetics_bp)
    app.register_blueprint(practice_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(verbs_bp)
    
    # 根路由 - 返回首页
    @app.route('/')
    def index():
        return send_from_directory(frontend_dir, 'index.html')
    
    # 页面路由
    @app.route('/pages/<path:page>')
    def serve_page(page):
        return send_from_directory(os.path.join(frontend_dir, 'pages'), page)
    
    # API健康检查
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'success': True,
            'message': '言葉AI (Kotoba AI) 服务正常运行',
            'version': '1.0.0'
        })
    
    return app
