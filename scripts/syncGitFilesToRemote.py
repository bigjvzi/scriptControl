import os
import git
import paramiko
import argparse
from scp import SCPClient

# 配置
LOCAL_GIT_DIR = 'D:/safe/blj_web/BLJ/src/main/webapp/'  # 本地 Git 仓库路径
REMOTE_PORT = 22  # 默认 SSH 端口是 22
REMOTE_USER = 'root'  # 远程服务器的 SSH 用户名
REMOTE_PASSWORD = 'admin@123'  # 远程服务器的 SSH 密码（也可以使用密钥）
REMOTE_BASE_DIR = '/opt/lsblj/tomcat/webapps/ROOT/'  # 远程机器上需要存放文件的目录

# 创建 SSH 客户端
def create_ssh_client(server, port, user, password):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, port, user, password)
        return ssh
    except Exception as e:
        print(f"Error connecting to {server}: {e}")
        return None

# 使用 SCP 复制文件到远程服务器
def copy_files_to_remote(ssh_client, local_files):
    try:
        scp = SCPClient(ssh_client.get_transport())
        for local_file in local_files:
            # 计算相对于 LOCAL_GIT_DIR 的相对路径
            local_file_path = LOCAL_GIT_DIR + local_file
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
        for item in repo.index.diff(None):
            modified_files.append(item.a_path)  # 获取修改文件的相对路径
        return modified_files
    except git.exc.InvalidGitRepositoryError as e:
        print(f"获取本地修改失败: {e}")
        return []

# 获取本地 Git 仓库中的所有文件
def get_all_files():
    all_files = []
    for root, dirs, files in os.walk(LOCAL_GIT_DIR):
        for file in files:
            all_files.append(os.path.join(root, file))
    return all_files

def main():
    # servers = ["192.168.1.159", "192.168.1.160", "192.168.1.161"]
    servers = ["192.168.1.222"]
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
    for server in servers:
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
