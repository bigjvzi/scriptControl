import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, simpledialog, messagebox
from importlib import import_module
import json
import sys
import io
import threading
import queue
import os

class ScriptRunnerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python脚本管理中心")
        
        # 脚本配置加载
        self.scripts = self.load_script_configs()

        # 配置文件路径
        self.saved_config_path = "config/history.json"
        self.saved_configs = self.load_saved_configs()
        
        # 主界面布局
        self.create_widgets()
        self.current_script = None

        # 新增输出显示区域
        self.create_output_area()
        
        # 重定向标准输出
        self.redirect_stdout()

        # 新增二次输入相关属性
        self.input_queue = queue.Queue()
        self.current_script_thread = None
        self.input_window = None

    def load_saved_configs(self):
        """加载保存的配置"""
        if not os.path.exists(self.saved_config_path):
            return {}
        try:
            with open(self.saved_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def create_output_area(self):
        output_frame = ttk.LabelFrame(self.root, text="执行输出")
        output_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame, 
            state='disabled'
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

    def redirect_stdout(self):
        class StdoutRedirector(io.TextIOBase):
            def __init__(self, widget):
                self.widget = widget
            
            def write(self, message):
                self.widget.configure(state='normal')
                self.widget.insert(tk.END, message)
                self.widget.see(tk.END)
                self.widget.configure(state='disabled')
                return len(message)

        sys.stdout = StdoutRedirector(self.output_text)
        sys.stderr = StdoutRedirector(self.output_text)
    
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
            elif param['type'] == 'folder':
                frame = ttk.Frame(self.param_frame)
                entry = ttk.Entry(frame)
                entry.grid(row=0, column=0, padx=5, sticky=tk.EW)
                ttk.Button(frame, text="浏览", 
                         command=lambda e=entry: self.browse_folder(e)).grid(row=0, column=1)
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

        # 自动选择使用次数最多的配置
        sorted_configs = self.get_sorted_configs()
        print(sorted_configs)
        if sorted_configs:
            self.apply_config(sorted_configs[0][0])
    
    def browse_file(self, entry_widget):
        filename = filedialog.askopenfilename()
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)

    def browse_folder(self, entry_widget):
        foldername = filedialog.askdirectory()
        if foldername:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, foldername)

    
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
        def run_script():
            try:
                script_config = self.current_script
                module_path = f"scripts.{script_config['module']}"
                
                # 动态导入脚本模块
                script_module = import_module(module_path)

                # 创建脚本执行上下文
                context = {
                    'request_input': self.request_input_handler,
                    'show_confirmation': self.show_confirmation_handler
                }
                
                # 获取参数并执行
                params = self.get_parameters()
                if hasattr(script_module, 'main'):
                    if self.current_script.get('interactive'):
                        script_module.main(**params, **context)
                    else:
                        script_module.main(**params)
                    print("✅ 脚本执行完成")
                else:
                    print("❌ 脚本缺少main函数入口")
            except Exception as e:
                print(f"❌ 执行出错: {str(e)}")
            finally:
                self.root.event_generate('<<ScriptFinished>>', when='tail')
        
        # 清空输出区域
        self.output_text.configure(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.configure(state='disabled')
        
        # 在新线程中执行
        threading.Thread(target=run_script, daemon=True).start()
        # 保存当前线程引用
        self.current_script_thread = threading.Thread(target=run_script, daemon=True)
        self.current_script_thread.start()
        self.root.bind('<<ScriptFinished>>', lambda e: self.on_script_finished())
    
    def request_input_handler(self, prompt, input_type="text"):
        """处理脚本的输入请求"""
        self.input_queue.put("WAITING_INPUT")
        result = []
        
        # 在主线程创建输入对话框
        self.root.after(0, lambda: result.append(
            self.create_input_dialog(prompt, input_type)
        ))
        
        # 等待用户输入
        while not result:
            if self.input_queue.get() == "CANCEL_SCRIPT":
                raise RuntimeError("用户取消执行")
        
        return result[0]
    
    def show_confirmation_handler(self, message):
        """处理确认对话框"""
        self.input_queue.put("WAITING_CONFIRM")
        result = []
        
        self.root.after(0, lambda: result.append(
            messagebox.askyesno("确认操作", message)
        ))
        
        while not result:
            if self.input_queue.get() == "CANCEL_SCRIPT":
                raise RuntimeError("用户取消执行")
            time.sleep(0.1)
        
        return result[0]
    
    def create_input_dialog(self, prompt, input_type):
        """创建动态输入对话框"""
        self.input_window = tk.Toplevel(self.root)
        self.input_window.title("脚本需要输入")
        
        ttk.Label(self.input_window, text=prompt).pack(padx=10, pady=5)
        
        entry = None
        if input_type == "file":
            frame = ttk.Frame(self.input_window)
            entry = ttk.Entry(frame)
            ttk.Button(frame, text="浏览", 
                      command=lambda: self.browse_file(entry)).pack(side=tk.RIGHT)
            entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
            frame.pack(fill=tk.X, padx=5)
        else:
            entry = ttk.Entry(self.input_window)
            entry.pack(padx=5, fill=tk.X)
        
        def submit():
            self.input_queue.put(entry.get())
            self.input_window.destroy()
        
        ttk.Button(self.input_window, text="提交", command=submit).pack(pady=5)
        
        self.input_window.protocol("WM_DELETE_WINDOW", self.cancel_input)
        self.center_window(self.input_window)

    def cancel_input(self):
        self.input_queue.put("CANCEL_SCRIPT")
        self.input_window.destroy()

    def center_window(self, window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'+{x}+{y}')

    def on_script_finished(self):
        """脚本执行完成后的清理"""
        if self.input_window and self.input_window.winfo_exists():
            self.input_window.destroy()
        self.current_script_thread = None
    
    def save_config(self):
        """保存当前配置"""
        if not self.current_script:
            messagebox.showwarning("警告", "请先选择脚本！")
            return
        
        # 获取配置名称
        config_name = simpledialog.askstring("保存配置", "请输入配置名称：")
        if not config_name:
            return
        
        # 获取当前参数值
        params = self.get_parameters()
        script_name = self.script_combobox.get()
        
        # 更新配置数据
        if script_name not in self.saved_configs:
            self.saved_configs[script_name] = {}
        self.saved_configs[script_name][config_name] = params
        
        # 保存到文件
        try:
            with open(self.saved_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.saved_configs, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", "配置保存成功！")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{str(e)}")
    
    def load_config(self):
        # 创建带排序的配置对话框
        dialog = ConfigDialog(
            parent=self.root,
            title="选择配置",
            configs=self.get_sorted_configs(),
            on_edit=self.handle_config_edit
        )
        dialog.show()

    def handle_config_edit(self, old_name):
        # 获取原始配置数据
        original = self.saved_configs[self.current_script][old_name]
        
        # 创建编辑对话框
        dialog = EditConfigDialog(
            self.root,
            original_name=old_name,
            original_params=original['params'],
            on_save=lambda new_name, params: self.update_config(old_name, new_name, params)
        )
        dialog.show()

    def update_config(self, old_name, new_name, params):
        # 处理名称冲突
        if new_name != old_name and new_name in self.saved_configs[self.current_script]:
            if not messagebox.askyesno("确认", "配置已存在，是否覆盖？"):
                return
        
        # 更新配置数据
        config_data = {
            'params': params,
            'usage_count': self.saved_configs[self.current_script][old_name]['usage_count'],
            'last_used': datetime.now().isoformat()
        }
        
        # 删除旧配置（如果重命名）
        if new_name != old_name:
            del self.saved_configs[self.current_script][old_name]
        
        # 保存新配置
        self.saved_configs[self.current_script][new_name] = config_data
        self.save_config_file()

    def apply_config(self, config_name):
        """应用配置并更新统计"""
        config_data = self.saved_configs[self.current_script][config_name]
        
        # 更新使用统计
        config_data['usage_count'] = config_data.get('usage_count', 0) + 1
        config_data['last_used'] = datetime.now().isoformat()
        
        # 保存到文件
        self.save_config_file()
        
        # 应用参数
        self._fill_parameters(config_data['params'])

    def get_sorted_configs(self):
        """获取排序后的配置列表"""
        configs = self.saved_configs.get(self.current_script["module"], {})["configs"].items()
        return sorted(
            configs,
            key=lambda x: (x[1]['usage_count'], x[1]['last_used']),
            reverse=True
        )
    
class ConfigDialog(tk.Toplevel):
    def __init__(self, parent, configs, on_edit):
        super().__init__(parent)
        self.configs = configs
        self.on_edit = on_edit
        
        # 创建列表组件
        self.tree = ttk.Treeview(self, columns=('usage', 'last_used'), show='headings')
        self.tree.heading('#0', text='配置名称')
        self.tree.heading('usage', text='使用次数')
        self.tree.heading('last_used', text='最后使用')
        
        # 填充数据
        for name, data in configs:
            self.tree.insert('', 'end', text=name,
                            values=(data['usage_count'], 
                                   data['last_used'][:16]))
        
        # 添加操作按钮
        btn_frame = ttk.Frame(self)
        ttk.Button(btn_frame, text="加载", command=self.on_load).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="编辑", command=self.on_edit).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="删除", command=self.on_delete).pack(side=tk.LEFT)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        btn_frame.pack(pady=5)
    
    def on_edit(self):
        selected = self.tree.selection()
        if selected:
            config_name = self.tree.item(selected[0], 'text')
            self.on_edit(config_name)

class EditConfigDialog(tk.Toplevel):
    def __init__(self, parent, original_name, original_params, on_save):
        super().__init__(parent)
        self.on_save = on_save
        
        # 名称编辑
        ttk.Label(self, text="配置名称:").grid(row=0, column=0)
        self.name_entry = ttk.Entry(self)
        self.name_entry.insert(0, original_name)
        self.name_entry.grid(row=0, column=1)
        
        # 参数编辑
        self.param_entries = {}
        for row, (key, value) in enumerate(original_params.items(), start=1):
            ttk.Label(self, text=f"{key}:").grid(row=row, column=0)
            entry = ttk.Entry(self)
            entry.insert(0, value)
            entry.grid(row=row, column=1)
            self.param_entries[key] = entry
        
        # 操作按钮
        btn_frame = ttk.Frame(self)
        ttk.Button(btn_frame, text="保存", command=self.save).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side=tk.LEFT)
        btn_frame.grid(row=row+1, columnspan=2)
    
    def save(self):
        new_name = self.name_entry.get()
        params = {k: v.get() for k, v in self.param_entries.items()}
        self.on_save(new_name, params)
        self.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptRunnerApp(root)
    root.mainloop()