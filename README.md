# XBee 參數設定工具

PC 版 XBee 參數讀取及設定程式，使用 Python + PyQt6 開發，參考 Arduino 程式 (get_modify_xbee_parameter.ino) 開發。

## 功能特色

- 🔍 自動搜尋 XBee 連接的 COM Port
- 🔧 設定 COM Port 通訊參數 (Baud Rate, Parity, Data Bits, Stop Bits)
- 📖 讀取 XBee 參數: MAC Address, PAN ID, JV, Baud Rate, CE, AP
- ✏️ 修改 XBee 參數: PAN ID, JV, Baud Rate, CE, AP
- 🔄 自動偵測 XBee Baud Rate
- 📝 即時通訊日誌顯示
- 💾 全部寫入功能 - 一次寫入所有參數

## 系統需求

- Python 3.8 或以上版本
- Windows / macOS / Linux

## 安裝方式

### 方式一：直接執行 Python 腳本

1. 安裝相依套件：
```bash
pip install -r requirements.txt
```

2. 執行程式：
```bash
python xbee_configurator.py
```

### 方式二：編譯為獨立執行檔 (Windows)

1. 安裝相依套件：
```bash
pip install -r requirements.txt
pip install pyinstaller
```

2. 執行編譯腳本：
```bash
build_exe.bat
```

3. 編譯完成後，執行檔位於 `dist/XBee_Configurator.exe`

## 使用說明

### 連接 XBee

1. 將 XBee 模組透過 USB 轉接板連接到電腦
2. 點擊「🔄 重新整理」按鈕掃描可用的 COM Port
3. 選擇正確的 COM Port 和 Baud Rate
4. 點擊「🔌 連接」按鈕建立連線

### 讀取參數

1. 連線成功後，點擊「📖 讀取所有參數」按鈕
2. 程式會自動讀取並顯示所有 XBee 參數

### 修改參數

1. 在對應的輸入欄位中輸入新值
2. 點擊該參數旁的「寫入」按鈕進行單一參數寫入
3. 或點擊「全部寫入」按鈕一次寫入所有參數

### 自動偵測 Baud Rate

如果不確定 XBee 的 Baud Rate，可以使用「🔍 自動偵測 Baud Rate」功能自動偵測。

## XBee 參數說明

| 參數 | 說明 | 範圍 |
|------|------|------|
| MAC Address | XBee 唯一識別碼 (唯讀) | 16 位元十六進制 |
| PAN ID | 個人區域網路識別碼 | 0x00000000 ~ 0xFFFFFFFF |
| JV | Channel Verification | 0 或 1 |
| Baud Rate | 序列埠通訊速率 | 1200 ~ 230400 |
| CE | Coordinator Enable | 0 (End Device) 或 1 (Coordinator) |
| AP | API Mode | 0 (Transparent) 或 1 (API Mode) |

## 檔案說明

| 檔案 | 說明 |
|------|------|
| xbee_configurator.py | 主程式 |
| requirements.txt | Python 相依套件清單 |
| build_exe.bat | Windows 編譯腳本 |
| XBee_Configurator.spec | PyInstaller 設定檔 |
| run_xbee_tool.bat | Windows 快速啟動腳本 |
| run_xbee_tool.sh | Linux/macOS 快速啟動腳本 |

## 注意事項

- 修改 Baud Rate 後需要以新的 Baud Rate 重新連接
- CE 參數會影響 XBee 的網路角色 (Coordinator/End Device)
- AP 參數會影響通訊模式 (透明模式/API模式)
- 建議修改參數前先備份原始設定

---

## 版本歷程

### v1.95 (2025-01-12)
- 🔧 **PAN ID 範圍擴展**：最大輸入範圍從 0xFFFF 擴展到 0xFFFFFFFF (32-bit)
- 📝 輸入欄位最大長度從 5 位調整為 8 位
- 🐛 修正 build_exe.bat：使用 `python -m PyInstaller` 取代直接呼叫 `pyinstaller` 以解決 PATH 問題

### v1.94 (2025-01-11)
- 🎨 調整連接/斷開按鈕顏色邏輯：
  - 初始狀態 → 紅色
  - 未連接狀態 → 紅色  
  - 已連接狀態 → 綠色
- 📄 更新 README.md，加入完整版本修改歷程

### v1.93 (2025-01-11)
- 🔒 **寫入權限控制**：連接成功後，所有寫入按鈕預設禁用，必須讀取所有參數成功後才能寫入
- 🎨 **連接按鈕顏色**：「連接/斷開」按鈕依狀態顯示不同顏色
- ➕ **全部寫入功能**：新增「全部寫入」按鈕，可一次依序寫入所有參數 (PAN ID → JV → CE → AP → Baud Rate)

### v1.92 (2025-01-11)
- 🔄 對調「連接」和「自動偵測 Baud Rate」按鈕順序
- 📐 新增 XBee 參數區域高度調整功能 (setFixedHeight)

### v1.91 (2025-01-11)
- 🎨 使用者自行調整 UI 佈局

### v1.9 (2025-01-11)
- 🐛 修復按鈕不可見問題：移除 `param_container.setStyleSheet("background-color: white;")` 
- 🔧 簡化 QScrollArea 樣式，與 v1.3 保持一致

### v1.8 (2025-01-09)
- 🔧 **完整 Layout 重設計**：使用 QGridLayout 取代 QHBoxLayout
- 📐 解決按鈕在 QScrollArea 中被隱藏的問題
- 🎯 Grid 佈局：Label (col 0) | Display (col 1) | New Label (col 2) | Input (col 3) | Button (col 4)

### v1.7 (2025-01-09)
- 🔧 嘗試縮減元件寬度解決按鈕不可見問題 (未完全解決)

### v1.6 (2025-01-09)
- 🐛 移除 QComboBox 自訂下拉箭頭樣式 (PyQt6 QSS 不支援 CSS border triangle 技巧)
- 🔧 改用系統預設箭頭，新增 padding-right 保留空間

### v1.5 (2025-01-09)
- 🎨 **集中化顏色配置**：新增顏色變數系統 (COLOR_PRIMARY, COLOR_BG_*, COLOR_TEXT_* 等)
- 📝 新增詳細顏色註解說明
- 🎯 QComboBox 下拉選單樣式優化

### v1.4 (2025-01-09)
- 🔧 修復捲動區域高度不足問題
- 📜 設定固定高度 220px，垂直捲軸 Always On
- 🎨 新增捲軸樣式 (藍色滑塊、hover 效果)

### v1.3 (2025-01-09)
- 🔧 修復 GUI 佈局壓縮問題
- 📜 新增 QScrollArea 捲動功能
- 📐 固定元件寬度避免壓縮

### v1.2 (2025-01-09)
- ➕ 新增 CE (Coordinator Enable) 參數支援
- ➕ 新增 AP (API Mode) 參數支援
- 🔧 修復 build_exe.bat 編碼問題 (UTF-8 BOM)

### v1.1 (2025-01-09)
- 🔧 PAN ID 改為十六進制格式輸入
- 📋 顯示格式：0xHHHH (DEC: DDDDD)

### v1.0 (2025-01-09)
- 🎉 初始版本
- ✅ 基本功能：COM Port 連接、參數讀取、參數寫入
- ✅ 支援參數：MAC Address, PAN ID, JV, Baud Rate
- ✅ 自動偵測 Baud Rate 功能
- ✅ 通訊日誌顯示

---

## 技術參考

- [Digi XBee/XBee-PRO S1 802.15.4 User Guide](https://www.digi.com/resources/documentation/digidocs/90000982/)
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [pySerial Documentation](https://pyserial.readthedocs.io/)

## 授權

此程式僅供學習和參考使用。

## 作者

Claude AI Assistant + Kennes
