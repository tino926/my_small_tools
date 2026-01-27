#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MMEX Kivy App - Stage 1: Basic UI Structure

這是第一階段的版本，只包含基礎的UI結構
"""

import logging
from typing import Optional, Dict, Any
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.core.window import Window

# 基礎日誌配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MMEXKivyAppStage1(App):
    """MMEX Kivy應用程式 - 第一階段：基礎結構"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "MMEX Reader - Stage 1"
        logger.info("MMEX Kivy App Stage 1 initialized")
    
    def build(self):
        """構建基礎UI"""
        # 創建主佈局
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 添加標題
        title_label = Label(
            text="MMEX Reader - Basic Structure",
            size_hint_y=0.1,
            font_size='20sp'
        )
        main_layout.add_widget(title_label)
        
        # 添加狀態標籤
        status_label = Label(
            text="Basic UI structure loaded - Stage 1",
            size_hint_y=0.1,
            font_size='14sp'
        )
        main_layout.add_widget(status_label)
        
        logger.info("Basic UI structure built successfully")
        return main_layout
    
    def on_start(self):
        """應用程式啟動時調用"""
        logger.info("MMEX Kivy App Stage 1 started")
    
    def on_stop(self):
        """應用程式停止時調用"""
        logger.info("MMEX Kivy App Stage 1 stopped")

if __name__ == "__main__":
    app = MMEXKivyAppStage1()
    app.run()