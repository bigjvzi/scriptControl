import os
import re
from bs4 import BeautifulSoup
from bs4 import Comment  # 修正注释检测

# 读取配置文件，格式为 key=value
def load_config(config_file_path):
    config = {}
    with open(config_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)  # 分割为键和值
                config[key.strip()] = value.strip()  # 存入字典
    return config

# 读取 HTML 文件
def read_html_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# 替换 HTML 内容并添加 data-i18n-text 属性，仅处理 <body> 标签内的元素
def replace_text_in_html(html_content, config, unmatched_texts, file_name):
    soup = BeautifulSoup(html_content, 'lxml')

    # 正则表达式匹配中文字符
    chinese_char_pattern = re.compile(r'[\u4e00-\u9fa5]+')

    # 遍历 <body> 标签内的所有文本节点
    for element in soup.find_all(string=True):  # 使用 string 遍历所有文本节点

        if element.parent.name in {"script", "style"}:
            continue  # 忽略 <script> 和 <style> 中的内容
        if isinstance(element, Comment):
            continue  # 忽略注释

        text = element.strip().replace("&nbsp", "").replace("&nbsp;", "").replace(" ", "")  # 删除空格和&nbsp;
        if text:
            match = chinese_char_pattern.search(text)  # 检查是否有中文字符
            if match:
                replaced = False
                # 检查是否以中英文冒号结尾
                is_colon_ended = text.endswith(':') or text.endswith('：')
                # 如果以冒号结尾，仅匹配冒号之前的部分
                compare_text = text[:-1] if is_colon_ended else text

                for key, value in config.items():
                    if value == compare_text:
                        # 替换文本：移除标签中的中文，保留替换内容并添加属性
                        parent = element.parent
                        if parent is not None and parent.name != '[document]':
                            # 替换为新内容，保留冒号（如果有）
                            new_text = text.replace(value, "")
                            parent['data-i18n-text'] = key
                            element.replace_with(new_text)  # 更新文本节点
                        replaced = True
                if not replaced:  # 如果没有匹配到替换规则，则记录未匹配中文
                    unmatched_texts[file_name].add(text)
    
    # 替换 placeholder 属性的中文内容
    for element in soup.find_all(attrs={"placeholder": True}):  # 查找带有 placeholder 属性的标签
        placeholder = element['placeholder']
        if chinese_char_pattern.search(placeholder):  # 检查 placeholder 是否包含中文
            replaced = False
            for key, value in config.items():
                if value == placeholder:
                    element['data-i18n-placeholder'] = key  # 添加 data-i18n-placeholder 属性
                    element['placeholder'] = ""  # 替换 placeholder 文本
                    replaced = True
            if not replaced:  # 如果未匹配到，记录未匹配的 placeholder 中文
                unmatched_texts[file_name].add(placeholder)

    for tag in soup.find_all(True):
        for attr in ["selected", "checked", "disabled", "readonly", "multiple", "stoprepeatedclick"]:
            if attr in tag.attrs and tag.attrs[attr] == "":
                tag.attrs[attr] = None  # 移除值以保留布尔属性原样
                
    return soup.decode(formatter=None)

# 递归获取目录下所有的 .html 文件
def get_html_files_from_directory(dir_path):
    html_files = []
    for root, _, files in os.walk(dir_path):  # 遍历目录
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))
    return html_files

# 输出未匹配的文字到 Markdown 文件
def write_unmatched_to_markdown(unmatched_texts, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 未匹配中文字符\n\n")
        for file_name, texts in unmatched_texts.items():
            if texts:
                f.write(f"## 文件: {file_name}\n\n")
                for text in texts:
                    f.write(f"- {text}\n")
                f.write("\n")

# 主函数
def main():
    config_file_path = 'output-cn-utf8.txt'  # 配置文件路径
    html_files = get_html_files_from_directory('.\html')  # 获取当前目录及子目录中的所有 .html 文件

    # 加载配置文件
    config = load_config(config_file_path)

    # 创建输出目录
    if not os.path.exists('updated'):
        os.makedirs('updated')

    # 创建字典存储未匹配的中文文本，按文件分类
    unmatched_texts = {}

    # 处理每个 HTML 文件
    for html_file in html_files:
        print(f"正在处理文件: {html_file}")
        
        # 读取原始 HTML 内容
        html_content = read_html_file(html_file)

        # 初始化当前文件的未匹配集合
        file_name = os.path.basename(html_file)
        unmatched_texts[file_name] = set()

        # 替换文本并添加 data-i18n-text 属性，仅处理 <body> 内的内容
        updated_html = replace_text_in_html(html_content, config, unmatched_texts, file_name)

        # 保存更新后的文件到 updated 目录
        relative_path = os.path.relpath(html_file, start='.')
        output_file_path = os.path.join('updated', relative_path)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        # 写入更新后的 HTML 内容
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(updated_html)

        print(f"已保存更新后的文件: {output_file_path}")

    # 将未匹配字符输出到 Markdown 文件
    unmatched_md_path = 'unmatched.md'
    write_unmatched_to_markdown(unmatched_texts, unmatched_md_path)
    print(f"未匹配的中文字符已保存到: {unmatched_md_path}")

    print("\n处理完成。")

if __name__ == '__main__':
    main()
