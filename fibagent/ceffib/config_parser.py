from typing import List

class CefNetdConfigParser:
    """
    cefnetd.fibファイルを読み書きするためのパーサークラス。
    """
    def __init__(self, file_path: str):
        self.file_path = file_path

    def read_fib_entries(self) -> List[str]:
        """
        cefnetd.fibファイルからFIBエントリを読み込み、文字列のリストとして返します。
        コメント行や空行は無視されます。
        """
        entries = []
        try:
            with open(self.file_path, 'r') as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line and not stripped_line.startswith('#'):
                        entries.append(stripped_line)
        except FileNotFoundError:
            print(f"Warning: {self.file_path} not found. Starting with an empty FIB.")
        except Exception as e:
            print(f"Error reading {self.file_path}: {e}")
        return entries
