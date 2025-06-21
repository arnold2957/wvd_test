import tkinter as tk
from tkinter import messagebox, ttk
import threading
import os
import sys
import shutil
import tempfile
import zipfile
import json
import requests
import subprocess
import time
import platform

# 当前版本号
__version__ = "1.1.2"
OWNER = "arnold2957"
REPO = "wvd"

class AutoUpdater:
    def __init__(self):
        self.latest_version = None
        self.download_url = None
        self.temp_dir = None
    
    def get_latest_release(self):
        """从GitHub API获取最新发布版本信息"""
        api_url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            self.latest_version = data.get('tag_name')
            self.download_url = data.get('zipball_url')
            return True
        except Exception as e:
            print(f"获取最新版本失败: {e}")
            return False
    
    def needs_update(self):
        """检查是否需要更新"""
        if not self.latest_version:
            return False
        # 简单的版本号比较（实际项目中可能需要更复杂的比较逻辑）
        return self.latest_version != __version__
    
    def download_release(self):
        """下载最新发布版本"""
        if not self.download_url:
            return False
        
        try:
            # 创建临时目录
            self.temp_dir = tempfile.mkdtemp(prefix=f"{self.repo}_update_")
            zip_path = os.path.join(self.temp_dir, "update.zip")
            
            # 下载zip文件
            response = requests.get(self.download_url, stream=True)
            response.raise_for_status()
            
            # 获取文件总大小（用于进度显示）
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # 计算下载进度百分比
                        progress = int((downloaded / total_size) * 100) if total_size > 0 else 0
                        yield progress
            
            # 解压zip文件
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            
            # 找到解压后的目录（GitHub生成的zip包含一个顶级目录）
            extracted_dir = None
            for entry in os.listdir(self.temp_dir):
                if entry != "update.zip":
                    extracted_dir = os.path.join(self.temp_dir, entry)
                    break
            
            if extracted_dir:
                self.update_dir = extracted_dir
                return True
            return False
        except Exception as e:
            print(f"下载失败: {e}")
            return False
    
    def prepare_restart(self):
        """准备重启脚本"""
        # 获取当前脚本路径
        script_path = os.path.abspath(sys.argv[0])
        script_dir = os.path.dirname(script_path)
        
        # 创建更新脚本
        if platform.system() == "Windows":
            return self._create_windows_restart_script(script_dir)
        else:
            return self._create_unix_restart_script(script_dir)
    
    def _create_windows_restart_script(self, target_dir):
        """创建Windows重启脚本"""
        try:
            bat_path = os.path.join(self.temp_dir, "update_script.bat")
            with open(bat_path, 'w') as f:
                f.write(f"""
@echo off
echo 正在更新程序...
timeout /t 2 /nobreak >nul

echo 复制新文件...
xcopy /Y /E "{self.update_dir}\\*" "{target_dir}"

echo 清理临时文件...
rmdir /s /q "{self.temp_dir}"

echo 启动新版本...
start "" "{sys.executable}" "{os.path.join(target_dir, os.path.basename(sys.argv[0]))}"

echo 删除更新脚本...
del /f /q "%~f0"
exit
                """)
            return bat_path
        except Exception as e:
            print(f"创建Windows脚本失败: {e}")
            return None
    
    def _create_unix_restart_script(self, target_dir):
        """创建Unix/Linux/macOS重启脚本"""
        try:
            sh_path = os.path.join(self.temp_dir, "update_script.sh")
            with open(sh_path, 'w') as f:
                f.write(f"""#!/bin/bash
echo "正在更新程序..."
sleep 2

echo "复制新文件..."
cp -Rf "{self.update_dir}"/* "{target_dir}/"

echo "清理临时文件..."
rm -rf "{self.temp_dir}"

echo "启动新版本..."
"{sys.executable}" "{os.path.join(target_dir, os.path.basename(sys.argv[0]))}" &

echo "删除更新脚本..."
rm -f "$0"
exit
                """)
            # 设置执行权限
            os.chmod(sh_path, 0o755)
            return sh_path
        except Exception as e:
            print(f"创建Unix脚本失败: {e}")
            return None


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("自动更新演示程序")
        self.geometry("600x400")
        self.resizable(True, True)
        
        # 设置应用图标
        try:
            self.iconbitmap(default="app_icon.ico")
        except:
            pass
        
        # 创建UI
        self.create_widgets()
        
        # 初始化更新器
        self.updater = AutoUpdater()
        
        # 启动后台检查更新
        self.after(1000, self.check_for_updates)
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(
            main_frame, 
            text="自动更新演示程序", 
            font=("Arial", 24, "bold"),
            foreground="#2c3e50"
        )
        title_label.pack(pady=10)
        
        # 版本信息
        version_frame = ttk.Frame(main_frame)
        version_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(version_frame, text="当前版本:", font=("Arial", 12)).pack(side=tk.LEFT)
        self.current_version_label = ttk.Label(
            version_frame, 
            text=__version__, 
            font=("Arial", 12, "bold"),
            foreground="#3498db"
        )
        self.current_version_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(version_frame, text="最新版本:", font=("Arial", 12)).pack(side=tk.LEFT, padx=(20, 0))
        self.latest_version_label = ttk.Label(
            version_frame, 
            text="检查中...", 
            font=("Arial", 12, "bold")
        )
        self.latest_version_label.pack(side=tk.LEFT, padx=5)
        
        # 更新按钮
        self.update_button = ttk.Button(
            main_frame,
            text="检查更新",
            command=self.check_for_updates,
            state=tk.DISABLED
        )
        self.update_button.pack(pady=10)
        
        # 进度条
        self.progress_frame = ttk.LabelFrame(main_frame, text="更新进度", padding=10)
        self.progress_frame.pack(fill=tk.X, pady=20)
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, 
            orient=tk.HORIZONTAL, 
            mode='determinate',
            length=500
        )
        self.progress_bar.pack(fill=tk.X)
        
        self.status_label = ttk.Label(
            self.progress_frame,
            text="就绪",
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, pady=(5, 0))
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="更新日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(
            log_frame, 
            height=8,
            state=tk.DISABLED,
            wrap=tk.WORD,
            bg="#f8f9fa",
            padx=10,
            pady=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
    
    def log_message(self, message):
        """向日志区域添加消息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)  # 滚动到底部
        self.log_text.config(state=tk.DISABLED)
    
    def check_for_updates(self):
        """检查更新（在后台线程中执行）"""
        self.update_button.config(state=tk.DISABLED)
        self.log_message("正在检查更新...")
        threading.Thread(target=self._check_updates_thread, daemon=True).start()
    
    def _check_updates_thread(self):
        """后台线程：检查更新"""
        try:
            # 获取最新版本信息
            success = self.updater.get_latest_release()
            
            # 更新UI
            self.after(0, lambda: self._update_ui_after_check(success))
        except Exception as e:
            self.after(0, lambda: self.log_message(f"检查更新时出错: {str(e)}"))
            self.after(0, lambda: self.update_button.config(state=tk.NORMAL))
    
    def _update_ui_after_check(self, success):
        """检查更新后更新UI"""
        if success:
            self.latest_version_label.config(text=self.updater.latest_version)
            
            if self.updater.needs_update():
                self.log_message(f"发现新版本 {self.updater.latest_version}，当前版本 {__version__}")
                self.update_button.config(
                    text="立即更新",
                    command=self.confirm_update,
                    state=tk.NORMAL
                )
            else:
                self.log_message("已是最新版本")
                self.update_button.config(
                    text="重新检查",
                    command=self.check_for_updates,
                    state=tk.NORMAL
                )
        else:
            self.log_message("无法获取更新信息")
            self.latest_version_label.config(text="获取失败")
            self.update_button.config(
                text="重试",
                command=self.check_for_updates,
                state=tk.NORMAL
            )
    
    def confirm_update(self):
        """确认更新弹窗"""
        if messagebox.askyesno(
            "确认更新",
            f"发现新版本 {self.updater.latest_version}，是否立即更新？\n\n"
            "更新完成后程序将自动重启。"
        ):
            self.start_update()
    
    def start_update(self):
        """开始更新过程"""
        self.update_button.config(state=tk.DISABLED)
        self.log_message("开始下载更新...")
        threading.Thread(target=self._update_thread, daemon=True).start()
    
    def _update_thread(self):
        """后台线程：执行更新"""
        try:
            # 下载更新
            download_gen = self.updater.download_release()
            
            # 更新进度条
            for progress in download_gen:
                self.after(0, lambda p=progress: self.progress_bar.config(value=p))
                self.after(0, lambda p=progress: self.status_label.config(text=f"下载中... {p}%"))
            
            self.after(0, lambda: self.log_message("下载完成，准备安装更新..."))
            
            # 准备重启脚本
            script_path = self.updater.prepare_restart()
            if not script_path:
                self.after(0, lambda: self.log_message("创建更新脚本失败"))
                self.after(0, lambda: self.update_button.config(state=tk.NORMAL))
                return
            
            self.after(0, lambda: self.log_message("更新准备就绪，即将重启..."))
            self.after(0, lambda: self.status_label.config(text="准备重启..."))
            
            # 等待UI更新
            time.sleep(1)
            
            # 执行更新脚本
            if platform.system() == "Windows":
                subprocess.Popen(['cmd', '/c', script_path], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(['sh', script_path])
            
            # 退出当前程序
            self.after(0, self.destroy)
        except Exception as e:
            self.after(0, lambda: self.log_message(f"更新失败: {str(e)}"))
            self.after(0, lambda: self.update_button.config(state=tk.NORMAL))


if __name__ == "__main__":
    app = Application()
    app.mainloop()