#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MMEX Kivy App - Stage 2: Event Handling and State Management

這是第二階段的版本，添加了事件處理和狀態管理
"""

import logging
from typing import Optional, Dict, Any, List
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock

# 進階日誌配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MMEXKivyAppStage2(App):
    """MMEX Kivy應用程式 - 第二階段：事件處理和狀態管理"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "MMEX Reader - Stage 2"
        self.click_count = 0
        self.state = "idle"
        logger.info("MMEX Kivy App Stage 2 initialized with event handling")
    
    def build(self):
        """構建UI與事件處理"""
        # 創建主佈局
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 添加標題
        title_label = Label(
            text="MMEX Reader - Event Handling",
            size_hint_y=0.1,
            font_size='20sp'
        )
        main_layout.add_widget(title_label)
        
        # 添加狀態標籤
        self.status_label = Label(
            text="Ready - Click the button to test events",
            size_hint_y=0.1,
            font_size='14sp'
        )
        main_layout.add_widget(self.status_label)
        
        # 添加測試按鈕
        test_button = Button(
            text="Click Me!",
            size_hint_y=0.2,
            font_size='16sp'
        )
        test_button.bind(on_press=self.on_button_click)
        main_layout.add_widget(test_button)
        
        # 添加計數器標籤
        self.counter_label = Label(
            text="Click count: 0",
            size_hint_y=0.1,
            font_size='12sp'
        )
        main_layout.add_widget(self.counter_label)
        
        # 設置定時器更新狀態
        Clock.schedule_interval(self.update_status, 1.0)
        
        logger.info("UI with event handling built successfully")
        return main_layout
    
    def on_button_click(self, instance):
        """按鈕點擊事件處理"""
        self.click_count += 1
        self.counter_label.text = f"Click count: {self.click_count}"
        self.status_label.text = f"Button clicked! Count: {self.click_count}"
        logger.info(f"Button clicked, count: {self.click_count}")
    
    def update_status(self, dt):
        """定期更新狀態"""
        if self.click_count > 0:
            self.status_label.text = f"Active - Last click: {self.click_count}"
    
    def on_start(self):
        """應用程式啟動時調用"""
        logger.info("MMEX Kivy App Stage 2 started with event handling")
    
    def on_stop(self):
        """應用程式停止時調用"""
        logger.info("MMEX Kivy App Stage 2 stopped")

if __name__ == "__main__":
    app = MMEXKivyAppStage2()
    app.run()