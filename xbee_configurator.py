#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XBee Parameter Configuration Tool
=================================
PC版 XBee 參數讀取及設定程式
參考 Arduino 程式開發，支援 AT Command Mode

功能:
- 自動搜尋 XBee 連接的 COM Port
- 設定 COM Port 及通訊參數 (Baud Rate, Parity, Data Bits, Stop Bits)
- 讀取參數: MAC Address, PAN ID, JV, Baud Rate
- 修改參數: PAN ID, JV, Baud Rate

Author: Claude AI Assistant + Kennes
Date: 2026-01-12
Version: 1.96 - 修正深色主題相容性問題
"""

import sys
import time
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QComboBox, QPushButton, QLineEdit, QTextEdit,
    QSpinBox, QMessageBox, QProgressBar, QFrame, QGridLayout,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon


class XBeeWorker(QThread):
    """背景執行緒處理 XBee 通訊"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    # Baud Rate 對照表 (index -> actual rate)
    BAUD_RATE_MAP = {
        0: 1200,
        1: 2400,
        2: 4800,
        3: 9600,
        4: 19200,
        5: 38400,
        6: 57600,
        7: 115200,
        8: 230400
    }
    
    # 反向對照表 (actual rate -> index)
    BAUD_RATE_INDEX = {v: k for k, v in BAUD_RATE_MAP.items()}
    
    def __init__(self, serial_port, operation='read', params=None):
        super().__init__()
        self.serial_port = serial_port
        self.operation = operation
        self.params = params or {}
        self.running = True
        
    def run(self):
        try:
            if self.operation == 'read':
                self.read_parameters()
            elif self.operation == 'write_panid':
                self.write_panid()
            elif self.operation == 'write_jv':
                self.write_jv()
            elif self.operation == 'write_baudrate':
                self.write_baudrate()
            elif self.operation == 'write_ce':
                self.write_ce()
            elif self.operation == 'write_ap':
                self.write_ap()
            elif self.operation == 'write_all':
                self.write_all_parameters()
            elif self.operation == 'auto_detect':
                self.auto_detect_baudrate()
        except Exception as e:
            self.error_signal.emit(f"錯誤: {str(e)}")
            
    def stop(self):
        self.running = False
        
    def send_command(self, cmd, wait_time=0.2):
        """發送 AT 命令並讀取回應"""
        self.serial_port.write(cmd.encode())
        time.sleep(wait_time)
        response = b''
        while self.serial_port.in_waiting:
            response += self.serial_port.read(self.serial_port.in_waiting)
            time.sleep(0.02)
        return response.decode('utf-8', errors='ignore').strip()
    
    def enter_at_mode(self):
        """進入 AT Command Mode"""
        self.log_signal.emit("正在進入 AT Command Mode...")
        time.sleep(1)
        self.serial_port.write(b'+++')
        time.sleep(2)
        
        response = b''
        while self.serial_port.in_waiting:
            response += self.serial_port.read(self.serial_port.in_waiting)
            time.sleep(0.02)
        
        response_str = response.decode('utf-8', errors='ignore').strip()
        self.log_signal.emit(f"回應: {response_str}")
        
        if 'OK' in response_str:
            self.log_signal.emit("成功進入 AT Command Mode")
            return True
        else:
            self.log_signal.emit("無法進入 AT Command Mode")
            return False
    
    def exit_at_mode(self):
        """退出 AT Command Mode"""
        self.log_signal.emit("退出 AT Command Mode...")
        response = self.send_command('ATCN\r')
        self.log_signal.emit(f"ATCN 回應: {response}")
        
    def read_parameters(self):
        """讀取所有 XBee 參數"""
        results = {}
        
        try:
            self.progress_signal.emit(5)
            
            # 進入 AT Mode
            if not self.enter_at_mode():
                self.error_signal.emit("無法進入 AT Command Mode，請檢查連接")
                return
            
            self.progress_signal.emit(10)
            
            # 讀取 JV
            self.log_signal.emit("讀取 JV 值...")
            response = self.send_command('ATJV\r')
            self.log_signal.emit(f"ATJV 回應: {response}")
            try:
                results['jv'] = int(response.replace('\r', '').replace('\n', ''))
            except:
                results['jv'] = 'N/A'
            
            self.progress_signal.emit(20)
            time.sleep(0.3)
            
            # 讀取 Baud Rate
            self.log_signal.emit("讀取 Baud Rate...")
            response = self.send_command('ATBD\r')
            self.log_signal.emit(f"ATBD 回應: {response}")
            try:
                bd_index = int(response.replace('\r', '').replace('\n', ''))
                results['baudrate_index'] = bd_index
                results['baudrate'] = self.BAUD_RATE_MAP.get(bd_index, 'Unknown')
            except:
                results['baudrate'] = 'N/A'
            
            self.progress_signal.emit(30)
            time.sleep(0.3)
            
            # 讀取 PAN ID
            self.log_signal.emit("讀取 PAN ID...")
            response = self.send_command('ATID\r')
            self.log_signal.emit(f"ATID 回應: {response}")
            try:
                pan_id_str = response.replace('\r', '').replace('\n', '')
                results['panid'] = int(pan_id_str, 16) if pan_id_str else 0
                results['panid_hex'] = pan_id_str.upper()
            except:
                results['panid'] = 'N/A'
                results['panid_hex'] = 'N/A'
            
            self.progress_signal.emit(40)
            time.sleep(0.3)
            
            # 讀取 CE (Coordinator Enable)
            self.log_signal.emit("讀取 CE (Coordinator Enable)...")
            response = self.send_command('ATCE\r')
            self.log_signal.emit(f"ATCE 回應: {response}")
            try:
                results['ce'] = int(response.replace('\r', '').replace('\n', ''))
            except:
                results['ce'] = 'N/A'
            
            self.progress_signal.emit(50)
            time.sleep(0.3)
            
            # 讀取 AP (API Enable)
            self.log_signal.emit("讀取 AP (API Enable)...")
            response = self.send_command('ATAP\r')
            self.log_signal.emit(f"ATAP 回應: {response}")
            try:
                results['ap'] = int(response.replace('\r', '').replace('\n', ''))
            except:
                results['ap'] = 'N/A'
            
            self.progress_signal.emit(60)
            time.sleep(0.3)
            
            # 讀取 MAC Address (SH + SL)
            self.log_signal.emit("讀取 MAC Address (SH)...")
            response_sh = self.send_command('ATSH\r')
            self.log_signal.emit(f"ATSH 回應: {response_sh}")
            mac_sh = response_sh.replace('\r', '').replace('\n', '').upper()
            
            self.progress_signal.emit(75)
            time.sleep(0.3)
            
            self.log_signal.emit("讀取 MAC Address (SL)...")
            response_sl = self.send_command('ATSL\r')
            self.log_signal.emit(f"ATSL 回應: {response_sl}")
            mac_sl = response_sl.replace('\r', '').replace('\n', '').upper()
            
            # 組合完整 MAC Address
            results['mac_address'] = f"{mac_sh.zfill(8)}{mac_sl.zfill(8)}"
            
            self.progress_signal.emit(90)
            
            # 退出 AT Mode
            self.exit_at_mode()
            
            self.progress_signal.emit(100)
            self.finished_signal.emit(results)
            
        except Exception as e:
            self.error_signal.emit(f"讀取參數時發生錯誤: {str(e)}")
            
    def write_panid(self):
        """寫入 PAN ID"""
        try:
            new_panid = self.params.get('panid', 0)
            
            self.progress_signal.emit(10)
            
            if not self.enter_at_mode():
                self.error_signal.emit("無法進入 AT Command Mode")
                return
            
            self.progress_signal.emit(25)
            
            # 寫入新的 PAN ID
            self.log_signal.emit(f"寫入新 PAN ID: {new_panid}...")
            response = self.send_command(f'ATID{new_panid:X}\r')
            self.log_signal.emit(f"ATID 回應: {response}")
            
            self.progress_signal.emit(40)
            time.sleep(0.5)
            
            # 驗證寫入
            self.log_signal.emit("驗證 PAN ID...")
            response = self.send_command('ATID\r')
            self.log_signal.emit(f"驗證回應: {response}")
            
            self.progress_signal.emit(55)
            
            # 寫入到 Flash
            self.log_signal.emit("寫入到 Flash (ATWR)...")
            response = self.send_command('ATWR\r')
            self.log_signal.emit(f"ATWR 回應: {response}")
            
            self.progress_signal.emit(70)
            time.sleep(0.5)
            
            # 套用變更
            self.log_signal.emit("套用變更 (ATAC)...")
            response = self.send_command('ATAC\r')
            self.log_signal.emit(f"ATAC 回應: {response}")
            
            self.progress_signal.emit(85)
            
            # 退出 AT Mode
            self.exit_at_mode()
            
            self.progress_signal.emit(100)
            self.finished_signal.emit({'success': True, 'message': f'PAN ID 已更新為 0x{new_panid:08X} (DEC: {new_panid})'})
            
        except Exception as e:
            self.error_signal.emit(f"寫入 PAN ID 時發生錯誤: {str(e)}")
            
    def write_jv(self):
        """寫入 JV 值"""
        try:
            new_jv = self.params.get('jv', 0)
            
            self.progress_signal.emit(10)
            
            if not self.enter_at_mode():
                self.error_signal.emit("無法進入 AT Command Mode")
                return
            
            self.progress_signal.emit(25)
            
            # 寫入新的 JV 值
            self.log_signal.emit(f"寫入新 JV 值: {new_jv}...")
            response = self.send_command(f'ATJV{new_jv}\r')
            self.log_signal.emit(f"ATJV 回應: {response}")
            
            self.progress_signal.emit(40)
            time.sleep(0.5)
            
            # 驗證寫入
            self.log_signal.emit("驗證 JV 值...")
            response = self.send_command('ATJV\r')
            self.log_signal.emit(f"驗證回應: {response}")
            
            self.progress_signal.emit(55)
            
            # 寫入到 Flash
            self.log_signal.emit("寫入到 Flash (ATWR)...")
            response = self.send_command('ATWR\r')
            self.log_signal.emit(f"ATWR 回應: {response}")
            
            self.progress_signal.emit(70)
            time.sleep(0.5)
            
            # 套用變更
            self.log_signal.emit("套用變更 (ATAC)...")
            response = self.send_command('ATAC\r')
            self.log_signal.emit(f"ATAC 回應: {response}")
            
            self.progress_signal.emit(85)
            
            # 退出 AT Mode
            self.exit_at_mode()
            
            self.progress_signal.emit(100)
            self.finished_signal.emit({'success': True, 'message': f'JV 已更新為 {new_jv}'})
            
        except Exception as e:
            self.error_signal.emit(f"寫入 JV 時發生錯誤: {str(e)}")
            
    def write_baudrate(self):
        """寫入 Baud Rate"""
        try:
            new_baudrate = self.params.get('baudrate', 9600)
            bd_index = self.BAUD_RATE_INDEX.get(new_baudrate, 3)
            
            self.progress_signal.emit(10)
            
            if not self.enter_at_mode():
                self.error_signal.emit("無法進入 AT Command Mode")
                return
            
            self.progress_signal.emit(25)
            
            # 寫入新的 Baud Rate
            self.log_signal.emit(f"寫入新 Baud Rate: {new_baudrate} (index={bd_index})...")
            response = self.send_command(f'ATBD{bd_index}\r')
            self.log_signal.emit(f"ATBD 回應: {response}")
            
            self.progress_signal.emit(40)
            time.sleep(0.5)
            
            # 驗證寫入
            self.log_signal.emit("驗證 Baud Rate...")
            response = self.send_command('ATBD\r')
            self.log_signal.emit(f"驗證回應: {response}")
            
            self.progress_signal.emit(55)
            
            # 寫入到 Flash
            self.log_signal.emit("寫入到 Flash (ATWR)...")
            response = self.send_command('ATWR\r')
            self.log_signal.emit(f"ATWR 回應: {response}")
            
            self.progress_signal.emit(70)
            time.sleep(0.5)
            
            # 套用變更
            self.log_signal.emit("套用變更 (ATAC)...")
            response = self.send_command('ATAC\r')
            self.log_signal.emit(f"ATAC 回應: {response}")
            
            self.progress_signal.emit(85)
            
            # 退出 AT Mode
            self.exit_at_mode()
            
            self.progress_signal.emit(100)
            self.finished_signal.emit({
                'success': True, 
                'message': f'Baud Rate 已更新為 {new_baudrate}',
                'new_baudrate': new_baudrate
            })
            
        except Exception as e:
            self.error_signal.emit(f"寫入 Baud Rate 時發生錯誤: {str(e)}")
            
    def write_ce(self):
        """寫入 CE (Coordinator Enable)"""
        try:
            new_ce = self.params.get('ce', 0)
            
            self.progress_signal.emit(10)
            
            if not self.enter_at_mode():
                self.error_signal.emit("無法進入 AT Command Mode")
                return
            
            self.progress_signal.emit(25)
            
            # 寫入新的 CE 值
            ce_desc = "Enabled" if new_ce == 1 else "Disabled"
            self.log_signal.emit(f"寫入新 CE 值: {new_ce} ({ce_desc})...")
            response = self.send_command(f'ATCE{new_ce}\r')
            self.log_signal.emit(f"ATCE 回應: {response}")
            
            self.progress_signal.emit(40)
            time.sleep(0.5)
            
            # 驗證寫入
            self.log_signal.emit("驗證 CE 值...")
            response = self.send_command('ATCE\r')
            self.log_signal.emit(f"驗證回應: {response}")
            
            self.progress_signal.emit(55)
            
            # 寫入到 Flash
            self.log_signal.emit("寫入到 Flash (ATWR)...")
            response = self.send_command('ATWR\r')
            self.log_signal.emit(f"ATWR 回應: {response}")
            
            self.progress_signal.emit(70)
            time.sleep(0.5)
            
            # 套用變更
            self.log_signal.emit("套用變更 (ATAC)...")
            response = self.send_command('ATAC\r')
            self.log_signal.emit(f"ATAC 回應: {response}")
            
            self.progress_signal.emit(85)
            
            # 退出 AT Mode
            self.exit_at_mode()
            
            self.progress_signal.emit(100)
            self.finished_signal.emit({'success': True, 'message': f'CE 已更新為 {new_ce} ({ce_desc})'})
            
        except Exception as e:
            self.error_signal.emit(f"寫入 CE 時發生錯誤: {str(e)}")
            
    def write_ap(self):
        """寫入 AP (API Enable)"""
        try:
            new_ap = self.params.get('ap', 0)
            
            self.progress_signal.emit(10)
            
            if not self.enter_at_mode():
                self.error_signal.emit("無法進入 AT Command Mode")
                return
            
            self.progress_signal.emit(25)
            
            # 寫入新的 AP 值
            ap_desc = "API Enabled" if new_ap == 1 else "Transparent Mode"
            self.log_signal.emit(f"寫入新 AP 值: {new_ap} ({ap_desc})...")
            response = self.send_command(f'ATAP{new_ap}\r')
            self.log_signal.emit(f"ATAP 回應: {response}")
            
            self.progress_signal.emit(40)
            time.sleep(0.5)
            
            # 驗證寫入
            self.log_signal.emit("驗證 AP 值...")
            response = self.send_command('ATAP\r')
            self.log_signal.emit(f"驗證回應: {response}")
            
            self.progress_signal.emit(55)
            
            # 寫入到 Flash
            self.log_signal.emit("寫入到 Flash (ATWR)...")
            response = self.send_command('ATWR\r')
            self.log_signal.emit(f"ATWR 回應: {response}")
            
            self.progress_signal.emit(70)
            time.sleep(0.5)
            
            # 套用變更
            self.log_signal.emit("套用變更 (ATAC)...")
            response = self.send_command('ATAC\r')
            self.log_signal.emit(f"ATAC 回應: {response}")
            
            self.progress_signal.emit(85)
            
            # 退出 AT Mode
            self.exit_at_mode()
            
            self.progress_signal.emit(100)
            self.finished_signal.emit({'success': True, 'message': f'AP 已更新為 {new_ap} ({ap_desc})'})
            
        except Exception as e:
            self.error_signal.emit(f"寫入 AP 時發生錯誤: {str(e)}")
    
    def write_all_parameters(self):
        """寫入所有參數 (PAN ID, JV, Baud Rate, CE, AP)"""
        try:
            new_panid = self.params.get('panid')
            new_jv = self.params.get('jv')
            new_baudrate = self.params.get('baudrate')
            new_ce = self.params.get('ce')
            new_ap = self.params.get('ap')
            
            self.log_signal.emit("開始全部寫入...")
            self.progress_signal.emit(5)
            
            if not self.enter_at_mode():
                self.error_signal.emit("無法進入 AT Command Mode")
                return
            
            self.progress_signal.emit(10)
            
            # 讀取原始 Baud Rate 以判斷是否有變更
            self.log_signal.emit("讀取原始 Baud Rate...")
            response = self.send_command('ATBD\r')
            try:
                original_bd_index = int(response.strip())
                original_baudrate = self.BAUD_RATE_MAP.get(original_bd_index, 9600)
            except:
                original_baudrate = 9600
            
            self.progress_signal.emit(15)
            
            # 1. 寫入 PAN ID
            self.log_signal.emit(f"[1/5] 寫入 PAN ID: 0x{new_panid:08X}...")
            response = self.send_command(f'ATID{new_panid:X}\r')
            self.log_signal.emit(f"ATID 回應: {response}")
            time.sleep(0.3)
            
            self.progress_signal.emit(25)
            
            # 2. 寫入 JV
            self.log_signal.emit(f"[2/5] 寫入 JV: {new_jv}...")
            response = self.send_command(f'ATJV{new_jv}\r')
            self.log_signal.emit(f"ATJV 回應: {response}")
            time.sleep(0.3)
            
            self.progress_signal.emit(40)
            
            # 3. 寫入 CE
            ce_desc = "Enabled" if new_ce == 1 else "Disabled"
            self.log_signal.emit(f"[3/5] 寫入 CE: {new_ce} ({ce_desc})...")
            response = self.send_command(f'ATCE{new_ce}\r')
            self.log_signal.emit(f"ATCE 回應: {response}")
            time.sleep(0.3)
            
            self.progress_signal.emit(55)
            
            # 4. 寫入 AP
            ap_desc = "API Enabled" if new_ap == 1 else "Transparent Mode"
            self.log_signal.emit(f"[4/5] 寫入 AP: {new_ap} ({ap_desc})...")
            response = self.send_command(f'ATAP{new_ap}\r')
            self.log_signal.emit(f"ATAP 回應: {response}")
            time.sleep(0.3)
            
            self.progress_signal.emit(65)
            
            # 5. 寫入 Baud Rate (最後寫入，因為可能會影響通訊)
            bd_index = self.BAUD_RATE_INDEX.get(new_baudrate, 3)
            self.log_signal.emit(f"[5/5] 寫入 Baud Rate: {new_baudrate} (index: {bd_index})...")
            response = self.send_command(f'ATBD{bd_index}\r')
            self.log_signal.emit(f"ATBD 回應: {response}")
            time.sleep(0.3)
            
            self.progress_signal.emit(75)
            
            # 寫入到 Flash
            self.log_signal.emit("寫入到 Flash (ATWR)...")
            response = self.send_command('ATWR\r')
            self.log_signal.emit(f"ATWR 回應: {response}")
            time.sleep(0.5)
            
            self.progress_signal.emit(85)
            
            # 套用變更
            self.log_signal.emit("套用變更 (ATAC)...")
            response = self.send_command('ATAC\r')
            self.log_signal.emit(f"ATAC 回應: {response}")
            time.sleep(0.3)
            
            self.progress_signal.emit(92)
            
            # 退出 AT Mode
            self.exit_at_mode()
            
            self.progress_signal.emit(100)
            
            # 判斷 Baud Rate 是否有變更
            baudrate_changed = (new_baudrate != original_baudrate)
            
            self.finished_signal.emit({
                'success': True, 
                'message': '所有參數已成功寫入',
                'baudrate_changed': baudrate_changed,
                'new_baudrate': new_baudrate
            })
            
        except Exception as e:
            self.error_signal.emit(f"全部寫入時發生錯誤: {str(e)}")
            
    def auto_detect_baudrate(self):
        """自動偵測 XBee 的 Baud Rate"""
        baud_rates = [9600, 115200, 57600, 38400, 19200, 4800, 2400, 1200, 230400]
        
        for i, baudrate in enumerate(baud_rates):
            if not self.running:
                return
                
            progress = int((i + 1) / len(baud_rates) * 100)
            self.progress_signal.emit(progress)
            
            self.log_signal.emit(f"嘗試 Baud Rate: {baudrate}...")
            
            try:
                self.serial_port.baudrate = baudrate
                time.sleep(0.5)
                
                # 清空緩衝區
                self.serial_port.reset_input_buffer()
                self.serial_port.reset_output_buffer()
                
                # 嘗試進入 AT Mode
                time.sleep(1)
                self.serial_port.write(b'+++')
                time.sleep(2)
                
                response = b''
                while self.serial_port.in_waiting:
                    response += self.serial_port.read(self.serial_port.in_waiting)
                    time.sleep(0.02)
                
                response_str = response.decode('utf-8', errors='ignore').strip()
                
                if 'OK' in response_str:
                    self.log_signal.emit(f"✓ 偵測到 XBee，Baud Rate: {baudrate}")
                    
                    # 退出 AT Mode
                    self.send_command('ATCN\r')
                    
                    self.finished_signal.emit({
                        'success': True,
                        'baudrate': baudrate,
                        'message': f'偵測成功！XBee Baud Rate: {baudrate}'
                    })
                    return
                    
            except Exception as e:
                self.log_signal.emit(f"  錯誤: {str(e)}")
                
        self.error_signal.emit("無法偵測到 XBee，請檢查連接")


class XBeeConfiguratorGUI(QMainWindow):
    """XBee 參數設定工具主視窗"""
    
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.worker = None
        self.init_ui()
        self.refresh_ports()
        
    def init_ui(self):
        """初始化使用者介面"""
        self.setWindowTitle("XBee 參數設定工具 v1.96")
        self.setMinimumSize(840, 750)
        
        # ============================================================
        # 顏色配置區域 - 修改這裡可以變更整體配色
        # ============================================================
        # 主要顏色
        COLOR_PRIMARY = "#3498db"        # 主色調 (藍色) - 邊框、按鈕
        COLOR_PRIMARY_HOVER = "#2980b9"  # 主色調懸停
        COLOR_PRIMARY_PRESSED = "#21618c" # 主色調按下
        
        # 背景顏色
        COLOR_BG_MAIN = "#f5f5f5"        # 主視窗背景 (淺灰)
        COLOR_BG_WHITE = "white"          # 白色背景
        COLOR_BG_INPUT = "white"          # 輸入框背景
        COLOR_BG_READONLY = "#ecf0f1"     # 唯讀欄位背景 (淺灰)
        COLOR_BG_DISABLED = "#bdc3c7"     # 停用狀態背景
        
        # 文字顏色
        COLOR_TEXT_DARK = "#2c3e50"       # 深色文字 (標籤、標題)
        COLOR_TEXT_WHITE = "white"        # 白色文字 (按鈕)
        COLOR_TEXT_INPUT = "#2c3e50"      # 輸入框文字
        
        # 邊框顏色
        COLOR_BORDER = "#bdc3c7"          # 一般邊框 (灰色)
        COLOR_BORDER_FOCUS = "#3498db"    # 聚焦邊框 (藍色)
        
        # 狀態顏色
        COLOR_SUCCESS = "#27ae60"         # 成功/已連接 (綠色)
        COLOR_ERROR = "#e74c3c"           # 錯誤/未連接 (紅色)
        
        # 通訊日誌區域
        COLOR_LOG_BG = "#2c3e50"          # 日誌背景 (深藍灰)
        COLOR_LOG_TEXT = "#2ecc71"        # 日誌文字 (綠色)
        
        # 下拉選單顏色
        COLOR_COMBO_BG = "white"          # 下拉選單背景
        COLOR_COMBO_TEXT = "#2c3e50"      # 下拉選單文字
        COLOR_COMBO_ITEM_BG = "white"     # 下拉選項背景
        COLOR_COMBO_ITEM_TEXT = "#2c3e50" # 下拉選項文字
        COLOR_COMBO_HOVER_BG = "#3498db"  # 下拉選項懸停背景
        COLOR_COMBO_HOVER_TEXT = "white"  # 下拉選項懸停文字
        # ============================================================
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLOR_BG_MAIN};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLOR_PRIMARY};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 5px;
                background-color: {COLOR_BG_WHITE};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px;
                color: {COLOR_TEXT_DARK};
            }}
            QPushButton {{
                background-color: {COLOR_PRIMARY};
                color: {COLOR_TEXT_WHITE};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLOR_PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {COLOR_PRIMARY_PRESSED};
            }}
            QPushButton:disabled {{
                background-color: {COLOR_BG_DISABLED};
            }}
            QLineEdit, QSpinBox {{
                padding: 6px;
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                background-color: {COLOR_BG_INPUT};
                color: {COLOR_TEXT_INPUT};
            }}
            QLineEdit:focus, QSpinBox:focus {{
                border: 2px solid {COLOR_BORDER_FOCUS};
            }}
            QComboBox {{
                padding: 6px;
                padding-right: 20px;
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                background-color: {COLOR_COMBO_BG};
                color: {COLOR_COMBO_TEXT};
            }}
            QComboBox:focus {{
                border: 2px solid {COLOR_BORDER_FOCUS};
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLOR_COMBO_ITEM_BG};
                color: {COLOR_COMBO_ITEM_TEXT};
                selection-background-color: {COLOR_COMBO_HOVER_BG};
                selection-color: {COLOR_COMBO_HOVER_TEXT};
                border: 1px solid {COLOR_BORDER};
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px;
                min-height: 25px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {COLOR_COMBO_HOVER_BG};
                color: {COLOR_COMBO_HOVER_TEXT};
            }}
            QTextEdit {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                background-color: {COLOR_LOG_BG};
                color: {COLOR_LOG_TEXT};
                font-family: Consolas, Monaco, monospace;
            }}
            QLabel {{
                color: {COLOR_TEXT_DARK};
            }}
            QScrollBar:vertical {{
                border: none;
                background: #f0f0f0;
                width: 12px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLOR_PRIMARY};
                min-height: 30px;
                border-radius: 1px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {COLOR_PRIMARY_HOVER};
            }}
            QProgressBar {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                background-color: #e0e0e0;
                text-align: center;
                color: {COLOR_TEXT_DARK};
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_PRIMARY};
                border-radius: 3px;
            }}
        """)
        
        # 主要 Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 標題
        title_label = QLabel("🔧 Digi XBee 參數設定工具")
        title_label.setFont(QFont("Microsoft JhengHei", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; padding: 0px;")
        main_layout.addWidget(title_label)
        
        # COM Port 設定區域
        port_group = QGroupBox("📡 COM Port 設定")
        port_layout = QGridLayout()
        port_layout.setSpacing(10)
        
        # COM Port 選擇
        port_layout.addWidget(QLabel("COM Port:"), 0, 0)
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        port_layout.addWidget(self.port_combo, 0, 1)
        
        self.refresh_btn = QPushButton("🔄 重新整理")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        port_layout.addWidget(self.refresh_btn, 0, 2)
        
        # Baud Rate
        port_layout.addWidget(QLabel("Baud Rate:"), 1, 0)
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(['1200', '2400', '4800', '9600', '19200', '38400', '57600', '115200', '230400'])
        self.baudrate_combo.setCurrentText('9600')
        port_layout.addWidget(self.baudrate_combo, 1, 1)
        
        # 資料格式
        port_layout.addWidget(QLabel("資料格式:"), 1, 2)
        self.data_bits_combo = QComboBox()
        self.data_bits_combo.addItems(['8', '7', '6', '5'])
        port_layout.addWidget(self.data_bits_combo, 1, 3)
        
        port_layout.addWidget(QLabel("同位檢查:"), 1, 4)
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(['None', 'Even', 'Odd', 'Mark', 'Space'])
        port_layout.addWidget(self.parity_combo, 1, 5)
        
        port_layout.addWidget(QLabel("停止位元:"), 1, 6)
        self.stop_bits_combo = QComboBox()
        self.stop_bits_combo.addItems(['1', '1.5', '2'])
        port_layout.addWidget(self.stop_bits_combo, 1, 7)
        
        # 連接按鈕
        btn_layout = QHBoxLayout()
        
        # 先放「自動偵測 Baud Rate」按鈕
        self.auto_detect_btn = QPushButton("🔍 自動偵測 Baud Rate")
        self.auto_detect_btn.clicked.connect(self.auto_detect_baudrate)
        btn_layout.addWidget(self.auto_detect_btn)
        
        # 再放「連接」按鈕
        self.connect_btn = QPushButton("🔌 連接")
        self.connect_btn.clicked.connect(self.toggle_connection)
        # 初始狀態：紅色（顯示連接 - 等待連接）
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e7723c;
            }
        """)
        btn_layout.addWidget(self.connect_btn)
        
        self.connection_status = QLabel("● 未連接")
        self.connection_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
        btn_layout.addWidget(self.connection_status)
        btn_layout.addStretch()
        
        port_layout.addLayout(btn_layout, 0, 3, 1, 6)
        port_group.setLayout(port_layout)
        main_layout.addWidget(port_group)
        
        # XBee 參數顯示區域
        param_group = QGroupBox("📋 XBee 參數")
        param_group_layout = QVBoxLayout()
        param_group_layout.setContentsMargins(10, 10, 10, 10)
        
        # 建立捲動區域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # ============================================================
        # XBee 參數區域高度設定
        # 方法1: setFixedHeight(高度) - 固定高度，不會隨視窗大小改變
        # 方法2: setMinimumHeight(高度) - 最小高度，可以更大
        # 方法3: setMaximumHeight(高度) - 最大高度，可以更小
        # ============================================================
        scroll_area.setFixedHeight(275)  # 固定高度為 230 像素，可依需求調整
        #scroll_area.setMaximumHeight(300)
        #scroll_area.setMinimumHeight(100)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
        """)
        
        # 參數容器 - 使用 QGridLayout
        param_container = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        grid_layout.setContentsMargins(10, 10, 10, 10)
        
        # 設定列寬比例
        grid_layout.setColumnStretch(0, 0)  # 標籤 - 固定
        grid_layout.setColumnStretch(1, 1)  # 顯示值 - 可伸展
        grid_layout.setColumnStretch(2, 0)  # 新值標籤 - 固定
        grid_layout.setColumnStretch(3, 0)  # 輸入框 - 固定
        grid_layout.setColumnStretch(4, 0)  # 按鈕 - 固定
        
        row = 0
        
        # MAC Address (唯讀) - 跨越整列
        mac_label = QLabel("MAC Address:")
        mac_label.setFixedWidth(100)
        grid_layout.addWidget(mac_label, row, 0)
        self.mac_display = QLineEdit()
        self.mac_display.setReadOnly(True)
        self.mac_display.setPlaceholderText("讀取後顯示")
        self.mac_display.setStyleSheet("background-color: #ecf0f1;")
        grid_layout.addWidget(self.mac_display, row, 1, 1, 3)  # 跨3列 (欄位1-3)
        
        # 「全部寫入」按鈕 - 放在第5列
        self.write_all_btn = QPushButton("全部寫入")
        self.write_all_btn.clicked.connect(self.write_all_parameters)
        self.write_all_btn.setEnabled(False)
        self.write_all_btn.setFixedWidth(100)
        self.write_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        grid_layout.addWidget(self.write_all_btn, row, 4)
        row += 1
        
        # 分隔線
        # line1 = QFrame()
        # line1.setFrameShape(QFrame.Shape.HLine)
        # line1.setStyleSheet("background-color: #bdc3c7;")
        # grid_layout.addWidget(line1, row, 0, 1, 5)  # 跨5列
        # row += 1
        
        # PAN ID
        panid_label = QLabel("PAN ID:")
        grid_layout.addWidget(panid_label, row, 0)
        self.panid_display = QLineEdit()
        self.panid_display.setReadOnly(True)
        self.panid_display.setPlaceholderText("讀取後顯示")
        self.panid_display.setStyleSheet("background-color: #ecf0f1;")
        grid_layout.addWidget(self.panid_display, row, 1)
        new_panid_label = QLabel("新值(HEX):")
        grid_layout.addWidget(new_panid_label, row, 2)
        self.new_panid_input = QLineEdit()
        self.new_panid_input.setPlaceholderText("如: 12345678")
        self.new_panid_input.setMaxLength(8)
        self.new_panid_input.setFixedWidth(150)
        self.new_panid_input.textChanged.connect(self.on_panid_input_changed)
        grid_layout.addWidget(self.new_panid_input, row, 3)
        self.write_panid_btn = QPushButton("寫入")
        self.write_panid_btn.clicked.connect(self.write_panid)
        self.write_panid_btn.setEnabled(False)
        self.write_panid_btn.setFixedWidth(100)
        grid_layout.addWidget(self.write_panid_btn, row, 4)
        row += 1
        
        # JV
        jv_label = QLabel("JV:")
        grid_layout.addWidget(jv_label, row, 0)
        self.jv_display = QLineEdit()
        self.jv_display.setReadOnly(True)
        self.jv_display.setPlaceholderText("讀取後顯示")
        self.jv_display.setStyleSheet("background-color: #ecf0f1;")
        grid_layout.addWidget(self.jv_display, row, 1)
        new_jv_label = QLabel("新值(0~1):")
        grid_layout.addWidget(new_jv_label, row, 2)
        self.new_jv_combo = QComboBox()
        self.new_jv_combo.addItems(['0', '1'])
        self.new_jv_combo.setFixedWidth(150)
        grid_layout.addWidget(self.new_jv_combo, row, 3)
        self.write_jv_btn = QPushButton("寫入")
        self.write_jv_btn.clicked.connect(self.write_jv)
        self.write_jv_btn.setEnabled(False)
        self.write_jv_btn.setFixedWidth(100)
        grid_layout.addWidget(self.write_jv_btn, row, 4)
        row += 1
        
        # Baud Rate
        bd_label = QLabel("Baud Rate:")
        grid_layout.addWidget(bd_label, row, 0)
        self.xbee_baudrate_display = QLineEdit()
        self.xbee_baudrate_display.setReadOnly(True)
        self.xbee_baudrate_display.setPlaceholderText("讀取後顯示")
        self.xbee_baudrate_display.setStyleSheet("background-color: #ecf0f1;")
        grid_layout.addWidget(self.xbee_baudrate_display, row, 1)
        new_bd_label = QLabel("新值(0~8):")
        grid_layout.addWidget(new_bd_label, row, 2)
        self.new_baudrate_combo = QComboBox()
        self.new_baudrate_combo.addItems(['1200', '2400', '4800', '9600', '19200', '38400', '57600', '115200', '230400'])
        self.new_baudrate_combo.setCurrentText('9600')
        self.new_baudrate_combo.setFixedWidth(150)
        grid_layout.addWidget(self.new_baudrate_combo, row, 3)
        self.write_baudrate_btn = QPushButton("寫入")
        self.write_baudrate_btn.clicked.connect(self.write_baudrate)
        self.write_baudrate_btn.setEnabled(False)
        self.write_baudrate_btn.setFixedWidth(100)
        grid_layout.addWidget(self.write_baudrate_btn, row, 4)
        row += 1
        
        # CE (Coordinator Enable)
        ce_label = QLabel("CE (Coordinator):")
        grid_layout.addWidget(ce_label, row, 0)
        self.ce_display = QLineEdit()
        self.ce_display.setReadOnly(True)
        self.ce_display.setPlaceholderText("讀取後顯示")
        self.ce_display.setStyleSheet("background-color: #ecf0f1;")
        grid_layout.addWidget(self.ce_display, row, 1)
        new_ce_label = QLabel("新值(0~1):")
        grid_layout.addWidget(new_ce_label, row, 2)
        self.new_ce_combo = QComboBox()
        self.new_ce_combo.addItem("Disabled [0]", 0)
        self.new_ce_combo.addItem("Enabled [1]", 1)
        self.new_ce_combo.setFixedWidth(150)
        grid_layout.addWidget(self.new_ce_combo, row, 3)
        self.write_ce_btn = QPushButton("寫入")
        self.write_ce_btn.clicked.connect(self.write_ce)
        self.write_ce_btn.setEnabled(False)
        self.write_ce_btn.setFixedWidth(100)
        grid_layout.addWidget(self.write_ce_btn, row, 4)
        row += 1
        
        # AP (API Enable)
        ap_label = QLabel("AP (API Mode):")
        grid_layout.addWidget(ap_label, row, 0)
        self.ap_display = QLineEdit()
        self.ap_display.setReadOnly(True)
        self.ap_display.setPlaceholderText("讀取後顯示")
        self.ap_display.setStyleSheet("background-color: #ecf0f1;")
        grid_layout.addWidget(self.ap_display, row, 1)
        new_ap_label = QLabel("新值(0~1):")
        grid_layout.addWidget(new_ap_label, row, 2)
        self.new_ap_combo = QComboBox()
        self.new_ap_combo.addItem("Transparent [0]", 0)
        self.new_ap_combo.addItem("API Mode [1]", 1)
        self.new_ap_combo.setFixedWidth(150)
        grid_layout.addWidget(self.new_ap_combo, row, 3)
        self.write_ap_btn = QPushButton("寫入")
        self.write_ap_btn.clicked.connect(self.write_ap)
        self.write_ap_btn.setEnabled(False)
        self.write_ap_btn.setFixedWidth(100)
        grid_layout.addWidget(self.write_ap_btn, row, 4)
        
        # 設定容器佈局
        param_container.setLayout(grid_layout)
        scroll_area.setWidget(param_container)
        param_group_layout.addWidget(scroll_area)
        param_group.setLayout(param_group_layout)
        main_layout.addWidget(param_group)
        
        # 操作按鈕
        action_layout = QHBoxLayout()
        
        self.read_btn = QPushButton("📖 讀取所有參數")
        self.read_btn.clicked.connect(self.read_parameters)
        self.read_btn.setEnabled(False)
        self.read_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                font-size: 14px;
                padding: 8px 24px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        action_layout.addWidget(self.read_btn)
        
        self.clear_btn = QPushButton("🗑️ 清除顯示")
        self.clear_btn.clicked.connect(self.clear_display)
        action_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(action_layout)
        
        # 進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)
        
        # 日誌區域
        log_group = QGroupBox("📝 通訊日誌")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(50)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # 狀態列
        self.statusBar().showMessage("就緒 - 請選擇 COM Port 並連接")
        
    def refresh_ports(self):
        """重新整理可用的 COM Port 列表"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            self.port_combo.addItem(f"{port.device} - {port.description}", port.device)
            
        if not ports:
            self.port_combo.addItem("未偵測到 COM Port", None)
            self.log("未偵測到任何 COM Port")
        else:
            self.log(f"偵測到 {len(ports)} 個 COM Port")
            
    def toggle_connection(self):
        """切換連接狀態"""
        if self.serial_port and self.serial_port.is_open:
            self.disconnect_port()
        else:
            self.connect_port()
            
    def connect_port(self):
        """連接到選定的 COM Port"""
        port = self.port_combo.currentData()
        if not port:
            QMessageBox.warning(self, "警告", "請選擇有效的 COM Port")
            return
            
        try:
            baudrate = int(self.baudrate_combo.currentText())
            data_bits = int(self.data_bits_combo.currentText())
            
            parity_map = {'None': 'N', 'Even': 'E', 'Odd': 'O', 'Mark': 'M', 'Space': 'S'}
            parity = parity_map[self.parity_combo.currentText()]
            
            stop_bits_map = {'1': 1, '1.5': 1.5, '2': 2}
            stop_bits = stop_bits_map[self.stop_bits_combo.currentText()]
            
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=data_bits,
                parity=parity,
                stopbits=stop_bits,
                timeout=2
            )
            
            self.connect_btn.setText("🔌 斷開")
            # 設定連接按鈕為綠色（連線狀態）- 顯示"斷開"
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #219a52;
                }
            """)
            self.connection_status.setText("● 已連接")
            self.connection_status.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.read_btn.setEnabled(True)
            # 連接成功後，所有寫入按鈕先禁用，必須讀取參數後才能啟用
            self.write_panid_btn.setEnabled(False)
            self.write_jv_btn.setEnabled(False)
            self.write_baudrate_btn.setEnabled(False)
            self.write_ce_btn.setEnabled(False)
            self.write_ap_btn.setEnabled(False)
            self.write_all_btn.setEnabled(False)
            
            self.log(f"已連接到 {port} (Baud Rate: {baudrate})")
            self.statusBar().showMessage(f"已連接: {port}")
            
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"無法連接到 COM Port: {str(e)}")
            self.log(f"連接失敗: {str(e)}")
            
    def disconnect_port(self):
        """斷開 COM Port 連接"""
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None
            
        self.connect_btn.setText("🔌 連接")
        # 設定連接按鈕為紅色（斷開狀態）- 顯示"連接"
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e7723c;
            }
        """)
        self.connection_status.setText("● 未連接")
        self.connection_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
        self.read_btn.setEnabled(False)
        self.write_panid_btn.setEnabled(False)
        self.write_jv_btn.setEnabled(False)
        self.write_baudrate_btn.setEnabled(False)
        self.write_ce_btn.setEnabled(False)
        self.write_ap_btn.setEnabled(False)
        self.write_all_btn.setEnabled(False)
        
        self.log("已斷開連接")
        self.statusBar().showMessage("已斷開連接")
        
    def auto_detect_baudrate(self):
        """自動偵測 XBee 的 Baud Rate"""
        port = self.port_combo.currentData()
        if not port:
            QMessageBox.warning(self, "警告", "請選擇有效的 COM Port")
            return
            
        # 如果已連接，先斷開
        if self.serial_port and self.serial_port.is_open:
            self.disconnect_port()
            
        try:
            # 建立臨時連接
            self.serial_port = serial.Serial(
                port=port,
                baudrate=9600,
                timeout=2
            )
            
            self.set_buttons_enabled(False)
            self.progress_bar.setValue(0)
            
            self.worker = XBeeWorker(self.serial_port, 'auto_detect')
            self.worker.log_signal.connect(self.log)
            self.worker.progress_signal.connect(self.progress_bar.setValue)
            self.worker.finished_signal.connect(self.on_auto_detect_finished)
            self.worker.error_signal.connect(self.on_error)
            self.worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"無法開啟 COM Port: {str(e)}")
            
    def on_auto_detect_finished(self, result):
        """自動偵測完成"""
        self.set_buttons_enabled(True)
        
        if result.get('success'):
            detected_baudrate = result.get('baudrate')
            self.baudrate_combo.setCurrentText(str(detected_baudrate))
            QMessageBox.information(self, "偵測成功", result.get('message'))
            self.log(f"自動偵測成功: {detected_baudrate}")
        
        # 斷開臨時連接
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None
            
    def read_parameters(self):
        """讀取 XBee 參數"""
        if not self.serial_port or not self.serial_port.is_open:
            QMessageBox.warning(self, "警告", "請先連接到 COM Port")
            return
            
        self.set_buttons_enabled(False)
        self.progress_bar.setValue(0)
        
        self.worker = XBeeWorker(self.serial_port, 'read')
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.finished_signal.connect(self.on_read_finished)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()
        
    def on_read_finished(self, result):
        """讀取完成"""
        self.set_buttons_enabled(True)
        
        # 更新顯示
        self.mac_display.setText(result.get('mac_address', 'N/A'))
        
        panid = result.get('panid', 'N/A')
        panid_hex = result.get('panid_hex', 'N/A')
        self.panid_display.setText(f"0x{panid_hex} (DEC: {panid})")
        if isinstance(panid, int):
            self.new_panid_input.setText(f"{panid:X}")
        
        self.jv_display.setText(str(result.get('jv', 'N/A')))
        jv = result.get('jv')
        if isinstance(jv, int):
            self.new_jv_combo.setCurrentText(str(jv))
        
        baudrate = result.get('baudrate', 'N/A')
        self.xbee_baudrate_display.setText(str(baudrate))
        if isinstance(baudrate, int):
            self.new_baudrate_combo.setCurrentText(str(baudrate))
        
        # CE (Coordinator Enable)
        ce = result.get('ce', 'N/A')
        if isinstance(ce, int):
            ce_desc = "Enabled" if ce == 1 else "Disabled"
            self.ce_display.setText(f"{ce} ({ce_desc})")
            self.new_ce_combo.setCurrentIndex(ce)
        else:
            self.ce_display.setText(str(ce))
        
        # AP (API Enable)
        ap = result.get('ap', 'N/A')
        if isinstance(ap, int):
            ap_desc = "API Enabled" if ap == 1 else "Transparent Mode"
            self.ap_display.setText(f"{ap} ({ap_desc})")
            # 只處理 0 和 1，其他值預設選擇 0
            self.new_ap_combo.setCurrentIndex(min(ap, 1))
        else:
            self.ap_display.setText(str(ap))
        
        self.log("參數讀取完成")
        self.statusBar().showMessage("參數讀取完成")
        
        # 讀取成功後，啟用所有寫入按鈕
        self.write_panid_btn.setEnabled(True)
        self.write_jv_btn.setEnabled(True)
        self.write_baudrate_btn.setEnabled(True)
        self.write_ce_btn.setEnabled(True)
        self.write_ap_btn.setEnabled(True)
        self.write_all_btn.setEnabled(True)
        
    def on_panid_input_changed(self, text):
        """當 PAN ID 輸入改變時，過濾非十六進制字元"""
        # 只允許十六進制字元
        filtered = ''.join(c for c in text.upper() if c in '0123456789ABCDEF')
        if filtered != text.upper():
            self.new_panid_input.setText(filtered)
            
    def write_panid(self):
        """寫入 PAN ID"""
        if not self.serial_port or not self.serial_port.is_open:
            return
        
        # 取得十六進制輸入
        hex_input = self.new_panid_input.text().strip().upper()
        if not hex_input:
            QMessageBox.warning(self, "警告", "請輸入 PAN ID (十六進制)")
            return
            
        try:
            new_panid = int(hex_input, 16)
            if new_panid > 0xFFFFFFFF:
                QMessageBox.warning(self, "警告", "PAN ID 超出範圍 (最大 FFFFFFFF)")
                return
        except ValueError:
            QMessageBox.warning(self, "警告", "請輸入有效的十六進制數值")
            return
        
        reply = QMessageBox.question(
            self, '確認', 
            f'確定要將 PAN ID 更新為 0x{new_panid:08X} (DEC: {new_panid}) 嗎?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.set_buttons_enabled(False)
            self.progress_bar.setValue(0)
            
            self.worker = XBeeWorker(self.serial_port, 'write_panid', {'panid': new_panid})
            self.worker.log_signal.connect(self.log)
            self.worker.progress_signal.connect(self.progress_bar.setValue)
            self.worker.finished_signal.connect(self.on_write_finished)
            self.worker.error_signal.connect(self.on_error)
            self.worker.start()
            
    def write_jv(self):
        """寫入 JV 值"""
        if not self.serial_port or not self.serial_port.is_open:
            return
            
        new_jv = int(self.new_jv_combo.currentText())
        
        reply = QMessageBox.question(
            self, '確認', 
            f'確定要將 JV 更新為 {new_jv} 嗎?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.set_buttons_enabled(False)
            self.progress_bar.setValue(0)
            
            self.worker = XBeeWorker(self.serial_port, 'write_jv', {'jv': new_jv})
            self.worker.log_signal.connect(self.log)
            self.worker.progress_signal.connect(self.progress_bar.setValue)
            self.worker.finished_signal.connect(self.on_write_finished)
            self.worker.error_signal.connect(self.on_error)
            self.worker.start()
            
    def write_baudrate(self):
        """寫入 Baud Rate"""
        if not self.serial_port or not self.serial_port.is_open:
            return
            
        new_baudrate = int(self.new_baudrate_combo.currentText())
        
        reply = QMessageBox.question(
            self, '確認', 
            f'確定要將 Baud Rate 更新為 {new_baudrate} 嗎?\n\n'
            f'注意：更新後需要以新的 Baud Rate 重新連接!',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.set_buttons_enabled(False)
            self.progress_bar.setValue(0)
            
            self.worker = XBeeWorker(self.serial_port, 'write_baudrate', {'baudrate': new_baudrate})
            self.worker.log_signal.connect(self.log)
            self.worker.progress_signal.connect(self.progress_bar.setValue)
            self.worker.finished_signal.connect(self.on_baudrate_write_finished)
            self.worker.error_signal.connect(self.on_error)
            self.worker.start()
            
    def write_ce(self):
        """寫入 CE (Coordinator Enable)"""
        if not self.serial_port or not self.serial_port.is_open:
            return
            
        new_ce = self.new_ce_combo.currentData()
        ce_desc = "Enabled" if new_ce == 1 else "Disabled"
        
        reply = QMessageBox.question(
            self, '確認', 
            f'確定要將 CE (Coordinator Enable) 更新為 {new_ce} ({ce_desc}) 嗎?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.set_buttons_enabled(False)
            self.progress_bar.setValue(0)
            
            self.worker = XBeeWorker(self.serial_port, 'write_ce', {'ce': new_ce})
            self.worker.log_signal.connect(self.log)
            self.worker.progress_signal.connect(self.progress_bar.setValue)
            self.worker.finished_signal.connect(self.on_write_finished)
            self.worker.error_signal.connect(self.on_error)
            self.worker.start()
            
    def write_ap(self):
        """寫入 AP (API Enable)"""
        if not self.serial_port or not self.serial_port.is_open:
            return
            
        new_ap = self.new_ap_combo.currentData()
        ap_desc = "API Enabled" if new_ap == 1 else "Transparent Mode"
        
        reply = QMessageBox.question(
            self, '確認', 
            f'確定要將 AP (API Mode) 更新為 {new_ap} ({ap_desc}) 嗎?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.set_buttons_enabled(False)
            self.progress_bar.setValue(0)
            
            self.worker = XBeeWorker(self.serial_port, 'write_ap', {'ap': new_ap})
            self.worker.log_signal.connect(self.log)
            self.worker.progress_signal.connect(self.progress_bar.setValue)
            self.worker.finished_signal.connect(self.on_write_finished)
            self.worker.error_signal.connect(self.on_error)
            self.worker.start()
    
    def write_all_parameters(self):
        """全部寫入 - 依序寫入所有參數"""
        if not self.serial_port or not self.serial_port.is_open:
            return
        
        # 收集所有參數
        # PAN ID
        hex_input = self.new_panid_input.text().strip().upper()
        if not hex_input:
            QMessageBox.warning(self, "警告", "請輸入 PAN ID 值")
            return
        try:
            new_panid = int(hex_input, 16)
            if new_panid > 0xFFFFFFFF:
                QMessageBox.warning(self, "警告", "PAN ID 必須在 0x00000000 ~ 0xFFFFFFFF 範圍內")
                return
        except ValueError:
            QMessageBox.warning(self, "警告", "PAN ID 格式錯誤，請輸入有效的十六進制數值")
            return
        
        # JV
        new_jv = int(self.new_jv_combo.currentText())
        
        # Baud Rate
        new_baudrate = int(self.new_baudrate_combo.currentText())
        
        # CE
        new_ce = self.new_ce_combo.currentData()
        ce_desc = "Enabled" if new_ce == 1 else "Disabled"
        
        # AP
        new_ap = self.new_ap_combo.currentData()
        ap_desc = "API Enabled" if new_ap == 1 else "Transparent Mode"
        
        # 確認對話框
        reply = QMessageBox.question(
            self, '確認全部寫入', 
            f'確定要寫入以下所有參數嗎?\n\n'
            f'• PAN ID: 0x{new_panid:08X} (DEC: {new_panid})\n'
            f'• JV: {new_jv}\n'
            f'• Baud Rate: {new_baudrate}\n'
            f'• CE: {new_ce} ({ce_desc})\n'
            f'• AP: {new_ap} ({ap_desc})\n\n'
            f'注意：若 Baud Rate 有變更，寫入完成後需要重新連接!',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.set_buttons_enabled(False)
            self.progress_bar.setValue(0)
            
            # 準備所有參數
            all_params = {
                'panid': new_panid,
                'jv': new_jv,
                'baudrate': new_baudrate,
                'ce': new_ce,
                'ap': new_ap
            }
            
            self.worker = XBeeWorker(self.serial_port, 'write_all', all_params)
            self.worker.log_signal.connect(self.log)
            self.worker.progress_signal.connect(self.progress_bar.setValue)
            self.worker.finished_signal.connect(self.on_write_all_finished)
            self.worker.error_signal.connect(self.on_error)
            self.worker.start()
    
    def on_write_all_finished(self, result):
        """全部寫入完成"""
        self.set_buttons_enabled(True)
        
        if result.get('success'):
            # 檢查是否有 Baud Rate 變更
            baudrate_changed = result.get('baudrate_changed', False)
            new_baudrate = result.get('new_baudrate')
            
            if baudrate_changed:
                QMessageBox.information(
                    self, "全部寫入完成", 
                    f"所有參數已成功寫入!\n\n"
                    f"由於 Baud Rate 已變更為 {new_baudrate}，\n"
                    f"請將連接 Baud Rate 更改為 {new_baudrate} 並重新連接。"
                )
                # 自動更新連接設定
                self.baudrate_combo.setCurrentText(str(new_baudrate))
                # 斷開連接
                self.disconnect_port()
            else:
                QMessageBox.information(self, "全部寫入完成", "所有參數已成功寫入!")
                # 重新讀取參數
                QTimer.singleShot(1000, self.read_parameters)
            
            self.log("全部參數寫入完成")
        else:
            error_msg = result.get('message', '寫入失敗')
            QMessageBox.critical(self, "寫入失敗", error_msg)
            self.log(f"全部寫入失敗: {error_msg}")
            
    def on_write_finished(self, result):
        """寫入完成"""
        self.set_buttons_enabled(True)
        
        if result.get('success'):
            QMessageBox.information(self, "成功", result.get('message'))
            self.log(result.get('message'))
            # 重新讀取參數
            QTimer.singleShot(1000, self.read_parameters)
        else:
            self.log("寫入失敗")
            
    def on_baudrate_write_finished(self, result):
        """Baud Rate 寫入完成"""
        self.set_buttons_enabled(True)
        
        if result.get('success'):
            new_baudrate = result.get('new_baudrate')
            QMessageBox.information(
                self, "成功", 
                f"{result.get('message')}\n\n"
                f"請將連接 Baud Rate 更改為 {new_baudrate} 並重新連接。"
            )
            self.log(result.get('message'))
            
            # 自動更新連接設定
            self.baudrate_combo.setCurrentText(str(new_baudrate))
            
            # 斷開連接
            self.disconnect_port()
        else:
            self.log("寫入失敗")
            
    def on_error(self, error_msg):
        """處理錯誤"""
        self.set_buttons_enabled(True)
        QMessageBox.critical(self, "錯誤", error_msg)
        self.log(f"錯誤: {error_msg}")
        
    def set_buttons_enabled(self, enabled):
        """設定按鈕啟用狀態"""
        self.read_btn.setEnabled(enabled and self.serial_port and self.serial_port.is_open)
        self.write_panid_btn.setEnabled(enabled and self.serial_port and self.serial_port.is_open)
        self.write_jv_btn.setEnabled(enabled and self.serial_port and self.serial_port.is_open)
        self.write_baudrate_btn.setEnabled(enabled and self.serial_port and self.serial_port.is_open)
        self.write_ce_btn.setEnabled(enabled and self.serial_port and self.serial_port.is_open)
        self.write_ap_btn.setEnabled(enabled and self.serial_port and self.serial_port.is_open)
        self.write_all_btn.setEnabled(enabled and self.serial_port and self.serial_port.is_open)
        self.connect_btn.setEnabled(enabled)
        self.refresh_btn.setEnabled(enabled)
        self.auto_detect_btn.setEnabled(enabled)
        
    def clear_display(self):
        """清除顯示"""
        self.mac_display.clear()
        self.panid_display.clear()
        self.jv_display.clear()
        self.xbee_baudrate_display.clear()
        self.ce_display.clear()
        self.ap_display.clear()
        self.log_text.clear()
        self.progress_bar.setValue(0)
        self.log("顯示已清除")
        
    def log(self, message):
        """添加日誌訊息"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # 自動滾動到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def closeEvent(self, event):
        """關閉視窗時清理資源"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # ============================================================
    # 強制使用淺色主題調色板，避免受 Windows 深色主題影響
    # ============================================================
    light_palette = QPalette()
    
    # 基本顏色
    light_palette.setColor(QPalette.ColorRole.Window, QColor(245, 245, 245))           # 視窗背景
    light_palette.setColor(QPalette.ColorRole.WindowText, QColor(44, 62, 80))          # 視窗文字
    light_palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))             # 輸入框背景
    light_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))    # 交替背景
    light_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))      # 工具提示背景
    light_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(44, 62, 80))         # 工具提示文字
    light_palette.setColor(QPalette.ColorRole.Text, QColor(44, 62, 80))                # 一般文字
    light_palette.setColor(QPalette.ColorRole.Button, QColor(52, 152, 219))            # 按鈕背景
    light_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))       # 按鈕文字
    light_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))           # 明亮文字
    light_palette.setColor(QPalette.ColorRole.Link, QColor(52, 152, 219))              # 連結
    light_palette.setColor(QPalette.ColorRole.Highlight, QColor(52, 152, 219))         # 選中背景
    light_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))  # 選中文字
    
    # 停用狀態顏色
    light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(127, 127, 127))
    light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
    light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))
    
    app.setPalette(light_palette)
    # ============================================================
    
    # 設定應用程式字型
    font = QFont("Microsoft JhengHei", 10)
    app.setFont(font)
    
    window = XBeeConfiguratorGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
