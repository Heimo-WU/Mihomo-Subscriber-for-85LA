import tkinter as tk
from tkinter import ttk, scrolledtext
import webbrowser  # Added import to fix undefined variable

from src.gui.ui_utils import copy_to_clipboard, on_title_click


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
    title_lbl = tk.Label(inner, text="🛸 Mihomo Subscriber 👾\nVersion 1.0.4",
                         font=('微软雅黑', 16, 'bold'), bg='#2c3e50', fg='white',
                         justify='center', pady=15)
    title_lbl.grid(row=0, column=0, sticky='ew', pady=(0, 15))
    
    title_lbl.bind('<Button-1>', lambda e: on_title_click(self, e))

    # 作者信息 (row=1)
    author_info = tk.LabelFrame(inner, text="🎅 作者信息", font=('微软雅黑', 10, 'bold'),
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
    email_label.bind('<Button-1>', lambda e: copy_to_clipboard(self, "heimo0721@gmail.com"))

    # GitHub
    github_frame = tk.Frame(author_info, bg='#f0f0f0')
    github_frame.pack(fill='x', pady=3)
    tk.Label(github_frame, text="GitHub:", font=('微软雅黑', 9, 'bold'),
             bg='#f0f0f0', fg='#34495e', width=8, anchor='w').pack(side='left')
    github_label = tk.Label(github_frame, text="https://github.com/Heimo-WU", font=('微软雅黑', 9),
                            bg='#f0f0f0', fg='#3498db', cursor='hand2')
    github_label.pack(side='left')
    github_label.bind('<Button-1>', lambda e: webbrowser.open("https://github.com/Heimo-WU"))

    # 软件信息 (row=2)
    intro_frame = tk.LabelFrame(
        inner,
        text="💻 软件信息",
        font=('微软雅黑', 10, 'bold'),
        bg='#f0f0f0',
        fg='#2c3e50',
        relief='groove',
        bd=2
    )
    intro_frame.grid(row=2, column=0, sticky='ew', padx=20, pady=10)
    intro_frame.columnconfigure(0, weight=1)

    # 将所有功能和信息整合到一个多行字符串中
    intro_text = (
        "Mihomo Subscriber 是一个半自动化的代理订阅管理工具，它能够\n"
        "智能搜索、验证并下载最新的免费代理节点订阅，轻松管理代理配置。\n\n"
        "🚀 主要功能:\n"
        " • 自动查找最新的免费节点订阅\n"
        " • 完整的操作记录和错误处理\n"
        " • 智能过滤和验证订阅链接\n"
        " • 文件管理和预览功能\n"
        " • 简洁美观的用户界面\n"
        " • 隐藏的彩蛋动画"
    )

    # 使用单个tk.Label来显示所有信息
    tk.Label(
        intro_frame,
        text=intro_text,
        font=('微软雅黑', 9),
        bg='#f0f0f0',
        fg="#131618",
        justify='left',
        anchor='w',
        wraplength=600
    ).pack(fill='x', padx=15, pady=10)

    # 数据来源 (新嵌入部分，row=3)
    source_frame = tk.LabelFrame(inner, text="📡 数据来源", font=('微软雅黑', 10, 'bold'),
                                 bg='#f0f0f0', fg='#2c3e50', relief='groove', bd=2)
    source_frame.grid(row=3, column=0, sticky='ew', padx=20, pady=10)
    source_frame.columnconfigure(0, weight=1)

    source_info_frame = tk.Frame(source_frame, bg='#f0f0f0')
    source_info_frame.pack(fill='x', padx=15, pady=10)

    tk.Label(source_info_frame, text="免费节点来源:", font=('微软雅黑', 9, 'bold'),
             bg='#f0f0f0', fg='#2c3e50').pack(side='left')

    source_link = tk.Label(source_info_frame, text="85LA (www.85la.com)",
                           font=('微软雅黑', 9, 'bold'),
                           bg='#f0f0f0', fg='#3498db', cursor='hand2')
    source_link.pack(side='left', padx=(10, 0))
    source_link.bind('<Button-1>', lambda e: webbrowser.open("https://www.85la.com/"))

    tk.Label(source_frame, text="感谢 85LA 提供的免费节点服务！", font=('微软雅黑', 9),
             bg='#f0f0f0', fg='#2c3e50').pack(padx=15, pady=(0, 10))

    # 免责声明 (row=4)
    warn = tk.LabelFrame(inner, text="⚠️ 免责声明", font=('微软雅黑', 10, 'bold'),
                         bg='#f0f0f0', fg='#e74c3c')
    warn.grid(row=4, column=0, sticky='ew', padx=20, pady=10)
    warn.columnconfigure(0, weight=1)

    disclaimer = ("本软件仅供学习和研究使用，请遵守当地法律法规。\n"
                  "使用本软件所产生的任何后果由用户自行承担，作者不承担任何责任。\n"
                  "请合理使用网络资源，尊重服务提供商的服务条款。")
    
    tk.Label(warn, text=disclaimer, font=('微软雅黑', 9), bg='#f0f0f0', fg='#e74c3c',
             justify='left', wraplength=480,
             anchor='w').grid(row=0, column=0, pady=10, sticky='w')