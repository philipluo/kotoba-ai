#!/usr/bin/env python3
"""
数据库初始化脚本
"""
import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.backend.models.database import Database

def main():
    print("🗄️  言葉AI 数据库初始化")
    print("=" * 50)
    
    try:
        db_path = os.path.join(project_root, 'data', 'japanese_learning.db')
        
        # 初始化表结构
        print("\n📋 创建数据表...")
        Database.init_db(db_path)
        print("✅ 数据表创建完成")
        
        # 初始化50音数据
        print("\n🈳 初始化50音数据...")
        Database.init_phonetics(db_path)
        print("✅ 50音数据初始化完成")
        
        print("\n🎉 数据库初始化成功！")
        print(f"📁 数据库位置: {db_path}")
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
