import os
import sys
import json
import hashlib
import threading
import tkinter as tk
from tkinter import messagebox
from urllib.request import urlopen, Request
from urllib.error import URLError

class AutoUpdater:
    def __init__(self, parent, github_user, github_repo, current_version):
        """
        自动更新管理器
        
        :param parent: 父窗口(Tk 或 Toplevel)
        :param github_user: GitHub 用户名
        :param github_repo: GitHub 仓库名
        :param current_version: 当前版本号
        """
        self.parent = parent
        self.github_user = github_user
        self.github_repo = github_repo
        self.current_version = current_version
        self.update_url = f"https://{github_user}.github.io/{github_repo}/release.json"
        print(self.update_url)
        
        self.showing_msg_window = False

        # 启动后台检查
        self.check_after_id = self.parent.after(1000, self.check_for_update)

    def check_for_update(self):
        """在后台线程中检查更新"""
        threading.Thread(target=self._fetch_update_data, daemon=True).start()
        
       
        self.check_after_id = self.parent.after(1000, self.check_for_update)

    def _fetch_update_data(self):
        """获取更新信息"""
        try:
            req = Request(self.update_url, headers={'Cache-Control': 'no-cache'})
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
            # 比较版本
            if self._is_newer_version(data['version']):
                if not self.showing_msg_window:
                    self.showing_msg_window = True
                    self.parent.after(0, self._show_update_prompt, data)

                
        except URLError as e:
            print(f"更新检查失败: {e}")
        except Exception as e:
            print(f"错误: {e}")

    def _is_newer_version(self, new_version):
        print(new_version,self.current_version)
        return new_version > self.current_version

    def _show_update_prompt(self, update_data):
        """显示更新提示对话框"""
        msg = f"发现新版本 {update_data['version']} (当前版本 {self.current_version})\n是否立即更新?"
        if messagebox.askyesno("发现更新", msg):
            threading.Thread(target=self._download_and_apply_update, 
                            args=(update_data,), daemon=True).start()
            self.showing_msg_window = False
        else:
            self.showing_msg_window = False

    def _download_and_apply_update(self, update_data):
        """下载并应用更新"""
        try:
            # 创建临时目录
            temp_dir = "__update_temp__"
            os.makedirs(temp_dir, exist_ok=True)
            
            # 下载新版本
            download_url = update_data['download_url']
            file_name = os.path.basename(download_url)
            temp_path = os.path.join(temp_dir, file_name)
            
            with urlopen(download_url) as response, open(temp_path, 'wb') as out_file:
                out_file.write(response.read())
            
            # 验证MD5
            if self._verify_md5(temp_path, update_data['md5']):
                # 生成重启脚本
                self._create_restart_script(temp_path)
                
                # 退出当前应用
                self.parent.after(0, self._restart_application)
            else:
                messagebox.showerror("更新失败", "文件校验失败，请手动更新")
                
        except Exception as e:
            messagebox.showerror("更新错误", f"更新失败: {str(e)}")

    def _verify_md5(self, file_path, expected_md5):
        """验证文件MD5哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest() == expected_md5

    def _create_restart_script(self, update_file):
        """创建重启脚本(跨平台)"""
        if sys.platform == "win32":
            script = f"""@echo off
timeout /t 1 /nobreak >nul
move /Y "{update_file}" "{os.path.basename(update_file)}"
start "" "{os.path.basename(update_file)}"
rmdir /S /Q "__update_temp__"
del "%~f0"
"""
            with open("_update_restart.bat", "w") as f:
                f.write(script)
                
        else:  # Linux/macOS
            script = f"""#!/bin/bash
sleep 1
mv -f "{update_file}" "{os.path.basename(update_file)}"
chmod +x "{os.path.basename(update_file)}"
rm -rf "__update_temp__"
nohup ./{os.path.basename(update_file)} >/dev/null 2>&1 &
rm -- "$0"
"""
            with open("_update_restart.sh", "w") as f:
                f.write(script)
            os.chmod("_update_restart.sh", 0o755)

    def _restart_application(self):
        """重启应用程序"""
        if sys.platform == "win32":
            os.startfile("_update_restart.bat")
        else:
            os.system("nohup ./_update_restart.sh &")
        
        # 关闭当前应用
        self.parent.destroy()