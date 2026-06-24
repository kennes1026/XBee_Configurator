# XBee 參數設定工具

PC版 XBee 參數讀取及設定程式 - Python + PyQt6 開發，支援 AT Command Mode

![Version](https://img.shields.io/badge/version-1.96-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## 功能特色

- 🔍 自動搜尋 XBee 連接的 COM Port
- ⚙️ 設定 COM Port 及通訊參數 (Baud Rate, Parity, Data Bits, Stop Bits)
- 📖 讀取參數: MAC Address, PAN ID, JV, Baud Rate, CE, AP
- ✏️ 修改參數: PAN ID, JV, Baud Rate, CE, AP
- 📦 支援全部參數一次寫入
- 🔎 自動偵測 XBee Baud Rate
- 📋 完整通訊日誌記錄

## 系統需求

- Python 3.8 或以上版本
- Windows / Linux / macOS

## 安裝步驟

1. 安裝 Python 依賴套件：
```bash
pip install -r requirements.txt
```

2. 執行程式：

**Windows:**
```bash
run_xbee_tool.bat
```
或
```bash
python xbee_configurator.py
```

**Linux/macOS:**
```bash
chmod +x run_xbee_tool.sh
./run_xbee_tool.sh
```

## 建置執行檔 (Windows)

執行建置腳本產生獨立執行檔：
```bash
build_exe.bat
```

產生的執行檔位於 `dist/XBee_Configurator/` 目錄。

## 使用說明

1. 將 XBee 模組透過 USB 轉接器連接到電腦
2. 啟動程式
3. 選擇正確的 COM Port 和 Baud Rate
4. 點擊「連接」按鈕
5. 點擊「讀取所有參數」取得 XBee 目前設定
6. 修改需要的參數後，點擊對應的「寫入」按鈕

## 參數說明

| 參數 | 說明 | 範圍 |
|------|------|------|
| MAC Address | XBee 的唯一識別碼 (唯讀) | - |
| PAN ID | 個人區域網路識別碼 | 0x00000000 ~ 0xFFFFFFFF |
| JV | Channel Verification | 0 或 1 |
| Baud Rate | 串列通訊速率 | 1200 ~ 230400 |
| CE | Coordinator Enable | 0 (Disabled) / 1 (Enabled) |
| AP | API Mode | 0 (Transparent) / 1 (API Mode) |

## 螢幕截圖

程式介面採用現代化設計，支援完整的參數讀寫功能。

## 版本歷史

### v1.96 (2026-01-12)
- 🔧 修正 Windows 深色/淺色主題相容性問題
- 🎨 強制使用淺色主題調色板，避免受系統主題影響
- 🎨 加入 QProgressBar 完整樣式定義
- 📝 確保所有介面元素在深色主題下仍清晰可見

### v1.95 (2026-01-12)
- 🔧 擴展 PAN ID 範圍至 32 位元 (0x00000000 ~ 0xFFFFFFFF)
- 🔧 更新 PAN ID 輸入欄位最大長度為 8 位十六進制
- 📝 更新 PAN ID 驗證邏輯和顯示格式

### v1.94 (2026-01-12)
- 🔧 修正 PyInstaller 建置腳本，改用 `python -m PyInstaller` 執行

### v1.93 (2026-01-12)
- ✨ 新增「全部寫入」功能，可一次寫入所有參數
- 🎨 使用深色按鈕樣式區分全部寫入按鈕

### v1.92 (2026-01-12)
- 🔧 修正寫入按鈕在連接後無法點擊的問題
- 📝 寫入按鈕現在需要先讀取參數後才能啟用

### v1.91 (2026-01-12)
- 🎨 調整 XBee 參數區域高度配置

### v1.9 (2026-01-12)
- ✨ 新增 CE (Coordinator Enable) 參數讀寫功能
- ✨ 新增 AP (API Mode) 參數讀寫功能
- 🎨 重新設計介面佈局，改用 QScrollArea 包裝參數區域

### v1.0 ~ v1.8
- 基礎功能開發
- COM Port 自動偵測
- 參數讀取/寫入功能
- GUI 介面設計

## 授權

MIT License

## 作者

Claude AI Assistant + Kennes
