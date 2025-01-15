import os
import json
import subprocess
import streamlit as st
from pathlib import Path

# 配置存储路径
SCRIPT_FOLDER = "./scripts"  # 请替换为你的脚本目录
SCRIPT_CONFIGS = "./script_configs.json"  # 脚本配置
HISTORY_FILE = "./path_history.json"  # 用于存储文件路径历史记录

# 加载路径历史记录
def load_path_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# 保存路径历史记录
def save_path_history(paths):
    with open(HISTORY_FILE, "w") as f:
        json.dump(paths, f)

# 列出指定目录下的文件
def list_files(directory):
    if os.path.isdir(directory):
        return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    return []

# 执行脚本并获取输出
def run_script(script_path, params):
    param_list = [f"--{key}={value}" for key, value in params.items()]
    result = subprocess.run(
        ['python', script_path] + param_list,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode == 0:
        return result.stdout
    else:
        return f"错误：{result.stderr}"

# 加载脚本列表
def list_scripts(script_folder):
    return [f for f in os.listdir(script_folder) if f.endswith('.py')]

# 主页面
def main():
    st.title("脚本管理页面")

    # 创建左右两列
    left_col, right_col = st.columns([1, 2])  # 左侧占 1/3，右侧占 2/3

    # 左侧：脚本选择和运行
    with left_col:
        st.header("脚本选择与运行")

        # 列出脚本
        scripts = list_scripts(SCRIPT_FOLDER)
        if not scripts:
            st.warning("脚本目录中没有可用的 Python 脚本。")
            return

        selected_script = st.selectbox("选择脚本", scripts)
        script_path = os.path.join(SCRIPT_FOLDER, selected_script)

        # 脚本运行
        if st.button("运行脚本"):
            st.session_state['running_script'] = selected_script

    # 右侧：具体配置和输出
    with right_col:
        st.header(f"脚本配置: {st.session_state.get('running_script', '未选择')}")
        
        # 加载历史路径
        path_history = load_path_history()
        st.subheader("文件路径选择")
        selected_path = st.selectbox("历史路径", options=path_history, index=0 if path_history else -1)
        custom_path = st.text_input("自定义路径", "")
        final_path = custom_path if custom_path else selected_path

        # 路径确认
        if st.button("确认路径"):
            if os.path.isdir(final_path):
                if final_path not in path_history:
                    path_history.append(final_path)
                    save_path_history(path_history)
                st.success(f"路径已确认：{final_path}")
            else:
                st.error(f"无效路径：{final_path}")

        if 'running_script' in st.session_state:
            running_script = st.session_state['running_script']
            running_script_path = os.path.join(SCRIPT_FOLDER, running_script)

            # 假设每个脚本都支持动态配置
            st.subheader("配置参数")
            param1 = st.text_input("参数 1", "默认值 1")
            param2 = st.number_input("参数 2", value=10, min_value=0, max_value=100)
            params = {"param1": param1, "param2": param2}

            # 脚本运行和输出展示
            if st.button("确认并运行"):
                output = run_script(running_script_path, params)
                st.subheader("执行结果")
                st.text(output)

                # 判断是否需要二次输入
                if "需要二次输入" in output:
                    st.subheader("二次输入")
                    secondary_input = st.text_input("二次参数")
                    if st.button("提交二次输入"):
                        params["param3"] = secondary_input
                        secondary_output = run_script(running_script_path, params)
                        st.text(secondary_output)

if __name__ == "__main__":
    main()
