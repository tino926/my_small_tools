#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MMEX Kivy App - Final Stage: Complete Integration

這是最終階段的版本，包含完整的UI組件整合
"""

import logging
from typing import Optional, Dict, Any, List
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.clock import Clock

# 進階日誌配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MMEXKivyAppFinal(App):
    """MMEX Kivy應用程式 - 最終階段：完整整合"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "MMEX Reader - Complete Integration"
        self.click_count = 0
        self.state = "ready"
        self.transactions = []
        logger.info("MMEX Kivy App Final initialized with complete integration")
    
    def build(self):
        """構建完整整合的UI"""
        # 創建主佈局
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 添加標題
        title_label = Label(
            text="MMEX Reader - Complete Integration",
            size_hint_y=0.1,
            font_size='20sp',
            bold=True
        )
        main_layout.add_widget(title_label)
        
        # 創建輸入區域
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=5)
        
        self.amount_input = TextInput(
            hint_text="Amount",
            multiline=False,
            size_hint_x=0.3
        )
        input_layout.add_widget(self.amount_input)
        
        self.description_input = TextInput(
            hint_text="Description",
            multiline=False,
            size_hint_x=0.5
        )
        input_layout.add_widget(self.description_input)
        
        add_button = Button(
            text="Add Transaction",
            size_hint_x=0.2
        )
        add_button.bind(on_press=self.add_transaction)
        input_layout.add_widget(add_button)
        
        main_layout.add_widget(input_layout)
        
        # 狀態顯示
        self.status_label = Label(
            text="Ready - Enter transaction details",
            size_hint_y=0.1,
            font_size='14sp'
        )
        main_layout.add_widget(self.status_label)
        
        # 交易列表顯示
        self.transactions_label = Label(
            text="Transactions: 0",
            size_hint_y=0.1,
            font_size='12sp'
        )
        main_layout.add_widget(self.transactions_label)
        
        # 測試按鈕
        test_button = Button(
            text="Test UI Components",
            size_hint_y=0.1
        )
        test_button.bind(on_press=self.test_components)
        main_layout.add_widget(test_button)
        
        # 設置定時器更新狀態
        Clock.schedule_interval(self.update_status, 2.0)
        
        logger.info("Complete integrated UI built successfully")
        return main_layout
    
    def add_transaction(self, instance):
        """添加交易記錄"""
        amount = self.amount_input.text.strip()
        description = self.description_input.text.strip()
        
        if amount and description:
            try:
                transaction = {
                    'amount': float(amount),
                    'description': description,
                    'timestamp': Clock.get_boottime()
                }
                self.transactions.append(transaction)
                
                # 清空輸入框
                self.amount_input.text = ""
                self.description_input.text = ""
                
                self.status_label.text = f"Added transaction: {amount} - {description}"
                self.transactions_label.text = f"Transactions: {len(self.transactions)}"
                
                logger.info(f"Transaction added: {amount} - {description}")
            except ValueError:
                self.status_label.text = "Error: Invalid amount format"
                logger.error("Invalid amount format")
        else:
            self.status_label.text = "Please enter both amount and description"
    
    def test_components(self, instance):
        """測試UI組件"""
        self.click_count += 1
        self.status_label.text = f"UI Components tested! Count: {self.click_count}"
        logger.info(f"UI components tested, count: {self.click_count}")
    
    def update_status(self, dt):
        """定期更新狀態"""
        if self.transactions:
            total_amount = sum(t['amount'] for t in self.transactions)
            self.status_label.text = f"Total: {total_amount:.2f} from {len(self.transactions)} transactions"
    
    def on_start(self):
        """應用程式啟動時調用"""
        logger.info("MMEX Kivy App Final started with complete integration")
    
    def on_stop(self):
        """應用程式停止時調用"""
        logger.info("MMEX Kivy App Final stopped")

if __name__ == "__main__":
    app = MMEXKivyAppFinal()
    app.run()