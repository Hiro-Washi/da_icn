import subprocess
import shlex

class CefCommandExecutor:
    """
    Cefore関連コマンドを実行するためのユーティリティクラス。
    """
    def run_command(self, command: List[str], requires_sudo: bool = False) -> str:
        """
        指定されたコマンドを実行し、その出力を返します。
        :param command: 実行するコマンドのリスト (例: ['cefroute', 'add', ...])
        :param requires_sudo: Trueの場合、sudoを付けてコマンドを実行します。
        :return: コマンドの標準出力
        :raises RuntimeError: コマンドの実行に失敗した場合
        """
        full_command = ["sudo"] + command if requires_sudo else command
        command_str = shlex.join(full_command) # ログ表示用に整形
        print(f"Executing command: {command_str}")
        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                check=True
            )
            if result.stderr:
                print(f"Command STDERR: {result.stderr.strip()}")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Command failed with exit code {e.returncode}:\n{e.stderr.strip()}") from e
        except FileNotFoundError:
            raise RuntimeError(f"Command not found: '{full_command[0]}'. Make sure Cefore is installed and in your PATH.")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred: {e}")
