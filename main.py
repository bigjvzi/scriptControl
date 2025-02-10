import tkinter as tk
from tkinter import ttk, filedialog
import importlib
import json
import os

class ScriptRunnerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python脚本管理中心")
        
        # 脚本配置加载
        self.scripts = self.load_script_configs()
        
        # 主界面布局
        self.create_widgets()
        self.current_script = None
    
    def load_script_configs(self):
        """加载脚本配置文件"""
        with open('config/script_configs.json', encoding='utf-8') as f:
            return json.load(f)
    
    def create_widgets(self):
        # 脚本选择区域
        script_frame = ttk.LabelFrame(self.root, text="选择脚本")
        script_frame.pack(padx=10, pady=5, fill=tk.X)
        
        self.script_combobox = ttk.Combobox(script_frame, values=list(self.scripts.keys()))
        self.script_combobox.pack(padx=5, pady=5, fill=tk.X)
        self.script_combobox.bind("<<ComboboxSelected>>", self.update_parameters)
        
        # 参数输入区域
        self.param_frame = ttk.LabelFrame(self.root, text="脚本参数")
        self.param_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        # 控制按钮区域
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(padx=10, pady=5, fill=tk.X)
        
        ttk.Button(btn_frame, text="执行", command=self.execute_script).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="保存配置", command=self.save_config).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="加载配置", command=self.load_config).pack(side=tk.RIGHT)
    
    def update_parameters(self, event):
        # 清除旧参数输入框
        for widget in self.param_frame.winfo_children():
            widget.destroy()
        
        script_name = self.script_combobox.get()
        self.current_script = self.scripts[script_name]
        
        # 创建新的参数输入组件
        row = 0
        self.input_widgets = {}
        for param in self.current_script['parameters']:
            label = ttk.Label(self.param_frame, text=param['label'])
            label.grid(row=row, column=0, padx=5, pady=2, sticky=tk.W)
            
            if param['type'] == 'file':
                frame = ttk.Frame(self.param_frame)
                entry = ttk.Entry(frame)
                entry.grid(row=0, column=0, padx=5, sticky=tk.EW)
                ttk.Button(frame, text="浏览", 
                         command=lambda e=entry: self.browse_file(e)).grid(row=0, column=1)
                frame.grid_columnconfigure(0, weight=1)
                frame.grid(row=row, column=1, sticky=tk.EW)
                self.input_widgets[param['name']] = entry
            elif param['type'] == 'dropdown':
                cb = ttk.Combobox(self.param_frame, values=param['options'])
                cb.grid(row=row, column=1, padx=5, pady=2, sticky=tk.EW)
                self.input_widgets[param['name']] = cb
            else:
                entry = ttk.Entry(self.param_frame)
                entry.grid(row=row, column=1, padx=5, pady=2, sticky=tk.EW)
                self.input_widgets[param['name']] = entry
            
            row += 1
        
        # 添加预览按钮（如果配置需要）
        if self.current_script.get('preview'):
            preview_btn = ttk.Button(self.param_frame, text="预览文件内容",
                                   command=self.preview_file)
            preview_btn.grid(row=row, columnspan=2, pady=5)
    
    def browse_file(self, entry_widget):
        filename = filedialog.askopenfilename()
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)
    
    def preview_file(self):
        # 实现文件预览逻辑
        pass
    
    def get_parameters(self):
        params = {}
        for name, widget in self.input_widgets.items():
            if isinstance(widget, ttk.Entry) or isinstance(widget, ttk.Combobox):
                params[name] = widget.get()
        return params
    
    def execute_script(self):
        # 执行脚本逻辑
        pass
    
    def save_config(self):
        # 配置保存逻辑
        pass
    
    def load_config(self):
        # 配置加载逻辑
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptRunnerApp(root)
    root.mainloop()