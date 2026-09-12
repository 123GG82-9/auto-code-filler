import pyautogui
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread
import json
import os

class AutoCodeFiller:
    def __init__(self, root):
        self.root = root
        self.root.title("自动填写代码工具")
        self.root.geometry("800x900")
        self.root.resizable(False, False)
        
        # 变量
        self.input_pos = None
        self.submit_pos = None
        self.is_marking = False
        self.mark_mode = None
        self.codes = []
        self.is_running = False
        self.current_index = 0
        
        # 禁用自动暂停（防止意外暂停）
        pyautogui.FAILSAFE = False
        
        self.create_ui()
        self.load_config()
        
    def create_ui(self):
        """创建用户界面"""
        # 标题
        title_label = tk.Label(self.root, text="🤖 自动填写代码工具", font=("Arial", 20, "bold"), fg="#667eea")
        title_label.pack(pady=15)
        
        # 第一部分：位置标记
        frame1 = ttk.LabelFrame(self.root, text="步骤 1: 标记位置", padding=10)
        frame1.pack(fill="x", padx=10, pady=5)
        
        btn_frame1 = tk.Frame(frame1)
        btn_frame1.pack(fill="x", pady=5)
        
        self.mark_input_btn = tk.Button(btn_frame1, text="标记输入框位置", command=lambda: self.start_marking('input'), 
                                        bg="#667eea", fg="white", width=20, padx=10)
        self.mark_input_btn.pack(side="left", padx=5)
        
        self.mark_submit_btn = tk.Button(btn_frame1, text="标记确认按钮位置", command=lambda: self.start_marking('submit'),
                                         bg="#667eea", fg="white", width=20, padx=10)
        self.mark_submit_btn.pack(side="left", padx=5)
        
        reset_btn = tk.Button(btn_frame1, text="重置标记", command=self.reset_marks,
                             bg="#f0f0f0", width=15, padx=10)
        reset_btn.pack(side="left", padx=5)
        
        # 状态显示
        status_frame = tk.Frame(frame1)
        status_frame.pack(fill="x", pady=10)
        
        self.input_pos_label = tk.Label(status_frame, text="输入框位置: 未标记", font=("Arial", 10), fg="#667eea")
        self.input_pos_label.pack(anchor="w", pady=3)
        
        self.submit_pos_label = tk.Label(status_frame, text="确认按钮位置: 未标记", font=("Arial", 10), fg="#667eea")
        self.submit_pos_label.pack(anchor="w", pady=3)
        
        # 第二部分：代码输入
        frame2 = ttk.LabelFrame(self.root, text="步骤 2: 输入代码列表", padding=10)
        frame2.pack(fill="both", expand=True, padx=10, pady=5)
        
        label = tk.Label(frame2, text="输入代码（每行一个）:")
        label.pack(anchor="w", pady=(0, 5))
        
        # 创建文本框和滚动条
        scrollbar = ttk.Scrollbar(frame2)
        scrollbar.pack(side="right", fill="y")
        
        self.code_input = tk.Text(frame2, height=8, font=("Courier New", 10), yscrollcommand=scrollbar.set)
        self.code_input.pack(fill="both", expand=True, pady=5)
        scrollbar.config(command=self.code_input.yview)
        
        btn_frame2 = tk.Frame(frame2)
        btn_frame2.pack(fill="x", pady=5)
        
        load_btn = tk.Button(btn_frame2, text="从文件加载", command=self.load_file,
                            bg="#f0f0f0", width=15, padx=10)
        load_btn.pack(side="left", padx=5)
        
        clear_btn = tk.Button(btn_frame2, text="清空", command=lambda: self.code_input.delete("1.0", "end"),
                             bg="#f0f0f0", width=15, padx=10)
        clear_btn.pack(side="left", padx=5)
        
        # 第三部分：配置参数
        frame3 = ttk.LabelFrame(self.root, text="步骤 3: 配置参数", padding=10)
        frame3.pack(fill="x", padx=10, pady=5)
        
        # 间隔时间
        param_frame1 = tk.Frame(frame3)
        param_frame1.pack(fill="x", pady=5)
        tk.Label(param_frame1, text="每次填写间隔（毫秒）:", width=25, anchor="w").pack(side="left")
        self.delay_var = tk.StringVar(value="500")
        tk.Spinbox(param_frame1, from_=100, to=5000, textvariable=self.delay_var, width=10).pack(side="left", padx=5)
        
        # 重试次数
        param_frame2 = tk.Frame(frame3)
        param_frame2.pack(fill="x", pady=5)
        tk.Label(param_frame2, text="重试次数:", width=25, anchor="w").pack(side="left")
        self.retry_var = tk.StringVar(value="3")
        tk.Spinbox(param_frame2, from_=1, to=10, textvariable=self.retry_var, width=10).pack(side="left", padx=5)
        
        # 自动点击
        param_frame3 = tk.Frame(frame3)
        param_frame3.pack(fill="x", pady=5)
        self.auto_click_var = tk.BooleanVar(value=True)
        tk.Checkbutton(param_frame3, text="自动点击确认按钮", variable=self.auto_click_var, font=("Arial", 10)).pack(anchor="w")
        
        # 第四部分：执行按钮
        frame4 = ttk.LabelFrame(self.root, text="步骤 4: 执行", padding=10)
        frame4.pack(fill="x", padx=10, pady=5)
        
        btn_frame4 = tk.Frame(frame4)
        btn_frame4.pack(fill="x")
        
        self.start_btn = tk.Button(btn_frame4, text="开始填写", command=self.start,
                                   bg="#10b981", fg="white", font=("Arial", 12, "bold"), width=20, padx=20)
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = tk.Button(btn_frame4, text="停止", command=self.stop,
                                  bg="#ef4444", fg="white", font=("Arial", 12, "bold"), width=20, padx=20, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        # 进度显示
        frame5 = ttk.LabelFrame(self.root, text="执行进度", padding=10)
        frame5.pack(fill="x", padx=10, pady=5)
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(frame5, length=400, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=5)
        
        self.progress_label = tk.Label(frame5, text="准备就绪", font=("Arial", 10), fg="#666")
        self.progress_label.pack(anchor="w")
        
        # 日志显示
        frame6 = ttk.LabelFrame(self.root, text="日志", padding=10)
        frame6.pack(fill="both", expand=True, padx=10, pady=5)
        
        scrollbar2 = ttk.Scrollbar(frame6)
        scrollbar2.pack(side="right", fill="y")
        
        self.log_box = tk.Text(frame6, height=6, font=("Courier New", 9), yscrollcommand=scrollbar2.set, state="disabled")
        self.log_box.pack(fill="both", expand=True)
        scrollbar2.config(command=self.log_box.yview)
    
    def start_marking(self, mode):
        """开始标记"""
        self.is_marking = True
        self.mark_mode = mode
        
        if mode == 'input':
            self.mark_input_btn.config(state="disabled", text="点击��口标记位置...")
        else:
            self.mark_submit_btn.config(state="disabled", text="点击窗口标记位置...")
        
        messagebox.showinfo("提示", f"请在5秒内点击目标位置\n（标记{('输入框' if mode == 'input' else '确认按钮')}）")
        self.mark_position(mode)
    
    def mark_position(self, mode):
        """记录鼠标点击位置"""
        import threading
        
        def wait_for_click():
            time.sleep(0.5)
            x, y = pyautogui.position()
            
            if mode == 'input':
                self.input_pos = (x, y)
                self.input_pos_label.config(text=f"输入框位置: ({x}, {y})")
                self.mark_input_btn.config(state="normal", text="标记输入框位置")
                self.add_log(f"已标记输入框位置: ({x}, {y})", "success")
            else:
                self.submit_pos = (x, y)
                self.submit_pos_label.config(text=f"确认按钮位置: ({x}, {y})")
                self.mark_submit_btn.config(state="normal", text="标记确认按钮位置")
                self.add_log(f"已标记确认按钮位置: ({x}, {y})", "success")
            
            self.is_marking = False
        
        thread = threading.Thread(target=wait_for_click, daemon=True)
        thread.start()
    
    def reset_marks(self):
        """重置标记"""
        self.input_pos = None
        self.submit_pos = None
        self.input_pos_label.config(text="输入框位置: 未标记")
        self.submit_pos_label.config(text="确认按钮位置: 未标记")
        self.add_log("已重置所有标记", "info")
    
    def load_file(self):
        """加载文件"""
        file_path = filedialog.askopenfilename(filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.code_input.delete("1.0", "end")
                self.code_input.insert("1.0", content)
                self.add_log(f"已加载文件: {os.path.basename(file_path)}", "success")
            except Exception as e:
                messagebox.showerror("错误", f"加载文件失败: {str(e)}")
    
    def start(self):
        """开始填写"""
        if not self.input_pos or not self.submit_pos:
            messagebox.showerror("错误", "请先标记输入框和确认按钮位置")
            return
        
        code_text = self.code_input.get("1.0", "end").strip()
        if not code_text:
            messagebox.showerror("错误", "请输入代码")
            return
        
        self.codes = [code.strip() for code in code_text.split('\n') if code.strip()]
        if not self.codes:
            messagebox.showerror("错误", "没有有效的代码")
            return
        
        self.is_running = True
        self.current_index = 0
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        self.add_log(f"📝 开始填写 {len(self.codes)} 个代码", "info")
        
        # 在线程中执行
        thread = Thread(target=self.fill_codes, daemon=True)
        thread.start()
    
    def fill_codes(self):
        """填写代码"""
        delay = int(self.delay_var.get()) / 1000  # 转换为秒
        retries = int(self.retry_var.get())
        auto_click = self.auto_click_var.get()
        
        while self.current_index < len(self.codes) and self.is_running:
            code = self.codes[self.current_index]
            success = False
            
            for attempt in range(1, retries + 1):
                if not self.is_running:
                    break
                
                try:
                    self.add_log(f"📌 第 {self.current_index + 1}/{len(self.codes)} 次 (尝试 {attempt}/{retries}): 输入 \"{code}\"", "info")
                    
                    # 点击输入框
                    pyautogui.click(self.input_pos[0], self.input_pos[1])
                    time.sleep(0.2)
                    
                    # 清空输入框
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.1)
                    
                    # 逐字输入
                    pyautogui.typewrite(code, interval=0.05)
                    time.sleep(0.2)
                    
                    self.add_log(f"✅ 成功输入: \"{code}\"", "success")
                    
                    # 自动点击确认按钮
                    if auto_click:
                        time.sleep(0.3)
                        pyautogui.click(self.submit_pos[0], self.submit_pos[1])
                        self.add_log(f"🔘 已点击确认按钮", "info")
                    
                    time.sleep(delay)
                    success = True
                    break
                    
                except Exception as e:
                    self.add_log(f"❌ 尝试 {attempt} 失败: {str(e)}", "error")
                    if attempt < retries:
                        time.sleep(1)
            
            if success:
                self.current_index += 1
            else:
                self.add_log(f"⏭️ 跳过该代码，继续下一个", "warning")
                self.current_index += 1
            
            # 更新进度
            self.update_progress()
        
        if self.is_running:
            self.add_log(f"✨ 完成! 已填写 {self.current_index}/{len(self.codes)} 个代码", "success")
        else:
            self.add_log(f"⛔ 已停止，完成 {self.current_index}/{len(self.codes)} 个代码", "warning")
        
        self.is_running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
    
    def update_progress(self):
        """更新进度"""
        progress = (self.current_index / len(self.codes)) * 100 if self.codes else 0
        self.progress_var.set(progress)
        self.progress_label.config(text=f"进度: {self.current_index}/{len(self.codes)} ({int(progress)}%)")
        self.root.update()
    
    def stop(self):
        """停止执行"""
        self.is_running = False
        self.add_log("⛔ 已停止执行", "warning")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
    
    def add_log(self, message, level="info"):
        """添加日志"""
        self.log_box.config(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        
        # 设置标签
        self.log_box.tag_config("success", foreground="#10b981")
        self.log_box.tag_config("error", foreground="#ef4444")
        self.log_box.tag_config("info", foreground="#667eea")
        self.log_box.tag_config("warning", foreground="#f59e0b")
        
        log_text = f"[{timestamp}] {message}\n"
        self.log_box.insert("end", log_text, level)
        self.log_box.see("end")
        self.log_box.config(state="disabled")
        self.root.update()
    
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    config = json.load(f)
                    self.delay_var.set(str(config.get("delay", 500)))
                    self.retry_var.set(str(config.get("retry", 3)))
                    self.auto_click_var.set(config.get("auto_click", True))
        except:
            pass
    
    def save_config(self):
        """保存配置"""
        config = {
            "delay": int(self.delay_var.get()),
            "retry": int(self.retry_var.get()),
            "auto_click": self.auto_click_var.get()
        }
        with open("config.json", "w") as f:
            json.dump(config, f)

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoCodeFiller(root)
    root.mainloop()
    app.save_config()
