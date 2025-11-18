"""生成密码哈希的工具脚本"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.utils.auth import get_password_hash

if __name__ == "__main__":
    password = "admin123"
    hash_value = get_password_hash(password)
    print(f"密码: {password}")
    print(f"哈希值: {hash_value}")

