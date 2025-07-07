"""
构建和上传包到PyPI的脚本
"""

import os
import shutil
import subprocess
import sys


def run_command(cmd, cwd=None):
    """运行命令"""
    print(f"运行命令: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"命令执行失败: {result.stderr}")
        sys.exit(1)
    return result.stdout


def main():
    """主函数"""
    # 清理旧的构建文件
    for dir_name in ["build", "dist", "*.egg-info"]:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name, ignore_errors=True)

    # 构建包
    print("构建包...")
    run_command("python setup.py sdist bdist_wheel")

    # 检查包
    print("检查包...")
    run_command("twine check dist/*")

    # 上传到测试PyPI（可选）
    upload_to_test = input("是否上传到测试PyPI? (y/N): ").lower() == 'y'
    if upload_to_test:
        print("上传到测试PyPI...")
        run_command("twine upload --repository certbot-dns-aliyun-next dist/*")
        print("测试安装:")
        print("pip install --index-url https://test.pypi.org/simple/ certbot-dns-aliyun-next")

        continue_to_prod = input("是否继续上传到正式PyPI? (y/N): ").lower() == 'y'
        if not continue_to_prod:
            return

    # 上传到正式PyPI
    confirm = input("确认上传到正式PyPI? (y/N): ").lower() == 'y'
    if confirm:
        print("上传到正式PyPI...")
        run_command("twine upload dist/*")
        print("上传完成!")
    else:
        print("取消上传")


if __name__ == "__main__":
    main()
