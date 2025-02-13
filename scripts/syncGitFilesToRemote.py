import os
import git
import paramiko
import argparse
from scp import SCPClient
import sys

# 配置
LOCAL_GIT_DIR = None  # 本地 Git 仓库路径
DELETE_PATH = None
REMOTE_SERVERS = None
REMOTE_PORT = 12288  # 默认 SSH 端口是 22
REMOTE_USER = None  # 远程服务器的 SSH 用户名
REMOTE_PASSWORD = None  # 远程服务器的 SSH 密码（也可以使用密钥）
REMOTE_BASE_DIR = None

# 创建 SSH 客户端
def create_ssh_client(server, port, user, password):
    try:
        # 创建一个SSH客户端实例
        ssh = paramiko.SSHClient()
        # 设置自动添加主机密钥策略
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 连接到SSH服务器
        ssh.connect(server, port, user, password)
        # 返回SSH客户端实例
        return ssh
    except Exception as e:
        # 打印连接错误信息
        print(f"Error connecting to {server}: {e}")
        # 返回None表示连接失败
        return None

# 使用 SCP 复制文件到远程服务器
def copy_files_to_remote(ssh_client, local_files):
    try:
        scp = SCPClient(ssh_client.get_transport())
        for local_file in local_files:
            # 计算相对于 LOCAL_GIT_DIR 的相对路径
            local_file_path = LOCAL_GIT_DIR + local_file
            local_file = local_file.replace(DELETE_PATH, '')
            remote_file_path = REMOTE_BASE_DIR + local_file
            
            # 确保远程路径的目录存在
            remote_dir = os.path.dirname(remote_file_path)
            ssh_client.exec_command(f"mkdir -p {remote_dir}")
            
            # 复制文件到远程路径
            print(f"【{local_file}】->【{remote_file_path}】")
            scp.put(local_file_path, remote_file_path)
        
        print("发送成功")
    except Exception as e:
        print(f"发送失败了TAT: {e}")

# 获取本地 Git 仓库中的修改文件
def get_modified_files():
    try:
        repo = git.Repo(LOCAL_GIT_DIR)
        modified_files = []
        # 获取所有未提交的修改
        for item in repo.git.status(porcelain=True).splitlines():
            status, path = item[:2].strip(), item[3:]
            if status in {"M", "A", "D", "R", "C", "??"}:  # M=Modified, A=Added, ??=Untracked
                modified_files.append(path)
        return modified_files
    except git.exc.InvalidGitRepositoryError as e:
        print(f"获取本地修改失败: {e}")
        return []

# 获取本地 Git 仓库中的所有文件
def get_all_files():    
    all_files = []
    for root, dirs, files in os.walk(LOCAL_GIT_DIR):
        print(files)
        for file in files:
            all_files.append(os.path.join(root, file))

    return all_files

def main(input_folder=None, delete_path=None,remote_server=None,prot=None,username=None,password=None,remote_folder=None):
    LOCAL_GIT_DIR = input_folder
    DELETE_PATH = delete_path
    REMOTE_SERVERS = remote_server.split(',')
    REMOTE_PORT = prot
    REMOTE_USER = username
    REMOTE_PASSWORD = password
    REMOTE_BASE_DIR = remote_folder
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="同步 Git 文件到远程设备")
    parser.add_argument(
        '--mode', choices=['full', 'modified'], default='modified',
        help="选择推送模式：'full' 推送所有文件，'modified' 仅推送修改过的文件"
    )
    args = parser.parse_args()

    # 根据选择的模式获取文件
    if args.mode == 'full':
        # 获取仓库中的所有文件
        files_to_copy = get_all_files()
        print("选择全量推送: 推送所有文件")
    else:
        # 获取修改过的文件
        files_to_copy = get_modified_files()
        print("选择仅推送修改过的文件")

    if not files_to_copy:
        print("没有要推送的文件.")
        return

    # 创建 SSH 客户端
    for server in REMOTE_SERVERS:
        print(f"正在连接到 {server}...")
        ssh_client = create_ssh_client(server, REMOTE_PORT, REMOTE_USER, REMOTE_PASSWORD)
        
        if ssh_client is None:
            print("无法连接到远程服务器.")
            return

        # 复制文件到远程设备
        copy_files_to_remote(ssh_client, files_to_copy)

        # 关闭 SSH 连接
        ssh_client.close()

if __name__ == "__main__":
    main()
