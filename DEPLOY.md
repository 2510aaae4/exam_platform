# 考古題平台部署指南

## 系統需求
- Python 3.8+
- Nginx
- SQLite3

## 部署步驟

### 1. 準備伺服器
```bash
# 更新系統
sudo apt update
sudo apt upgrade -y

# 安裝必要的套件
sudo apt install python3-pip python3-venv nginx -y
```

### 2. 設置專案
```bash
# 創建專案目錄
sudo mkdir -p /var/www/exam_platform
sudo chown -R $USER:$USER /var/www/exam_platform

# 複製專案文件
cp -r * /var/www/exam_platform/

# 創建虛擬環境
cd /var/www/exam_platform
python3 -m venv venv
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

### 3. 設置 Nginx
```bash
# 複製 Nginx 配置
sudo cp nginx.conf /etc/nginx/sites-available/exam_platform
sudo ln -s /etc/nginx/sites-available/exam_platform /etc/nginx/sites-enabled/

# 修改 nginx.conf 中的路徑
sudo nano /etc/nginx/sites-available/exam_platform

# 測試配置
sudo nginx -t

# 重啟 Nginx
sudo systemctl restart nginx
```

### 4. 設置 Gunicorn 服務
```bash
# 創建服務文件
sudo nano /etc/systemd/system/exam_platform.service
```

將以下內容複製到服務文件中：
```ini
[Unit]
Description=Gunicorn instance to serve exam platform
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/exam_platform
Environment="PATH=/var/www/exam_platform/venv/bin"
ExecStart=/var/www/exam_platform/venv/bin/gunicorn --workers 3 --bind unix:exam_platform.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
```

```bash
# 啟動服務
sudo systemctl start exam_platform
sudo systemctl enable exam_platform
```

### 5. 設置防火牆
```bash
# 允許 HTTP 和 HTTPS 流量
sudo ufw allow 'Nginx Full'
```

### 6. 設置 SSL（選擇性）
使用 Let's Encrypt 設置 HTTPS：
```bash
# 安裝 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 獲取 SSL 證書
sudo certbot --nginx -d your_domain.com
```

### 7. 資料庫備份（建議定期執行）
```bash
# 備份資料庫
cp instance/exam.db /backup/exam_$(date +%Y%m%d).db
```

## 維護指南

### 更新應用程式
```bash
# 進入專案目錄
cd /var/www/exam_platform

# 啟動虛擬環境
source venv/bin/activate

# 拉取最新代碼（如果使用 git）
git pull

# 更新依賴
pip install -r requirements.txt

# 重啟服務
sudo systemctl restart exam_platform
```

### 查看日誌
```bash
# 查看應用程式日誌
sudo journalctl -u exam_platform

# 查看 Nginx 日誌
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 故障排除

### 1. 如果應用程式無法啟動
- 檢查日誌：`sudo journalctl -u exam_platform`
- 確認權限：`sudo chown -R www-data:www-data /var/www/exam_platform`
- 檢查 Python 路徑：`which python`

### 2. 如果無法訪問網站
- 檢查 Nginx 狀態：`sudo systemctl status nginx`
- 檢查防火牆規則：`sudo ufw status`
- 檢查域名解析：`ping your_domain.com`

### 3. 資料庫問題
- 檢查權限：`sudo chown www-data:www-data /var/www/exam_platform/instance/exam.db`
- 備份並重建：`cp instance/exam.db instance/exam.db.bak`
