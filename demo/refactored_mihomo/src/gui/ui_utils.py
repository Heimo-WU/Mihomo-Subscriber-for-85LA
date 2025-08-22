import random
import tkinter as tk
from tkinter import messagebox


def copy_to_clipboard(self, text):
    """复制文本到剪贴板"""
    self.root.clipboard_clear()
    self.root.clipboard_append(text)
    messagebox.showinfo("提示", f"已复制到剪贴板: {text}")


def on_title_click(self, event):
    """处理标题点击事件的彩蛋功能"""
    self.easter_egg_clicks += 1
    
    # 重置计时器
    if self.easter_egg_timer:
        self.root.after_cancel(self.easter_egg_timer)
    
    # 3秒后重置点击计数
    self.easter_egg_timer = self.root.after(3000, lambda: self.reset_easter_egg())
    
    # 每次点击都有视觉反馈
    title_flash_effect(self, event.widget)
    
    # 达到15次点击触发彩蛋
    if self.easter_egg_clicks >= 15:
        # 并行触发彩虹效果和抖动动画
        rainbow_title_effect(self)
        shake_window(self)


def title_flash_effect(self, title_widget):
    """标题闪烁效果"""
    original_bg = title_widget.cget('bg')
    
    # 闪烁
    title_widget.config(bg="#8F00FF")
    
    # 150毫秒后恢复原色
    self.root.after(150, lambda: title_widget.config(bg=original_bg))


def reset_easter_egg(self):
    """重置彩蛋点击计数"""
    self.easter_egg_clicks = 0
    self.easter_egg_timer = None


def shake_window(self):
    """窗口抖动效果"""
    # 获取当前窗口位置
    current_x = self.root.winfo_x()
    current_y = self.root.winfo_y()
    
    # 抖动动画
    def shake_step(step):
        if step > 0:
            # 随机偏移
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-10, 10)
            self.root.geometry(f"+{current_x + offset_x}+{current_y + offset_y}")
            
            # 继续下一步抖动
            self.root.after(50, lambda: shake_step(step - 1))
        else:
            # 抖动结束，回到原位
            self.root.geometry(f"+{current_x}+{current_y}")
    
    shake_step(20)  # 抖动20次


def rainbow_title_effect(self):
    """彩虹标题效果"""
    # 找到标题标签
    title_label = None
    
    # 遍历关于标签页寻找标题
    def find_title_label(widget):
        nonlocal title_label
        if isinstance(widget, tk.Label) and "Mihomo Subscriber" in str(widget.cget('text')):
            title_label = widget
            return
        
        # 递归查找子控件
        for child in widget.winfo_children():
            find_title_label(child)
    
    find_title_label(self.about_tab)
    
    if not title_label:
        return
    
    # 彩虹颜色列表
    colors = ['#FF6B6B', '#FF8C00', '#FFEAA7', '#27AE60', '#4ECDC4', '#45B7D1', '#9B59B6']
    original_bg = title_label.cget('bg')
    original_fg = title_label.cget('fg')
    
    # 彩虹动画
    def rainbow_step(step, color_index):
        if step > 0:
            color = colors[color_index % len(colors)]
            title_label.config(bg=color, fg='white')
            
            # 继续下一步
            self.root.after(200, lambda: rainbow_step(step - 1, color_index + 1))
        else:
            # 动画结束，恢复原色
            title_label.config(bg=original_bg, fg=original_fg)
            
            # 重置点击计数
            self.easter_egg_clicks = 0
    
    rainbow_step(15, 0)  # 15步彩虹动画