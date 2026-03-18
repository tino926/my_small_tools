#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MMEX Reader 重構 - 預定 Commit 時間表腳本
支援方法三：從備份檔還原並提交，實現同一檔案內修改分多次commit

使用說明：
1. 在專案根目錄執行此腳本：C:\z_btsync\btSyncAndroid\curr_proj_p\my_small_tools
2. 腳本會計算所有 commit 的時間表，每天晚上 7 點後進行 1-2 個 commits
3. 支援兩種模式：
   - 檔案模式：直接提交指定檔案
   - 內容覆蓋模式：從source_file讀取內容覆蓋target_file後提交
4. 添加安全機制：測試模式標記，防止開發過程中誤commit
5. 完成後，請切換到主分支並合併此分支：
   - git checkout main
   - git merge refactor-ui-components
   - git push origin main
   - git branch -d refactor-ui-components (可選，刪除重構分支)
"""
import datetime
import os
import time
import random
import subprocess
import sys
import shutil

import sys

# 強制使用 UTF-8 輸出
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def get_current_time():
    """獲取當前時間"""
    return datetime.datetime.now()

def get_next_evening_7pm(target_date=None):
    """獲取下一個晚上 7 點的時間"""
    if target_date is None:
        target_date = datetime.date.today()
    
    next_7pm = datetime.datetime.combine(target_date, datetime.time(19, 0, 0))
    
    # 如果當前時間已經超過今天晚上 7 點，則返回明天晚上 7 點
    if get_current_time() > next_7pm:
        next_7pm = next_7pm + datetime.timedelta(days=1)
    
    return next_7pm

def get_commited_messages():
    """獲取已經 commit 的提交訊息列表"""
    try:
        # 獲取當前分支的 commit 歷史 (檢查範圍擴大到 100 以免漏掉)
        result = subprocess.run(['git', 'log', '--pretty=format:%s', '-n', '100'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            committed_messages = set()
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line:
                    committed_messages.add(line)
            return committed_messages
        else:
            return set()
    except Exception:
        return set()

def execute_git_command(command):
    """執行 git 命令"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"錯誤: {result.stderr}")
            return False
        print(result.stdout)
        return True
    except Exception as e:
        print(f"執行命令時發生錯誤: {e}")
        return False

def apply_file_content(target_file, source_file):
    """將source_file的內容覆蓋到target_file"""
    try:
        if not os.path.exists(source_file):
            print(f"錯誤：源檔案 {source_file} 不存在")
            return False
        
        # 確保目標檔案的目錄存在
        target_dir = os.path.dirname(target_file)
        if target_dir and not os.path.exists(target_dir):
            os.makedirs(target_dir)
        
        # 複製檔案內容
        shutil.copy2(source_file, target_file)
        print(f"已將 {source_file} 的內容覆蓋到 {target_file}")
        return True
    except Exception as e:
        print(f"覆蓋檔案內容時發生錯誤: {e}")
        return False

def is_test_mode():
    """檢查是否為測試模式"""
    # 檢查是否存在測試模式標記檔案
    test_marker_file = ".commit_scheduler_test_mode"
    return os.path.exists(test_marker_file)

def main():
    print("=" * 60)
    print("MMEX Reader 重構 - 進階 Commit 時間表腳本")
    print("支援同一檔案內修改分多次commit")
    print("Ctrl+C 退出程序")
    
    # 檢查測試模式
    if is_test_mode():
        print("⚠️  警告：目前為測試模式，不會執行實際的git操作")
        print("   如需執行實際commit，請刪除 .commit_scheduler_test_mode 檔案")
    else:
        print("✅ 生產模式：將執行實際的git操作")
    
    print("=" * 60)
    
    # 要 commit 的檔案列表（每個commit只包含一個檔案）
    commits_to_do = [
        # Scheduler 自我更新
        {
            "files": ["z_local_cmd/commit_scheduler.py"],
            "msg": "Feat(scheduler): Enhance to support file deletion\n\n- Add logic to handle 'delete_files' key in commit tasks\n- Add cleanup task for obsolete temp_versions files"
        },
        # Database工具更新
        {
            "files": ["mmex_reader/db_queries.py"],
            "msg": "Refactor(db): Add transaction query functions for MMEXReader\n\n- Add get_transactions_by_date_range and count_transactions_by_date_range\n- Support specialized queries for reader module"
        },
        # Reader模組重構（逐個檔案提交）
        {
            "target_file": "mmex_reader/mmex_reader.py",
            "source_file": "mmex_reader/temp_versions/mmex_reader_step1.py",
            "msg": "Refactor(reader): Step 1 - Migrate Transaction Queries\n\n- Replace inline transaction query and count logic with imports from db_queries.py\n- Reduce size of mmex_reader.py and centralize database access"
        },
        # Reader模組重構 - Step 2
        {
            "files": ["mmex_reader/reader_config.py"],
            "msg": "Refactor(reader): Extract MMEXReaderConfig to new module\n\n- Move MMEXReaderConfig class to its own file\n- Centralize reader configuration logic"
        },
        {
            "target_file": "mmex_reader/mmex_reader.py",
            "source_file": "mmex_reader/temp_versions/mmex_reader_step2.py",
            "msg": "Refactor(reader): Step 2 - Migrate Config to import\n\n- Replace inline MMEXReaderConfig with import from reader_config.py"
        },
        # 清理過時的暫存檔案
        {
            "delete_files": [
                "mmex_reader/temp_versions/ui_components_step1.py",
                "mmex_reader/temp_versions/ui_components_step2.py",
                "mmex_reader/temp_versions/ui_components_step3.py",
                "mmex_reader/temp_versions/db_utils_step1.py",
                "mmex_reader/temp_versions/db_utils_step2.py",
                "mmex_reader/temp_versions/db_utils_step3.py"
            ],
            "msg": "Refactor(cleanup): Remove obsolete temp_versions files\n\n- Delete temporary files from ui_components and db_utils refactoring\n- Keep project directory clean"
        },
        # Reader模組重構 - Step 3
        {
            "files": ["mmex_reader/reader_main.py"],
            "msg": "Refactor(reader): Extract MMEXReader class to new module\n\n- Move MMEXReader class to its own file\n- Centralize reader main logic"
        },
        {
            "target_file": "mmex_reader/mmex_reader.py",
            "source_file": "mmex_reader/temp_versions/mmex_reader_step3.py",
            "msg": "Refactor(reader): Step 3 - Finalize mmex_reader as entry point\n\n- Replace main class with imports from new modules"
        },
        # ConfigManager 重構 - Step 1
        {
            "files": ["mmex_reader/config_model.py"],
            "msg": "Refactor(config): Step 1 - Extract AppConfig model\n\n- Move AppConfig dataclass to its own module"
        },
        {
            "target_file": "mmex_reader/config_manager.py",
            "source_file": "mmex_reader/temp_versions/config_manager_step1.py",
            "msg": "Refactor(config): Step 1 - Import AppConfig from model\n\n- Update config_manager.py to use the new model module"
        },
        # ConfigManager 重構 - Step 2
        {
            "files": ["mmex_reader/config_ui.py"],
            "msg": "Refactor(config): Step 2 - Extract SettingsPopup UI\n\n- Move Kivy-based UI components to its own module"
        },
        {
            "target_file": "mmex_reader/config_manager.py",
            "source_file": "mmex_reader/temp_versions/config_manager_step2.py",
            "msg": "Refactor(config): Step 2 - Import UI from config_ui\n\n- Update config_manager.py to use the new UI module"
        },
        # ConfigManager 重構 - Step 3
        {
            "files": ["mmex_reader/config_logic.py"],
            "msg": "Refactor(config): Step 3 - Extract ConfigManager logic\n\n- Move core management logic to its own module"
        },
        {
            "target_file": "mmex_reader/config_manager.py",
            "source_file": "mmex_reader/temp_versions/config_manager_step3.py",
            "msg": "Refactor(config): Step 3 - Finalize config_manager as interface\n\n- Update config_manager.py to be a clean entry point"
        },
        # 清理 ConfigManager 暫存檔案
        {
            "delete_files": [
                "mmex_reader/temp_versions/config_manager_step1.py",
                "mmex_reader/temp_versions/config_manager_step2.py",
                "mmex_reader/temp_versions/config_manager_step3.py"
            ],
            "msg": "Refactor(cleanup): Remove ConfigManager temp files\n\n- Delete intermediate refactoring files"
        }
    ]
    
    # 獲取已經 commit 的提交訊息
    already_committed = get_commited_messages()
    print(f"已檢測到 {len(already_committed)} 個已 commit 的提交")
    
    # 過濾出還未 commit 的提交
    remaining_commits = []
    for commit_info in commits_to_do:
        # 只比對第一行（Subject），因為 git log --pretty=format:%s 只會返回第一行
        subject = commit_info['msg'].split('\n')[0].strip()
        if subject not in already_committed:
            remaining_commits.append(commit_info)
    
    print(f"剩餘 {len(remaining_commits)} 個提交需要執行")
    
    if len(remaining_commits) == 0:
        print("所有提交都已完成！程序結束。")
        return
    
    # 計算 commit 時間表
    print("\n計算 commit 時間表...")
    commit_schedule = []
    
    # 從今天或明天晚上 7 點開始
    current_target_date = datetime.date.today()
    current_time = get_current_time()
    
    # 如果當前時間已經超過今天晚上 7 點，則從明天開始
    if current_time.time() >= datetime.time(19, 0, 0):
        current_target_date = current_target_date + datetime.timedelta(days=1)
    
    commit_index = 0
    daily_commit_count = 0
    
    while commit_index < len(remaining_commits):
        # 獲取當晚 7 點的時間
        evening_7pm = get_next_evening_7pm(current_target_date)
        
        # 計算從現在到晚上 7 點的秒數
        current_time = get_current_time()
        seconds_to_7pm = int((evening_7pm - current_time).total_seconds())
        
        # 如果已經超過當晚 7 點，則跳到第二天
        if seconds_to_7pm <= 0:
            current_target_date = current_target_date + datetime.timedelta(days=1)
            evening_7pm = get_next_evening_7pm(current_target_date)
            seconds_to_7pm = int((evening_7pm - get_current_time()).total_seconds())
            daily_commit_count = 0  # 新的一天，重置計數
        
        # 每天最多2個commits
        if daily_commit_count >= 2:
            current_target_date = current_target_date + datetime.timedelta(days=1)
            daily_commit_count = 0
            continue
        
        # 隨機選擇 commit 時間
        if daily_commit_count == 0:
            # 第一個 commit：晚上 7 點後的 n 到 n+1200 秒之間（20分鐘內）
            commit_delay = random.randint(seconds_to_7pm, seconds_to_7pm + 1200)
        else:
            # 第二個 commit：第一個 commit 後的 600 到 1800 秒內（10-30分鐘）
            last_commit_time = commit_schedule[-1]["time"]
            additional_delay = random.randint(600, 1800)
            commit_delay = (last_commit_time - current_time).total_seconds() + additional_delay
        
        commit_time = current_time + datetime.timedelta(seconds=commit_delay)
        
        if commit_index < len(remaining_commits):
            commit_schedule.append({
                "time": commit_time,
                "commit_info": remaining_commits[commit_index],
                "index": commit_index + 1
            })
            commit_index += 1
            daily_commit_count += 1
    
    # 顯示時間表
    print("\n預定的 commit 時間表:")
    for commit in commit_schedule:
        if "delete_files" in commit["commit_info"]:
            files_str = ", ".join(commit['commit_info']['delete_files'])
        elif "target_file" in commit["commit_info"]:
            files_str = f"{commit['commit_info']['target_file']} (from {commit['commit_info']['source_file']})"
        else:
            files_str = ", ".join(commit['commit_info']['files'])
        print(f"  {commit['index']:2d}. {commit['time'].strftime('%Y-%m-%d %H:%M:%S')} - {commit['commit_info']['msg']}")
        print(f"      檔案: {files_str}")
    
    print(f"\n總共 {len(commit_schedule)} 個 commits 已預定")
    
    # 如果是測試模式，顯示提示並退出
    if is_test_mode():
        print("\n⚠️  測試模式：不會執行實際的git操作")
        print("   時間表已生成，如需執行實際commit，請刪除 .commit_scheduler_test_mode 檔案後重新運行")
        return
    
    # 執行 commit 時間表
    try:
        for commit in commit_schedule:
            current_time = get_current_time()
            wait_time = (commit['time'] - current_time).total_seconds()
            
            if wait_time > 0:
                print(f"\n等待到 {commit['time'].strftime('%Y-%m-%d %H:%M:%S')}...")
                # 顯示倒數計時
                # 檢測是否為互動式終端機
                is_tty = sys.stdout.isatty()
                last_print_time = 0
                
                while wait_time > 0:
                    hours, remainder = divmod(int(wait_time), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    # 判斷是否為 "Tee-Object" 環境（不是TTY，但又不是單純的檔案重定向）
                    # 為了滿足用戶需求：即使在 tee 環境下也要強制每秒輸出 \r
                    # 注意：這在某些 log 檢視器中可能會顯示大量重複行，但在 PowerShell 終端配合 Tee-Object 可能可以達到效果
                    
                    print(f"\r  倒數 {hours:02d}:{minutes:02d}:{seconds:02d}", end='', flush=True)
                    time.sleep(min(1, wait_time))
                    
                    wait_time = (commit['time'] - get_current_time()).total_seconds()
                
                print()  # 換行
            
            print(f"\n[{get_current_time().strftime('%Y-%m-%d %H:%M:%S')}] 執行第 {commit['index']} 個 commit: {commit['commit_info']['msg']}")
            
            # 處理刪除檔案模式
            if "delete_files" in commit["commit_info"]:
                for file_path in commit['commit_info']['delete_files']:
                    if not os.path.exists(file_path):
                        print(f"警告：要刪除的檔案 {file_path} 不存在，跳過")
                        continue
                    
                    # 嘗試 git rm
                    rm_cmd = f"git rm {file_path}"
                    print(f"執行: {rm_cmd}")
                    if not execute_git_command(rm_cmd):
                        # 如果 git rm 失敗，可能是未追蹤的檔案，直接從硬碟刪除
                        print(f"git rm 失敗，嘗試直接刪除未追蹤檔案: {file_path}")
                        try:
                            if os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                            else:
                                os.remove(file_path)
                            print(f"已成功從硬碟刪除: {file_path}")
                        except Exception as e:
                            print(f"刪除檔案時發生錯誤: {e}")

            # 處理內容覆蓋模式
            elif "target_file" in commit["commit_info"]:
                target_file = commit["commit_info"]["target_file"]
                source_file = commit["commit_info"]["source_file"]
                
                if not apply_file_content(target_file, source_file):
                    print(f"跳過第 {commit['index']} 個 commit：檔案覆蓋失敗")
                    continue
                
                # 添加覆蓋後的檔案到 staging area
                add_cmd = f"git add {target_file}"
                print(f"執行: {add_cmd}")
                if not execute_git_command(add_cmd):
                    print("git add 失敗，嘗試強制添加 (git add -f)...")
                    if not execute_git_command(f"git add -f {target_file}"):
                        print("git add -f 也失敗，跳過此檔案")
                        continue
            
            # 處理傳統檔案模式
            elif "files" in commit["commit_info"]:
                # 添加檔案到 staging area
                for file_path in commit['commit_info']['files']:
                    add_cmd = f"git add {file_path}"
                    print(f"執行: {add_cmd}")
                    if not execute_git_command(add_cmd):
                        print(f"git add {file_path} 失敗，嘗試強制添加 (git add -f)...")
                        if not execute_git_command(f"git add -f {file_path}"):
                            print(f"git add -f {file_path} 也失敗，跳過此檔案")
                            continue
            
            # 檢查是否有內容可以 commit
            status_result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
            if not status_result.stdout.strip():
                print("提示：沒有偵測到已暫存的更改，跳過此 commit")
                continue
            
            # 執行 git commit
            commit_cmd = f'git commit -m "{commit["commit_info"]["msg"]}"'
            print(f"執行: {commit_cmd}")
            if not execute_git_command(commit_cmd):
                print("git commit 失敗")
                continue
            
            # 執行 git push
            push_cmd = "git push"
            print(f"執行: {push_cmd}")
            if not execute_git_command(push_cmd):
                print("git push 失敗")
            
            print(f"完成第 {commit['index']} / {len(commit_schedule)} 個 commit")
    
    except KeyboardInterrupt:
        print("\n\n程序被用戶中斷")
        completed = sum(1 for c in commit_schedule if c['time'] < get_current_time())
        print(f"已完成 {completed}/{len(commit_schedule)} 個 commits")
        sys.exit(0)
    
    print(f"\n所有 {len(commit_schedule)} 個 commits 都已完成！")

if __name__ == "__main__":
    main()
