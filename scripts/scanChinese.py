import os
import re

def extract_chinese_text(directory):
    """
    Scan the specified directory and extract non-comment Chinese text from HTML, JS, VUE, and TS files.

    :param directory: The directory to scan.
    :return: A dictionary where keys are file paths and values are lists of Chinese text strings.
    """
    # File extensions to process
    file_extensions = ['.html', '.js', '.vue', '.ts']
    chinese_text_pattern = re.compile(r'[\u4e00-\u9fff]+')

    # Patterns for comments
    single_line_comment = re.compile(r'//.*')
    multi_line_comment = re.compile(r'/\*.*?\*/', re.DOTALL)
    html_comment = re.compile(r'<!--.*?-->', re.DOTALL)

    extracted_text = {}

    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in file_extensions):
                file_path = os.path.join(root, file)

                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Remove comments
                content = re.sub(html_comment, '', content)
                content = re.sub(multi_line_comment, '', content)
                content = re.sub(single_line_comment, '', content)

                # Extract Chinese text
                matches = chinese_text_pattern.findall(content)

                if matches:
                    extracted_text[file_path] = matches

    return extracted_text

def main(input_folder=None):
    result = extract_chinese_text(input_folder)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, 'extracted_chinese_text.md')

    with open(output_file, 'w', encoding='utf-8') as f:
        if not result:
            f.write("# Extracted Chinese Text\n\nNo Chinese text found in the specified directory.\n")
        else:
            f.write("# Extracted Chinese Text\n\n")
            for file_path, texts in result.items():
                f.write(f"## File: {file_path}\n")
                for text in texts:
                    f.write(f"- {text}\n")
                f.write("\n")

    print(f"Extraction completed. Results saved to {output_file}")

if __name__ == '__main__':
    main()
