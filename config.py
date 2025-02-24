import os

# 獲取當前文件的目錄
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # 設置密鑰
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    
    # 設置數據庫
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    
    # 設置是否追踪數據庫修改
    SQLALCHEMY_TRACK_MODIFICATIONS = False
