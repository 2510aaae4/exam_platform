#!/bin/bash
# 執行資料庫遷移
flask db upgrade

# 啟動應用程序
exec gunicorn wsgi:application
