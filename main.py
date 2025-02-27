import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox, scrolledtext
import json
import os
import sys
import io
import threading
import queue
from datetime import datetime
from importlib import import_module

class ScriptRunnerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python脚本管理中心")
        
        # 初始化配置
        self.script_configs = self.load_config('config/script_configs.json')
        self.saved_configs = self.load_config('config/saved_configs.json')
        self.current_script = None
        self.current_script_name = None
        
        # 初始化界面
        self.create_widgets()
        self.create_output_area()
        self.redirect_stdout()
        
        # 初始化交互相关
        self.input_queue = queue.Queue()
        self.current_script_thread = None
        self.input_window = None

    def load_config(self, filename):
        """加载配置文件"""
        if not os.path.exists(filename):
            return {}
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            messagebox.showerror("错误", f"加载配置文件失败: {str(e)}")
            return {}

    def save_config_file(self):
        """保存配置文件"""
        try:
            with open('config/saved_configs.json', 'w', encoding='utf-8') as f:
                json.dump(self.saved_configs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")

    def create_widgets(self):
        """创建主界面组件"""
        # 脚本选择区域
        script_frame = ttk.LabelFrame(self.root, text="选择脚本")
        script_frame.pack(padx=10, pady=5, fill=tk.X)
        
        self.script_combobox = ttk.Combobox(
            script_frame, 
            values=list(self.script_configs.keys())
        )
        self.script_combobox.pack(padx=5, pady=5, fill=tk.X)
        self.script_combobox.bind("<<ComboboxSelected>>", self.on_script_selected)
        
        # 参数输入区域
        self.param_frame = ttk.LabelFrame(self.root, text="脚本参数")
        self.param_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        # 控制按钮区域
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(padx=10, pady=5, fill=tk.X)
        
        ttk.Button(btn_frame, text="执行", command=self.execute_script).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="保存配置", command=self.save_config).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="加载配置", command=self.load_config_dialog).pack(side=tk.RIGHT)

    def create_output_area(self):
        """创建输出区域"""
        output_frame = ttk.LabelFrame(self.root, text="执行输出")
        output_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame, 
            wrap=tk.WORD,
            state='disabled'
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

    def redirect_stdout(self):
        """重定向标准输出"""
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

    def on_script_selected(self, event):
        """处理脚本选择事件"""
        script_name = self.script_combobox.get()
        self.current_script_name = script_name
        self.current_script = self.script_configs[script_name]
        self.create_parameter_inputs()
        self.auto_load_config()

    def create_parameter_inputs(self):
        """创建参数输入组件"""
        # 清除旧组件
        for widget in self.param_frame.winfo_children():
            widget.destroy()
        
        # 创建新组件
        self.input_widgets = {}
        for row, param in enumerate(self.current_script['parameters']):
            label = ttk.Label(self.param_frame, text=param['label'])

            if "type" not in param:
                label.grid(row=row, padx=5, pady=2, sticky=tk.W)
                continue

            label.grid(row=row, column=1, padx=5, pady=2, sticky=tk.W)

            if param['type'] == 'file':
                self.create_file_input(row, param)
            elif param['type'] == 'folder':
                self.create_folder_input(row, param)
            elif param['type'] == 'dropdown':
                self.create_dropdown(row, param)
            else:
                self.create_basic_input(row, param)

    def create_file_input(self, row, param):
        """创建文件选择组件"""
        frame = ttk.Frame(self.param_frame)
        entry = ttk.Entry(frame)
        entry.grid(row=0, column=0, padx=5, sticky=tk.EW)
        
        ttk.Button(frame, text="浏览", 
                 command=lambda: self.browse_file(entry, param.get('filetype')))\
            .grid(row=0, column=1)
        
        frame.grid_columnconfigure(0, weight=1)
        frame.grid(row=row, column=0, sticky=tk.EW)
        self.input_widgets[param['name']] = entry

    def create_folder_input(self, row, param):
        """创建文件夹选择组件"""
        frame = ttk.Frame(self.param_frame)
        entry = ttk.Entry(frame)
        entry.grid(row=0, column=0, padx=5, sticky=tk.EW)
        
        ttk.Button(frame, text="浏览", 
                   command=lambda: self.browse_file(entry, 'directory'))\
            .grid(row=0, column=1)
        
        frame.grid_columnconfigure(0, weight=1)
        frame.grid(row=row, column=0, sticky=tk.EW)
        self.input_widgets[param['name']] = entry

    def create_dropdown(self, row, param):
        """创建下拉选择框"""
        cb = ttk.Combobox(self.param_frame, values=param['options'])
        cb.grid(row=row, column=0, padx=5, pady=2, sticky=tk.EW)
        if 'default' in param:
            cb.set(param['default'])
        self.input_widgets[param['name']] = cb

    def create_basic_input(self, row, param):
        """创建基本输入框"""
        entry = ttk.Entry(self.param_frame)
        entry.grid(row=row, column=0, padx=5, pady=2, sticky=tk.EW)
        if 'default' in param:
            entry.insert(0, param['default'])
        self.input_widgets[param['name']] = entry

    def browse_file(self, entry_widget, filetype=None):
        """文件浏览对话框"""
        if filetype == 'directory':
            filename = filedialog.askdirectory()
        else:
            filename = filedialog.askopenfilename()
        
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)

    def auto_load_config(self):
        """自动加载配置"""
        script_configs = self.saved_configs.get(self.current_script_name, {})
        if not script_configs.get('configs'):
            return
        
        # 获取使用最多的配置
        sorted_configs = sorted(
            script_configs['configs'].items(),
            key=lambda x: x[1]['last_used'], reverse=True)
        
        
        if sorted_configs:
            config_name = sorted_configs[0][0]
            self.apply_config(config_name, update_stats=False)

    def get_parameters(self):
        """获取当前参数值"""
        return {name: widget.get() for name, widget in self.input_widgets.items()}

    def execute_script(self):
        """执行脚本"""
        def run_script():
            try:
                module = import_module(f"scripts.{self.current_script['module']}")
                params = self.get_parameters()
                
                # 更新配置使用统计
                if hasattr(self, 'current_config_name'):
                    self.update_config_usage(self.current_config_name)
                
                # 执行上下文
                context = {
                    'request_input': self.request_input,
                    'show_confirmation': self.show_confirmation
                }
                
                module.main(**params)
                print("✅ 脚本执行完成")
            except Exception as e:
                print(f"❌ 执行出错: {str(e)}")
            finally:
                self.root.event_generate('<<ScriptFinished>>')

        # 清空输出
        self.output_text.configure(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.configure(state='disabled')
        
        # 启动线程
        self.current_script_thread = threading.Thread(target=run_script, daemon=True)
        self.current_script_thread.start()
        self.root.bind('<<ScriptFinished>>', lambda e: self.on_script_finished())

    def request_input(self, prompt, input_type="text"):
        """处理脚本输入请求"""
        self.input_queue.put("WAITING_INPUT")
        result = []
        
        def get_input():
            if input_type == "file":
                filename = filedialog.askopenfilename(title=prompt)
                result.append(filename)
            else:
                answer = simpledialog.askstring("输入请求", prompt)
                result.append(answer)
        
        self.root.after(0, get_input)
        
        while not result:
            if self.input_queue.get() == "CANCEL_SCRIPT":
                raise RuntimeError("用户取消执行")
            self.root.update()
        
        return result[0]

    def show_confirmation(self, message):
        """显示确认对话框"""
        self.input_queue.put("WAITING_CONFIRM")
        result = []
        
        def get_confirmation():
            result.append(messagebox.askyesno("确认操作", message))
        
        self.root.after(0, get_confirmation)
        
        while not result:
            if self.input_queue.get() == "CANCEL_SCRIPT":
                raise RuntimeError("用户取消执行")
            self.root.update()
        
        return result[0]

    def save_config(self):
        """保存当前配置"""
        if not self.current_script:
            messagebox.showwarning("警告", "请先选择脚本！")
            return
        
        config_name = simpledialog.askstring("保存配置", "请输入配置名称：")
        if not config_name:
            return
        
        script_name = self.current_script_name
        params = self.get_parameters()
        
        # 初始化配置存储结构
        if script_name not in self.saved_configs:
            self.saved_configs[script_name] = {
                "configs": {},
                "default_config": None
            }
        
        # 处理重名
        if config_name in self.saved_configs[script_name]['configs']:
            if not messagebox.askyesno("确认", "配置已存在，是否覆盖？"):
                return
        
        # 保存配置
        self.saved_configs[script_name]['configs'][config_name] = {
            "params": params,
            "usage_count": 0,
            "last_used": datetime.now().isoformat()
        }
        
        self.save_config_file()
        messagebox.showinfo("成功", "配置保存成功！")

    def load_config_dialog(self):
        """加载配置对话框"""
        if not self.current_script_name:
            messagebox.showwarning("警告", "请先选择脚本！")
            return
        
        script_configs = self.saved_configs.get(self.current_script_name, {})
        if not script_configs.get('configs'):
            messagebox.showinfo("提示", "该脚本没有保存的配置")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("选择配置")
        
        # 创建列表
        tree = ttk.Treeview(dialog, columns=('#0', 'usage', 'last_used'), show='headings')
        tree.heading('#0', text='配置名称')
        tree.heading('usage', text='使用次数')
        tree.heading('last_used', text='最后使用时间')
        
        # 排序配置
        sorted_configs = sorted(
            script_configs['configs'].items(),
            key=lambda x: x[1]['last_used'],
            reverse=False
        )
        
        for name, data in sorted_configs:
            tree.insert('', 'end', text=name,
                       values=(name, data['last_used'][:16], data['usage_count']))
        
        # 添加按钮
        btn_frame = ttk.Frame(dialog)
        ttk.Button(btn_frame, text="加载", 
                  command=lambda: self.on_config_selected(tree, dialog))\
            .pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="编辑",
                  command=lambda: self.edit_config(tree, dialog))\
            .pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy)\
            .pack(side=tk.LEFT)
        
        tree.pack(fill=tk.BOTH, expand=True)
        btn_frame.pack(pady=5)

    def on_config_selected(self, tree, dialog):
        """处理配置选择"""
        selected = tree.selection()
        if selected:
            config_name = tree.item(selected[0], 'text')
            self.apply_config(config_name)
            dialog.destroy()

    def apply_config(self, config_name, update_stats=True):
        """应用配置到界面"""
        script_name = self.current_script_name
        config_data = self.saved_configs[script_name]['configs'][config_name]
        
        if update_stats:
            config_data['usage_count'] += 1
            config_data['last_used'] = datetime.now().isoformat()
            self.save_config_file()
        
        # 更新当前配置名称
        self.current_config_name = config_name
        
        # 填充参数
        for name, widget in self.input_widgets.items():
            value = config_data['params'].get(name, "")
            if isinstance(widget, ttk.Combobox):
                widget.set(value)
            else:
                widget.delete(0, tk.END)
                widget.insert(0, value)

    def edit_config(self, tree, dialog):
        """编辑配置"""
        selected = tree.selection()
        if not selected:
            return
        
        old_name = tree.item(selected[0], 'text')
        config_data = self.saved_configs[self.current_script_name]['configs'][old_name]
        
        edit_dialog = tk.Toplevel(self.root)
        edit_dialog.title("编辑配置")
        
        # 配置名称
        ttk.Label(edit_dialog, text="配置名称:").grid(row=0, column=0, padx=5, pady=2)
        name_entry = ttk.Entry(edit_dialog)
        name_entry.insert(0, old_name)
        name_entry.grid(row=0, column=1, padx=5, pady=2)
        
        # 参数编辑
        entries = {}
        for row, (param_name, param_value) in enumerate(config_data['params'].items(), start=1):
            ttk.Label(edit_dialog, text=f"{param_name}:").grid(row=row, column=0, padx=5, pady=2)
            entry = ttk.Entry(edit_dialog)
            entry.insert(0, param_value)
            entry.grid(row=row, column=1, padx=5, pady=2)
            entries[param_name] = entry
        
        # 保存按钮
        def save_changes():
            new_name = name_entry.get()
            new_params = {name: entry.get() for name, entry in entries.items()}
            
            # 更新配置
            del self.saved_configs[self.current_script_name]['configs'][old_name]
            self.saved_configs[self.current_script_name]['configs'][new_name] = {
                "params": new_params,
                "usage_count": config_data['usage_count'],
                "last_used": config_data['last_used']
            }
            
            self.save_config_file()
            edit_dialog.destroy()
            dialog.destroy()
            self.load_config_dialog()
        
        ttk.Button(edit_dialog, text="保存", command=save_changes)\
            .grid(row=row+1, columnspan=2, pady=5)

    def update_config_usage(self, config_name):
        """更新配置使用统计"""
        config = self.saved_configs[self.current_script_name]['configs'][config_name]
        config['usage_count'] += 1
        config['last_used'] = datetime.now().isoformat()
        self.save_config_file()

    def on_script_finished(self):
        """脚本执行完成处理"""
        if self.input_window and self.input_window.winfo_exists():
            self.input_window.destroy()
        self.current_script_thread = None

if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptRunnerApp(root)
    root.mainloop()