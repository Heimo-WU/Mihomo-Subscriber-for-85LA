# refactored_mihomo/main.py
import tkinter as tk

from src.gui.main_window import MihomoSubscriptionGUI


def main():
    """主函数，创建并运行GUI应用程序。"""
    root = tk.Tk()
    app = MihomoSubscriptionGUI(root)
    app.refresh_files()

    def on_closing():
        """处理窗口关闭事件，确保程序正常退出。"""
        app.is_running = False
        if app.search_thread and app.search_thread.is_alive():
            # 可以在这里添加等待线程结束的逻辑，但daemon线程会自动退出
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()