import os
import requests
import shutil
import openpyxl

def download_file(url, save_path):
    """
    下载文件到指定路径
    """
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            shutil.copyfileobj(response.raw, file)
        print(f"File downloaded: {save_path}")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")
        raise Exception("Download failed.")

def to_unicode(text):
    if not text:
        return ""
    return "".join(f"\\u{ord(char):04x}" for char in text)

def list_excel_files(directory):
    """
    列出当前目录中的所有 .xlsx 文件。
    """
    return [f for f in os.listdir(directory) if f.endswith('.xlsx')]

def process_excel_and_generate_txt(
    input_file,  # 输入的 .xlsx 文件路径
    output_file,  # 输出的 .txt 文件路径
    col1,  # 第一列的列名或索引 (如 'A' 或 1)
    col2,  # 第二列的列名或索引 (如 'B' 或 2)
    sheet_name,  # 选择的表名
    delimiter="-",  # 两列字符的连接符，默认是 "-"
    encoding="utf-8"
):
    try:
        # 加载 Excel 文件
        wb = openpyxl.load_workbook(input_file)
        sheet = wb[sheet_name]  # 根据用户选择的表加载

        # 处理列名为字母或索引的情况
        col1_idx = col1 if isinstance(col1, int) else openpyxl.utils.column_index_from_string(col1)
        col2_idx = col2 if isinstance(col2, int) else openpyxl.utils.column_index_from_string(col2)

        # 打开输出文件
        with open(output_file, "w", encoding="utf-8") as txt_file:
            for row in sheet.iter_rows(min_row=2):  # 从第2行开始，跳过表头
                value1 = row[col1_idx - 1].value  # 获取第 col1 列的值
                value2 = row[col2_idx - 1].value  # 获取第 col2 列的值

                # 如果有空值，用空字符串代替
                value1 = value1 if value1 is not None else ""
                value2 = value2 if value2 is not None else ""

                if encoding == "unicode":
                    value2 = to_unicode(str(value2))

                # 将两列的值通过连接符拼接
                combined = f'{value1}{delimiter}{value2}'

                if value1 == "":
                    return

                # 写入到输出文件
                txt_file.write(combined + "\n")

        print(f"生成完成！文件已保存到: {output_file}")

    except Exception as e:
        print(f"发生错误: {e}")


if __name__ == "__main__":
    # 获取当前目录路径
    current_dir = os.getcwd()

    # 列出当前目录中的所有 .xlsx 文件
    excel_files = list_excel_files(current_dir)

    if not excel_files:
        print("当前目录没有找到任何 .xlsx 文件！")
    else:
        print("找到以下 .xlsx 文件：")
        for i, file in enumerate(excel_files, start=1):
            print(f"{i}. {file}")

        # 让用户选择文件
        try:
            choice = int(input("请输入要处理的文件编号：")) - 1
            if choice < 0 or choice >= len(excel_files):
                print("无效选择！")
            else:
                selected_file = excel_files[choice]
                wb = openpyxl.load_workbook(selected_file)

                # 列出表名并让用户选择
                print("找到以下表：")
                sheet_names = wb.sheetnames
                for i, sheet_name in enumerate(sheet_names, start=1):
                    print(f"{i}. {sheet_name}")

                sheet_choice = int(input("请选择要处理的表编号：")) - 1
                if sheet_choice < 0 or sheet_choice >= len(sheet_names):
                    print("无效选择！")
                else:
                    selected_sheet = sheet_names[sheet_choice]

                    process_excel_and_generate_txt(
                        input_file=selected_file,  # 输入文件名
                        output_file="output-cn.txt",  # 输出文件名
                        col1="A",  # 第一列
                        col2="B",  # 第二列
                        sheet_name=selected_sheet,  # 用户选择的表名
                        delimiter=" = ",  # 连接符号
                        encoding="unicode"
                    )
                    process_excel_and_generate_txt(
                        input_file=selected_file,  # 输入文件名
                        output_file="output-en.txt",  # 输出文件名
                        col1="A",  # 第一列
                        col2="C",  # 第二列
                        sheet_name=selected_sheet,  # 用户选择的表名
                        delimiter=" = ",  # 连接符号
                    )
                    process_excel_and_generate_txt(
                        input_file=selected_file,  # 输入文件名
                        output_file="output-config.txt",  # 输出文件名
                        col1="A",  # 第一列
                        col2="B",  # 第二列
                        sheet_name=selected_sheet,  # 用户选择的表名
                        delimiter=" = ",  # 连接符号
                    )

        except ValueError:
            print("请输入有效的数字！")
