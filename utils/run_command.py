import subprocess

def run_command(command: str) -> str:
    """执行系统命令并返回输出结果（跨平台）"""
    try:
        # 使用 check_output 捕获标准输出
        output = subprocess.check_output(
            command,
            shell=True,          # 支持复杂命令
            stderr=subprocess.STDOUT,  # 合并错误输出
            universal_newlines=True,   # 返回字符串而非字节
            timeout=60       # 防止长时间阻塞
        )
        return output.strip()
    except subprocess.CalledProcessError as e:
        return f"Command failed (code {e.returncode}): {e.output.strip()}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds"