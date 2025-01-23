# 考古題平台使用說明

這是一個用於練習考試題目的網頁應用程式。

## 系統需求

- Python 3.8 或更新版本
- pip（Python 套件管理器）

## 安裝步驟

1. 下載或複製整個專案資料夾

2. 安裝所需的 Python 套件：
   ```bash
   pip install -r requirements.txt
   ```

## 如何運行

1. 打開命令提示字元（cmd）或終端機

2. 切換到專案資料夾：
   ```bash
   cd 專案資料夾路徑
   ```

3. 運行應用程式：
   ```bash
   python app.py
   ```

4. 開啟網頁瀏覽器，訪問：
   ```
   http://localhost:5000
   ```

## 資料夾結構說明

- `app.py`：主程式
- `config.py`：設定檔
- `requirements.txt`：需要的 Python 套件清單
- `templates/`：網頁模板
- `static/`：靜態檔案（CSS、JavaScript）
- `questions/`：題目資料夾
  - 各年度題目和圖片

## 注意事項

1. 確保 `questions` 資料夾中有完整的題目檔案和圖片
2. 第一次運行時會自動建立資料庫
3. 預設使用 SQLite 資料庫，資料會存在 `app.db` 檔案中

## 常見問題解決

1. 如果看到 "找不到模組" 的錯誤：
   ```bash
   pip install -r requirements.txt
   ```

2. 如果無法開啟網頁：
   - 確認 Python 程式正在運行
   - 確認使用的是 http://localhost:5000
   - 確認防火牆沒有阻擋

3. 如果圖片無法顯示：
   - 確認 questions 資料夾中有對應的圖片檔案
   - 確認圖片副檔名為 .png

## 聯絡方式

如有任何問題，請聯繫系統管理員。
