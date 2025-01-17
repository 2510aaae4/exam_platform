# Render.com 部署指南

## 步驟 1：準備 GitHub
1. 前往 https://github.com/ 註冊帳號（如果還沒有）
2. 創建新的儲存庫（Repository）
   - 點擊右上角的 "+" -> "New repository"
   - 輸入儲存庫名稱：`exam_platform`
   - 選擇 "Public"
   - 點擊 "Create repository"

## 步驟 2：上傳程式碼到 GitHub
1. 下載並安裝 Git：https://git-scm.com/downloads
2. 在專案資料夾中打開命令提示字元，執行：
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/您的用戶名/exam_platform.git
   git push -u origin main
   ```

## 步驟 3：在 Render.com 部署
1. 前往 https://render.com/ 註冊帳號
   - 可以直接用 GitHub 帳號登入

2. 創建新的 Web Service
   - 點擊 "New +" -> "Web Service"
   - 選擇 "Build and deploy from a Git repository"
   - 選擇您的 GitHub 儲存庫 `exam_platform`

3. 配置 Web Service
   填寫以下資訊：
   - Name: `exam-platform`（或您想要的名稱）
   - Region: 選擇離您最近的地區
   - Branch: `main`
   - Root Directory: 保持空白
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn wsgi:application`
   - Plan: 選擇 "Free"

4. 環境變數設置
   在 "Environment" 部分添加：
   - Key: `PYTHON_VERSION`
     Value: `3.8.12`
   - Key: `FLASK_APP`
     Value: `app.py`
   - Key: `FLASK_ENV`
     Value: `production`

5. 點擊 "Create Web Service"

## 步驟 4：等待部署
- Render 會自動開始部署您的應用
- 部署過程可能需要幾分鐘
- 您可以在 "Events" 標籤中查看部署進度

## 步驟 5：訪問您的網站
- 部署完成後，Render 會提供一個網址（例如：https://exam-platform.onrender.com）
- 點擊網址測試您的應用

## 更新網站
當您想更新網站時：
1. 在本地修改程式碼
2. 提交到 GitHub：
   ```bash
   git add .
   git commit -m "更新說明"
   git push
   ```
3. Render 會自動重新部署

## 注意事項
1. 免費方案有一些限制：
   - 每月有 750 小時的運行時間限制
   - 不活躍時會自動休眠
   - 首次訪問可能需要等待幾秒鐘喚醒

2. 資料庫注意事項：
   - 免費方案的資料會在每次部署時重置
   - 如果需要永久儲存資料，建議使用外部資料庫服務

3. 檔案儲存：
   - 上傳的檔案不會永久保存
   - 建議使用外部儲存服務（如 AWS S3）存儲檔案

## 疑難排解
如果遇到問題：
1. 檢查 Render 的日誌（Logs）
2. 確認所有環境變數設置正確
3. 檢查 requirements.txt 是否包含所有需要的套件
