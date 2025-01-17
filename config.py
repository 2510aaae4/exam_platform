import os
from datetime import timedelta

class Config:
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    
    # Azure SQL Database 配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('AZURE_SQL_CONNECTION_STRING') or \
        'mssql+pyodbc://<username>:<password>@<server>.database.windows.net/<database>?driver=SQL+Server'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Azure Blob Storage 配置（用於存儲題目圖片）
    AZURE_STORAGE_CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
    AZURE_CONTAINER_NAME = os.environ.get('AZURE_CONTAINER_NAME', 'exam-images')
    
    # Application Insights 配置
    APPINSIGHTS_INSTRUMENTATIONKEY = os.environ.get('APPINSIGHTS_INSTRUMENTATIONKEY')
    
    # Session 配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 檔案上傳配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
