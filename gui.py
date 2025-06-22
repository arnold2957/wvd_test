import tkinter as tk
from auto_updater import AutoUpdater

# 当前版本号
__version__ = "1.1.3"
OWNER = "arnold2957"
REPO = "wvd_test"

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("自动更新示例")
        self.geometry("400x300")
        
        label = tk.Label(self, text=f"当前版本: {__version__}", font=("Arial", 14))
        label.pack(pady=50)
        
        # 初始化自动更新
        AutoUpdater(self, OWNER, REPO, __version__)

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()