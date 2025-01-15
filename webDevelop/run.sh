#!/bin/bash

# 检查是否以 root 身份运行
if [ "$(id -u)" -ne 0 ]; then
    echo "请以 root 用户运行此脚本。"
    exit 1
fi

# 固定参数
USERNAME="web_develop"           # 固定用户名
SSH_KEY_FILE="./id_rsa"   # 固定公钥路径
OPTION1="/opt/lsblj/tomcat/webapps/ROOT/"        # 第一个固定目录
OPTION2="/opt/lsblj/sbin/sg_web/"        # 第二个固定目录

# 检查公钥文件是否存在
if [ ! -f "$SSH_KEY_FILE" ]; then
    echo "公钥文件不存在: $SSH_KEY_FILE"
    exit 1
fi

# 提供目录选项给用户
echo "请选择需要限制的目录:"
echo "1) $OPTION1"
echo "2) $OPTION2"
read -p "请输入 1 或 2: " CHOICE

# 根据选择设置目录
case $CHOICE in
    1)
        USER_DIR="$OPTION1"
        ;;
    2)
        USER_DIR="$OPTION2"
        ;;
    *)
        echo "无效选择，请输入 1 或 2。"
        exit 1
        ;;
esac

# 检查目录是否存在
if [ ! -d "$USER_DIR" ]; then
    echo "目录不存在: $USER_DIR"
    exit 1
fi

# 创建用户（如果用户已存在则跳过创建）
if id "$USERNAME" &>/dev/null; then
    echo "用户 $USERNAME 已存在，跳过创建。"
else
    useradd -m -s /bin/bash "$USERNAME"
    echo "用户 $USERNAME 已创建。"
fi

# 确保指定目录权限正确
chown root:root "$USER_DIR"  # 必须由 root 拥有
chmod 755 "$USER_DIR"
echo "目录 $USER_DIR 的权限已设置为 root:root，模式 755。"

# 配置 SSH
SSH_DIR="/home/$USERNAME/.ssh"
mkdir -p "$SSH_DIR"
cat "$SSH_KEY_FILE" > "$SSH_DIR/authorized_keys"
chown -R "$USERNAME:$USERNAME" "$SSH_DIR"
chmod 700 "$SSH_DIR"
chmod 600 "$SSH_DIR/authorized_keys"
echo "SSH 公钥已配置。"

# 更新 SSH 配置，限制用户权限
echo "Match User $USERNAME" >> /etc/ssh/sshd_config
echo "    ChrootDirectory $USER_DIR" >> /etc/ssh/sshd_config
echo "    ForceCommand internal-sftp" >> /etc/ssh/sshd_config
echo "    AllowTcpForwarding no" >> /etc/ssh/sshd_config
echo "    X11Forwarding no" >> /etc/ssh/sshd_config
echo "SSH 配置已更新。"

# 重启 SSH 服务
systemctl restart sshd
if [ $? -eq 0 ]; then
    echo "SSH 服务已重启。"
else
    echo "SSH 服务重启失败，请检查配置。"
    exit 1
fi

echo "用户 $USERNAME 已成功配置！"
echo "只能访问目录 $USER_DIR，并通过 SSH 使用公钥登录。"
