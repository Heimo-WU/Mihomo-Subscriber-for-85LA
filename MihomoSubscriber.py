import re
import os
import glob
import time
import logging
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

# 配置全局保存目录和日志
SAVE_DIR = r"D:\Tool\Proxy\Yaml"
os.makedirs(SAVE_DIR, exist_ok=True)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# 基础URL和请求参数
BASE_URL = "https://www.85la.com/"
TIMEOUT = 15
RETRY = 3


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
        self.setup_logging()
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

    def setup_logging(self):
        """配置日志记录器，同时输出到文件和控制台。"""
        log_file = os.path.join(self.DEFAULT_SAVE_DIR, "mihomo_auto.log")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.FileHandler(log_file, encoding='utf-8'),
                      logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)

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

        self.create_main_tab()
        self.create_files_tab()
        self.create_about_tab()

    def create_main_tab(self):
        """创建"主要功能"标签页的组件。"""
        settings_frame = tk.LabelFrame(self.main_tab, text="⚙️ 设置",
                                       font=('微软雅黑', 9, 'bold'),
                                       bg='#f0f0f0', fg='#2c3e50')
        settings_frame.pack(fill='x', pady=(0, 8))

        # 查找日期选择
        date_frame = tk.Frame(settings_frame, bg='#f0f0f0')
        date_frame.pack(fill='x', padx=8, pady=5)
        tk.Label(date_frame, text="查找日期:", font=('微软雅黑', 8),
                 bg='#f0f0f0').pack(side='left')
        self.date_var = tk.StringVar()
        self.date_combo = ttk.Combobox(date_frame, textvariable=self.date_var,
                                       width=18, state='readonly')
        self.date_combo.pack(side='left', padx=5)
        self.populate_date_options()

        # 保存路径
        file_frame = tk.Frame(settings_frame, bg='#f0f0f0')
        file_frame.pack(fill='x', padx=8, pady=5)
        tk.Label(file_frame, text="保存路径:", font=('微软雅黑', 8),
                 bg='#f0f0f0').pack(anchor='w')
        path_frame = tk.Frame(file_frame, bg='#f0f0f0')
        path_frame.pack(fill='x')
        self.save_path_var = tk.StringVar(value=self.DEFAULT_SAVE_DIR)
        tk.Entry(path_frame, textvariable=self.save_path_var,
                 font=('微软雅黑', 8)).pack(side='left', fill='x', expand=True, padx=(0, 5))
        tk.Button(path_frame, text="浏览", command=self.browse_path,
                  font=('微软雅黑', 7), bg='#3498db', fg='white',
                  relief='flat', padx=8).pack(side='right')

        # 控制按钮
        btn_frame = tk.Frame(self.main_tab, bg='#f0f0f0')
        btn_frame.pack(fill='x', pady=(0, 8))
        self.start_btn = tk.Button(btn_frame, text="🔍 开始查找", command=self.start_search,
                                   font=('微软雅黑', 10, 'bold'),
                                   bg='#27ae60', fg='white', relief='flat',
                                   padx=20, pady=6)
        self.start_btn.pack(side='left', padx=(0, 8))
        self.stop_btn = tk.Button(btn_frame, text="⏹️ 停止任务", command=self.stop_search,
                                  font=('微软雅黑', 10, 'bold'),
                                  bg='#e74c3c', fg='white', relief='flat',
                                  padx=20, pady=6, state='disabled')
        self.stop_btn.pack(side='left', padx=(0, 8))
        tk.Button(btn_frame, text="🗑️ 清除日志", command=self.clear_log,
                  font=('微软雅黑', 8), bg='#95a5a6', fg='white',
                  relief='flat', padx=15, pady=6).pack(side='left')

        self.progress = ttk.Progressbar(self.main_tab, mode='indeterminate')
        self.progress.pack(fill='x', pady=(0, 8))

        # 结果列表
        result_frame = tk.LabelFrame(self.main_tab, text="📋 查找结果",
                                     font=('微软雅黑', 9, 'bold'),
                                     bg='#f0f0f0', fg='#2c3e50')
        result_frame.pack(fill='x', pady=(0, 8))
        self.result_tree = ttk.Treeview(result_frame, columns=('status', 'url'),
                                        show='tree headings', height=1)
        self.result_tree.heading('#0', text='描述')
        self.result_tree.heading('status', text='状态')
        self.result_tree.heading('url', text='链接')
        self.result_tree.column('#0', width=130)
        self.result_tree.column('status', width=60)
        self.result_tree.column('url', width=420)
        vsb = ttk.Scrollbar(result_frame, orient='vertical', command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=vsb.set)
        self.result_tree.pack(side='left', fill='both', expand=True, padx=(8, 0), pady=6)
        vsb.pack(side='right', fill='y', padx=(0, 8), pady=6)
        self.result_tree.bind('<Double-1>', self.on_item_double_click)

        # 日志
        log_frame = tk.LabelFrame(self.main_tab, text="📝 运行日志",
                                  font=('微软雅黑', 9, 'bold'),
                                  bg='#f0f0f0', fg='#2c3e50')
        log_frame.pack(fill='both', expand=True)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8,
                                                  font=('Consolas', 8),
                                                  bg='#2c3e50', fg='#ecf0f1')
        self.log_text.pack(fill='both', expand=True, padx=8, pady=6)

    def create_files_tab(self):
        """创建"文件管理"标签页的组件。"""
        # 顶部路径和按钮区域
        path_frame = tk.Frame(self.files_tab, bg='#f0f0f0')
        path_frame.pack(fill='x', padx=8, pady=6)
        tk.Label(path_frame, text="文件夹路径:", font=('微软雅黑', 8),
                 bg='#f0f0f0').pack(side='left')
        self.files_path_label = tk.Label(path_frame, text=self.DEFAULT_SAVE_DIR,
                                         font=('微软雅黑', 8), bg='#f0f0f0', fg='#2c3e50')
        self.files_path_label.pack(side='left', padx=5)

        btn_frame = tk.Frame(self.files_tab, bg='#f0f0f0')
        btn_frame.pack(fill='x', padx=8, pady=(0, 6))
        tk.Button(btn_frame, text="🔄 刷新文件列表", command=self.refresh_files,
                  font=('微软雅黑', 8), bg='#3498db', fg='white',
                  relief='flat', padx=15, pady=4).pack(side='left', padx=(0, 6))
        tk.Button(btn_frame, text="📁 打开文件夹", command=self.open_folder,
                  font=('微软雅黑', 8), bg='#9b59b6', fg='white',
                  relief='flat', padx=15, pady=4).pack(side='left')

        # 主内容区域 - 左右布局
        main_content_frame = tk.Frame(self.files_tab, bg='#f0f0f0')
        main_content_frame.pack(fill='both', expand=True, padx=8, pady=(0, 6))

        # 左侧：文件列表
        files_frame = tk.LabelFrame(main_content_frame, text="📄 已导出文件",
                                     font=('微软雅黑', 9, 'bold'),
                                     bg='#f0f0f0', fg='#2c3e50')
        files_frame.pack(side='left', fill='both', expand=True, padx=(0, 4))
        
        self.files_tree = ttk.Treeview(files_frame, columns=('date',),
                               show='tree headings')
        self.files_tree.heading('#0', text='文件名')
        self.files_tree.heading('date', text='修改时间')
        self.files_tree.column('#0', width=120)
        self.files_tree.column('date', width=140)
        
        files_vsb = ttk.Scrollbar(files_frame, orient='vertical', command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=files_vsb.set)
        self.files_tree.pack(side='left', fill='both', expand=True, padx=(8, 0), pady=6)
        files_vsb.pack(side='right', fill='y', padx=(0, 8), pady=6)
        self.files_tree.bind('<Double-1>', self.on_file_double_click)

        # 右侧：文件预览
        preview_frame = tk.LabelFrame(main_content_frame, text="👁️ 文件内容预览",
                                      font=('微软雅黑', 9, 'bold'),
                                      bg='#f0f0f0', fg='#2c3e50')
        preview_frame.pack(side='right', fill='both', expand=True, padx=(4, 0))
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=20,
                                                      font=('Consolas', 8),
                                                      bg='#34495e', fg='#ecf0f1')
        self.preview_text.pack(fill='both', expand=True, padx=8, pady=6)

    def create_about_tab(self):
        """创建"关于"标签页的组件和内容。"""
        # 滚动容器
        container = tk.Frame(self.about_tab, bg='#f0f0f0')
        container.pack(fill='both', expand=True)

        canvas = tk.Canvas(container, bg='#f0f0f0', highlightthickness=0)
        scroll = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
        scroll.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        canvas.configure(yscrollcommand=scroll.set)

        inner = tk.Frame(canvas, bg='#f0f0f0')
        canvas.create_window((0, 0), window=inner, anchor='n')

        # 调整画布内容宽度以匹配窗口大小
        def on_resize(e):
            canvas.itemconfig(canvas.find_all()[0], width=e.width)
        canvas.bind('<Configure>', on_resize)

        # 绑定鼠标滚轮事件
        canvas.bind_all('<MouseWheel>',
                        lambda e: canvas.yview_scroll(-1 * (e.delta // 120), 'units'))
        inner.bind('<Configure>',
                lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        inner.columnconfigure(0, weight=1)
        
        # 标题
        title_lbl = tk.Label(inner, text="🚀 Mihomo Subscriber\nVersion 1.0.0",
                             font=('微软雅黑', 16, 'bold'), bg='#2c3e50', fg='white',
                             justify='center', pady=15)
        title_lbl.grid(row=0, column=0, sticky='ew', pady=(0, 15))
        
        # 作者信息
        author_info = tk.LabelFrame(inner, text="👨‍💻 作者信息", font=('微软雅黑', 10, 'bold'),
                                     bg='#f0f0f0', fg='#2c3e50')
        author_info.grid(row=1, column=0, sticky='ew', padx=20, pady=10)
        author_info.columnconfigure(0, weight=1)

        # 作者姓名
        name_frame = tk.Frame(author_info, bg='#f0f0f0')
        name_frame.pack(fill='x', pady=3)
        tk.Label(name_frame, text="昵称:", font=('微软雅黑', 9, 'bold'),
                 bg='#f0f0f0', fg='#34495e', width=8, anchor='w').pack(side='left')
        tk.Label(name_frame, text="WÜ", font=('微软雅黑', 9),
                 bg='#f0f0f0', fg='#2c3e50').pack(side='left')

        # 邮箱
        email_frame = tk.Frame(author_info, bg='#f0f0f0')
        email_frame.pack(fill='x', pady=3)
        tk.Label(email_frame, text="邮箱:", font=('微软雅黑', 9, 'bold'),
                 bg='#f0f0f0', fg='#34495e', width=8, anchor='w').pack(side='left')
        email_label = tk.Label(email_frame, text="heimo0721@gmail.com", font=('微软雅黑', 9),
                               bg='#f0f0f0', fg='#3498db', cursor='hand2')
        email_label.pack(side='left')
        email_label.bind('<Button-1>', lambda e: self.copy_to_clipboard("heimo0721@gmail.com"))

        # GitHub
        github_frame = tk.Frame(author_info, bg='#f0f0f0')
        github_frame.pack(fill='x', pady=3)
        tk.Label(github_frame, text="GitHub:", font=('微软雅黑', 9, 'bold'),
                 bg='#f0f0f0', fg='#34495e', width=8, anchor='w').pack(side='left')
        github_label = tk.Label(github_frame, text="https://github.com/Heimo-WU", font=('微软雅黑', 9),
                                bg='#f0f0f0', fg='#3498db', cursor='hand2')
        github_label.pack(side='left')
        github_label.bind('<Button-1>', lambda e: webbrowser.open("https://github.com/Heimo-WU"))

        # 软件信息
        soft = tk.LabelFrame(inner, text="💻 软件信息", font=('微软雅黑', 10, 'bold'),
                             bg='#f0f0f0', fg='#2c3e50')
        soft.grid(row=2, column=0, sticky='ew', padx=20, pady=10)
        soft.columnconfigure(0, weight=1)

        # 重新编排软件信息
        soft_info_frame = tk.Frame(soft, bg='#f0f0f0')
        soft_info_frame.grid(row=0, column=0, pady=10, padx=5, sticky='w')

        # 功能列表
        tk.Label(soft_info_frame, text="功能:", font=('微软雅黑', 9, 'bold'), bg='#f0f0f0', fg='#34495e', anchor='w').pack(fill='x')
        tk.Label(soft_info_frame, text="  • 自动查找最新的免费节点订阅", font=('微软雅黑', 9), bg='#f0f0f0', anchor='w').pack(fill='x')
        tk.Label(soft_info_frame, text="  • 智能过滤和验证订阅链接", font=('微软雅黑', 9), bg='#f0f0f0', anchor='w').pack(fill='x')
        tk.Label(soft_info_frame, text="  • 文件管理和预览功能", font=('微软雅黑', 9), bg='#f0f0f0', anchor='w').pack(fill='x')
        tk.Label(soft_info_frame, text="  • 简洁美观的用户界面", font=('微软雅黑', 9), bg='#f0f0f0', anchor='w').pack(fill='x')

        # 节点来源
        source_frame = tk.Frame(soft_info_frame, bg='#f0f0f0')
        source_frame.pack(fill='x', pady=(10, 0))
        tk.Label(source_frame, text="免费节点来源:", font=('微软雅黑', 9, 'bold'), bg='#f0f0f0', fg='#34495e').pack(side='left', anchor='w')
        source_lbl = tk.Label(source_frame, text="85LA", font=('微软雅黑', 9),
                              bg='#f0f0f0', fg='#3498db', cursor='hand2')
        source_lbl.pack(side='left', anchor='w', padx=(5,0))
        source_lbl.bind('<Button-1>', lambda e: webbrowser.open("https://www.85la.com/"))
        
        # 免责声明
        warn = tk.LabelFrame(inner, text="⚠️ 免责声明", font=('微软雅黑', 10, 'bold'),
                             bg='#f0f0f0', fg='#e74c3c')
        warn.grid(row=3, column=0, sticky='ew', padx=20, pady=10)
        warn.columnconfigure(0, weight=1)

        disclaimer = ("本软件仅供学习和研究使用，请遵守当地法律法规。\n"
                      "使用本软件所产生的任何后果由用户自行承担，作者不承担任何责任。\n"
                      "请合理使用网络资源，尊重服务提供商的服务条款。")
        tk.Label(warn, text=disclaimer, font=('微软雅黑', 9), bg='#f0f0f0', fg='#e74c3c',
                 justify='left', wraplength=480,
                 anchor='w').grid(row=0, column=0, pady=10, sticky='w')

    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("提示", f"已复制到剪贴板: {text}")


    # ========== 业务逻辑 ==========
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
                post_url = self.find_post_by_date(current_target_date)
                
                if not post_url:
                    self.log_message(f"未找到 {current_target_date.strftime('%Y年%m月%d日')} 的文章，继续回溯...", "WARN")
                    continue
                
                self.log_message(f"找到文章: {post_url}")
                mihomo_urls = self.extract_mihomo_urls(post_url)
                
                if not mihomo_urls:
                    self.log_message("未找到 Mihomo 订阅链接，继续回溯...", "WARN")
                    continue
                
                self.log_message(f"找到 {len(mihomo_urls)} 个 Mihomo 链接")
                valid_urls = []
                for idx, url in enumerate(mihomo_urls):
                    if not self.is_running:
                        return
                    self.log_message(f"验证链接 {idx+1}/{len(mihomo_urls)}: {url[:50]}...")
                    if self.validate_yaml_url(url):
                        valid_urls.append(url)
                        self.root.after(0, lambda u=url, i=idx: self.add_result_item(f"Mihomo {i+1}", "✅ 有效", u))
                    else:
                        self.root.after(0, lambda u=url, i=idx: self.add_result_item(f"Mihomo {i+1}", "❌ 无效", u))
                
                if valid_urls:
                    self.save_subscription_url(valid_urls[0])
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
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, content)
            self.notebook.select(self.files_tab)
        except Exception as e:
            messagebox.showerror("错误", f"无法读取文件: {e}")

    # ========== 网络与解析 ==========
    def get_date_formats(self, target_date):
        """返回可能的日期格式列表，用于匹配文章标题。"""
        return [
            f"{target_date.year}年{target_date.month}月{target_date.day}日",
            f"{target_date.year}/{target_date.month}/{target_date.day}",
            f"{target_date.year}-{target_date.month:02d}-{target_date.day:02d}",
            target_date.strftime("%Y年%m月%d日"),
        ]

    def make_request(self, url, retries=None):
        """
        封装的HTTP GET请求方法，包含重试和超时逻辑。
        """
        if retries is None:
            retries = self.RETRY_COUNT
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        for attempt in range(retries):
            if not self.is_running:
                return None
            try:
                resp = requests.get(url, timeout=self.TIMEOUT, headers=headers)
                resp.raise_for_status()
                resp.encoding = 'utf-8'
                return resp
            except requests.RequestException as e:
                self.log_message(f"请求失败 (尝试 {attempt + 1}/{retries}): {e}", "WARN")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
        return None

    def find_post_by_date(self, target_date):
        """
        在首页查找指定日期的文章链接。
        """
        try:
            resp = self.make_request(self.BASE_URL)
            if not resp:
                return None
            soup = BeautifulSoup(resp.text, "html.parser")
            date_formats = self.get_date_formats(target_date)
            for h2 in soup.find_all("h2", class_="qzdy-title"):
                title_text = h2.get_text()
                for fmt in date_formats:
                    if fmt in title_text and "免费节点" in title_text:
                        link = h2.find("a")
                        if link and link.get("href"):
                            full_url = link["href"]
                            if not full_url.startswith("http"):
                                full_url = self.BASE_URL.rstrip("/") + full_url
                            return full_url
            return None
        except Exception as e:
            self.log_message(f"查找文章失败: {e}", "ERROR")
            return None

    def extract_mihomo_urls(self, post_url):
        """
        从文章页面提取 Mihomo 订阅链接。
        使用多个正则表达式和上下文过滤来确保准确性。
        """
        try:
            resp = self.make_request(post_url)
            if not resp:
                return []
            content = resp.text
            patterns = [
                r'https://[^\s<>"\'\)]*mihomo[^\s<>"\'\)]*\.ya?ml',
                r'(?i)(?:clash\.?mihomo|mihomo).*?订阅.*?(?:地址|链接).*?(https://[^\s<>"\'\)]+\.ya?ml)',
            ]
            found_urls = set()
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    url = match[0] if isinstance(match, tuple) else match
                    found_urls.add(url)
            
            # 如果没找到特定的mihomo链接，尝试查找所有yaml链接并进行上下文过滤
            if not found_urls:
                all_yaml_pattern = r'https://www\.85la\.com/wp-content/uploads/[^\s<>"\'\)]+\.ya?ml'
                all_yamls = re.findall(all_yaml_pattern, content, re.IGNORECASE)
                for url in all_yamls:
                    url_index = content.find(url)
                    if url_index != -1:
                        start = max(0, url_index - 300)
                        end = min(len(content), url_index + len(url) + 300)
                        context = content[start:end].lower()
                        # 确保上下文中包含 'mihomo' 且不包含 'clash.meta'
                        if 'mihomo' in context and 'clash.meta' not in context:
                            found_urls.add(url)
            
            filtered_urls = []
            for url in found_urls:
                url_index = content.find(url)
                if url_index != -1:
                    start = max(0, url_index - 200)
                    end = min(len(content), url_index + len(url) + 200)
                    context = content[start:end].lower()
                    # 再次过滤，排除可能被误判的clash.meta链接
                    if 'clash.meta' in context and 'mihomo' not in context:
                        self.log_message(f"排除 Clash.meta 链接: {url}")
                        continue
                    filtered_urls.append(url)
            return filtered_urls
        except Exception as e:
            self.log_message(f"提取 Mihomo 链接失败: {e}", "ERROR")
            return []

    def validate_yaml_url(self, url):
        """
        通过HEAD请求验证URL是否可访问。
        """
        try:
            # 使用 HEAD 请求，更快且不下载整个文件
            resp = requests.head(url, timeout=10, allow_redirects=True)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    # ===== 关键：始终保存为 85LA.yaml =====
    def save_subscription_url(self, yaml_url: str) -> bool:
        """
        远程下载 yaml 文件内容，并直接覆盖 85LA.yaml
        """
        try:
            resp = requests.get(yaml_url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0"
            })
            resp.raise_for_status()
            content = resp.text
            save_path = os.path.join(self.save_path_var.get(), "85LA.yaml")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.log_message(f"✅ 已下载并更新节点配置到 {save_path}", "SUCCESS")
            return True
        except Exception as e:
            self.log_message(f"❌ 下载 yaml 失败：{e}", "ERROR")
            return False


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