import os
import subprocess


class CommandExecutor:
    def __init__(self):
        self.work_dir = os.getcwd()  # 跟踪当前工作目录
    
    def run(self, command: str) -> str:
        """在指定目录执行命令"""
        try:
            print(f"执行命令: {command}") 

            output = subprocess.check_output(
                command,
                shell=True,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=3000,
                cwd=self.work_dir  # 关键：指定工作目录
            )
            print(f"命令执行结果: {output}")
            # output不能超过1000个字符
            result = output.strip()
            if len(result) > 200:
                result = result[:200]
            return result
        except subprocess.CalledProcessError as e:
            return f"[ERROR {e.returncode}]: {e.output.strip()}"
        except Exception as e:
            return f"[SYSTEM ERROR]: {str(e)}"
    
    def change_dir(self, path: str) -> str:
        """切换工作目录"""
        try:
            new_path = os.path.abspath(os.path.join(self.work_dir, path))
            if os.path.isdir(new_path):
                self.work_dir = new_path

                print(f"切换目录到: {new_path}")

                return f"Working directory changed to: {new_path}"
            return f"[ERROR] Directory not found: {new_path}"
        except Exception as e:
            return f"[ERROR] {str(e)}"