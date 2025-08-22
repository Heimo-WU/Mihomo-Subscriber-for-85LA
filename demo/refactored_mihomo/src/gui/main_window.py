# refactored_mihomo/src/gui/main_window.py
import os
import threading
import webbrowser
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

from src.core.network import MihomoNetwork
from src.core.file_manager import MihomoFileManager
from src.utils.logger import MihomoLogger
from src.utils.constants import SAVE_DIR, BASE_URL, TIMEOUT, RETRY
from src.gui.tabs import create_main_tab, create_files_tab, create_about_tab
from src.gui.ui_utils import copy_to_clipboard, on_title_click, shake_window, rainbow_title_effect


class MihomoSubscriptionGUI:
    """
    一个用于自动查找和下载 Mihomo 订阅的 GUI 应用程序。
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Mihomo Subscriber")
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 设置窗口尺寸
        window_width = 750
        window_height = 650
        
        # 计算居中位置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # 设置窗口位置和大小，实现居中显示
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.configure(bg='#f0f0f0')
        self.root.overrideredirect(True)  # 删除系统标题栏

        self.BASE_URL = BASE_URL
        self.TIMEOUT = TIMEOUT
        self.RETRY_COUNT = RETRY
        self.DEFAULT_SAVE_DIR = SAVE_DIR
        os.makedirs(self.DEFAULT_SAVE_DIR, exist_ok=True)
        self.logger = MihomoLogger(self.DEFAULT_SAVE_DIR)
        self.network = MihomoNetwork(
            BASE_URL, TIMEOUT, RETRY,
            self.logger, lambda: self.is_running
        )
        self.file_manager = MihomoFileManager(self.DEFAULT_SAVE_DIR, self.logger)
        self.create_widgets()
        self.is_running = False
        self.search_thread = None

        # 绑定窗口拖动事件
        self.title_frame.bind("<ButtonPress-1>", self.start_move)
        self.title_frame.bind("<ButtonRelease-1>", self.stop_move)
        self.title_frame.bind("<B1-Motion>", self.do_move)

        # 拖动窗口的辅助变量
        self.x = None
        self.y = None

        # 彩蛋功能 - 连击计数器和定时器
        self.easter_egg_clicks = 0
        self.easter_egg_timer = None

    def start_move(self, event):
        """记录鼠标按下时的位置，用于窗口拖动。"""
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        """重置鼠标位置，结束窗口拖动。"""
        self.x = None
        self.y = None

    def do_move(self, event):
        """计算并移动窗口到新位置。"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    # ========== UI 创建（统一缩小字体/间距） ==========
    def create_widgets(self):
        """创建并布局所有GUI组件。"""
        # 自定义标题栏
        self.title_frame = tk.Frame(self.root, bg='#2c3e50', height=40)
        self.title_frame.pack(fill='x')
        self.title_frame.pack_propagate(False)
        tk.Label(self.title_frame, text="🚀 Mihomo Subscriber",
                 font=('微软雅黑', 12, 'bold'),
                 bg='#2c3e50', fg='white').pack(side='left', padx=10, expand=True, anchor='w')

        # 添加关闭按钮
        tk.Button(self.title_frame, text="✖", command=self.root.destroy,
                  font=('微软雅黑', 10, 'bold'),
                  bg='#2c3e50', fg='white',
                  bd=0, relief='flat', activebackground='#e74c3c').pack(side='right')

        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=8, pady=8)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)

        self.main_tab = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(self.main_tab, text="主要功能")
        self.files_tab = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(self.files_tab, text="文件管理")
        self.about_tab = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(self.about_tab, text="关于")

        create_main_tab(self)
        create_files_tab(self)
        create_about_tab(self)

    def populate_date_options(self):
        """填充日期选择下拉列表，显示最近8天的日期。"""
        today = datetime.now()
        options = []
        for i in range(8):
            date = today - timedelta(days=i)
            desc = "今天" if i == 0 else f"{i}天前"
            options.append(f"{desc} ({date.strftime('%Y年%m月%d日')})")
        self.date_combo['values'] = options
        self.date_combo.current(0)

    def browse_path(self):
        """打开文件夹对话框，让用户选择保存路径。"""
        folder = filedialog.askdirectory(initialdir=self.save_path_var.get(),
                                         title="选择保存文件夹")
        if folder:
            self.save_path_var.set(folder)
            self.files_path_label.config(text=folder)

    def get_target_date(self):
        """根据用户选择的下拉列表项，返回对应的日期对象。"""
        selection = self.date_combo.current()
        return datetime.now() - timedelta(days=selection)

    def log_message(self, message, level='INFO'):
        """在GUI日志框中显示带时间戳和级别的日志消息。"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {level}: {message}\n"
        self.root.after(0, lambda: self.update_log_display(formatted_msg))
        self.logger.log(message, level)

    def update_log_display(self, msg):
        """将日志消息添加到日志文本框并滚动到底部。"""
        self.log_text.insert(tk.END, msg)
        self.log_text.see(tk.END)

    def clear_log(self):
        """清除日志文本框和结果列表的内容。"""
        self.log_text.delete(1.0, tk.END)
        self.result_tree.delete(*self.result_tree.get_children())

    def start_search(self):
        """启动搜索线程，更新UI状态。"""
        if self.is_running:
            return
        self.is_running = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.progress.start()
        self.result_tree.delete(*self.result_tree.get_children())
        target_date = self.get_target_date()
        self.search_thread = threading.Thread(target=self.search_worker, args=(target_date,), daemon=True)
        self.search_thread.start()

    def stop_search(self):
        """停止搜索任务，更新UI状态。"""
        self.is_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.progress.stop()
        self.log_message("用户停止了搜索", "WARN")

    def search_worker(self, target_date):
        """
        搜索任务的核心逻辑。
        1. 查找文章 -> 2. 提取链接 -> 3. 验证链接 -> 4. 保存有效链接。
        """
        try:
            self.log_message(f"开始查找 {target_date.strftime('%Y年%m月%d日')} 的 Mihomo 订阅...")
            
            # 回溯查找，直到找到有效的文章或达到限制
            for i in range(8):
                if not self.is_running:
                    return
                current_target_date = datetime.now() - timedelta(days=i)
                self.log_message(f"尝试查找 {current_target_date.strftime('%Y年%m月%d日')} 的文章...")
                post_url = self.network.find_post_by_date(current_target_date)
                
                if not post_url:
                    self.log_message(f"未找到 {current_target_date.strftime('%Y年%m月%d日')} 的文章，继续回溯...", "WARN")
                    continue
                
                self.log_message(f"找到文章: {post_url}")
                mihomo_urls = self.network.extract_mihomo_urls(post_url)
                
                if not mihomo_urls:
                    self.log_message("未找到 Mihomo 订阅链接，继续回溯...", "WARN")
                    continue
                
                self.log_message(f"找到 {len(mihomo_urls)} 个 Mihomo 链接")
                valid_urls = []
                for idx, url in enumerate(mihomo_urls):
                    if not self.is_running:
                        return
                    self.log_message(f"验证链接 {idx+1}/{len(mihomo_urls)}: {url[:50]}...")
                    if self.network.validate_yaml_url(url):
                        valid_urls.append(url)
                        self.root.after(0, lambda u=url, i=idx: self.add_result_item(f"Mihomo {i+1}", "✅ 有效", u))
                    else:
                        self.root.after(0, lambda u=url, i=idx: self.add_result_item(f"Mihomo {i+1}", "❌ 无效", u))
                
                if valid_urls:
                    self.file_manager.save_subscription_url(valid_urls[0])
                    self.log_message(f"Mihomo 订阅更新完成！", "SUCCESS")
                    self.root.after(0, self.refresh_files)
                    self.root.after(0, lambda: messagebox.showinfo("成功",
                                                                  f"已更新 Mihomo 订阅！\n文件：{os.path.join(self.save_path_var.get(), '85LA.yaml')}"))
                    return # 找到并更新成功，结束循环
                else:
                    self.log_message("所有找到的链接均无效，继续回溯查找更早的文章...", "WARN")

            self.log_message("回溯查找失败，没有找到有效的 Mihomo 订阅链接。", "ERROR")
            
        except Exception as e:
            self.log_message(f"搜索过程中出错: {e}", "ERROR")
        finally:
            self.root.after(0, self.search_finished)

    def search_finished(self):
        """搜索任务结束后，重置UI状态。"""
        self.is_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.progress.stop()

    def add_result_item(self, desc, status, url):
        """向结果列表添加一个新条目。"""
        self.result_tree.insert('', 'end', text=desc, values=(status, url))

    def on_item_double_click(self, event):
        """双击结果列表项时，打开对应的URL。"""
        sel = self.result_tree.selection()
        if not sel:
            return
        url = self.result_tree.item(sel[0])['values'][1]
        if url and url.startswith('http') and messagebox.askyesno("打开链接", f"是否打开？\n\n{url}"):
            webbrowser.open(url)

    def refresh_files(self):
        """刷新文件管理标签页的文件列表。"""
        # 清空旧数据
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

        save_dir = self.save_path_var.get()
        if not os.path.exists(save_dir):
            return

        # 只匹配 85LA.yaml
        file_path = os.path.join(save_dir, "85LA.yaml")
        if not os.path.isfile(file_path):
            return

        mtime = datetime.fromtimestamp(os.path.getmtime(file_path)) \
            .strftime('%Y-%m-%d %H:%M:%S')
        filename = os.path.basename(file_path)

        self.files_tree.insert('', 'end',
                               text=filename,
                               values=(mtime,),
                               tags=(file_path,))

    def open_folder(self):
        """打开保存文件的目录。"""
        save_dir = self.save_path_var.get()
        if os.path.exists(save_dir):
            os.startfile(save_dir)
        else:
            messagebox.showerror("错误", "文件夹不存在")

    def on_file_double_click(self, event):
        """双击文件列表项时，预览文件内容。"""
        sel = self.files_tree.selection()
        if not sel:
            return
        file_path = self.files_tree.item(sel[0], 'tags')[0]
        self.show_file_content(file_path)

    def show_file_content(self, file_path):
        """在预览框中显示指定文件的内容。"""
        try:
            content = self.file_manager.read_file_content(file_path)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, content)
            self.notebook.select(self.files_tab)
        except Exception as e:
            messagebox.showerror("错误", f"无法读取文件: {e}")