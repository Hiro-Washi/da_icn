import os
from typing import List, Dict, Union
from .cef_command_executor import CefCommandExecutor
from .config_parser import CefNetdConfigParser

class FibManager:
    """
    Cefore FIB (Forwarding Information Base) の管理を行うクラス。
    静的FIBファイルと動的FIBコマンドの両方を扱います。
    """

    CEFNETD_FIB_PATH = "/etc/cefnetd/cefnetd.fib" # デフォルトのcefnetd.fibパス

    def __init__(self, cefnetd_fib_path: str = None):
        """
        FibManagerの初期化。
        :param cefnetd_fib_path: cefnetd.fibファイルのパス。Noneの場合はデフォルトパスを使用。
        """
        self.cefnetd_fib_path = cefnetd_fib_path if cefnetd_fib_path else self.CEFNETD_FIB_PATH
        self.command_executor = CefCommandExecutor()
        self.config_parser = CefNetdConfigParser(self.cefnetd_fib_path)

    def _format_fib_entry(self, name: str, protocol: str, next_hops: List[str]) -> str:
        """
        FIBエントリを行形式でフォーマットする内部メソッド。
        """
        return f"{name} {protocol} {' '.join(next_hops)}"

    def add_static_fib_entry(self, name: str, protocol: str, next_hops: List[str]):
        """
        静的FIBエントリをcefnetd.fibファイルに追加します。
        すでに存在する場合は追加しません。
        :param name: URI名 (例: ccnx:/test/video/demo)
        :param protocol: プロトコル (例: udp)
        :param next_hops: ネクストホップのIPアドレスリスト (例: ['172.18.0.21', '172.18.0.31'])
        """
        entry_line = self._format_fib_entry(name, protocol, next_hops)
        print(f"Attempting to add static FIB entry: {entry_line}")

        existing_entries = self.config_parser.read_fib_entries()
        if entry_line in existing_entries:
            print(f"Static FIB entry already exists: {entry_line}")
            return

        try:
            with open(self.cefnetd_fib_path, 'a') as f:
                f.write(entry_line + '\n')
            print(f"Successfully added static FIB entry to {self.cefnetd_fib_path}: {entry_line}")
        except PermissionError:
            print(f"Permission denied: Cannot write to {self.cefnetd_fib_path}. Run with sudo if necessary.")
        except IOError as e:
            print(f"Error writing to {self.cefnetd_fib_path}: {e}")

    def remove_static_fib_entry(self, name: str, protocol: str, next_hops: List[str]):
        """
        静的FIBエントリをcefnetd.fibファイルから削除します。
        :param name: URI名
        :param protocol: プロトコル
        :param next_hops: ネクストホップのIPアドレスリスト
        """
        entry_to_remove = self._format_fib_entry(name, protocol, next_hops)
        print(f"Attempting to remove static FIB entry: {entry_to_remove}")

        existing_entries = self.config_parser.read_fib_entries()
        if entry_to_remove not in existing_entries:
            print(f"Static FIB entry not found: {entry_to_remove}")
            return

        try:
            remaining_entries = [e for e in existing_entries if e != entry_to_remove]
            with open(self.cefnetd_fib_path, 'w') as f:
                for entry in remaining_entries:
                    f.write(entry + '\n')
            print(f"Successfully removed static FIB entry from {self.cefnetd_fib_path}: {entry_to_remove}")
        except PermissionError:
            print(f"Permission denied: Cannot write to {self.cefnetd_fib_path}. Run with sudo if necessary.")
        except IOError as e:
            print(f"Error writing to {self.cefnetd_fib_path}: {e}")

    def add_dynamic_fib_entry(self, name: str, protocol: str, next_hops: List[str]):
        """
        動的FIBエントリをcefrouteコマンドで追加します。
        この操作にはsudo権限が必要です。
        :param name: URI名
        :param protocol: プロトコル
        :param next_hops: ネクストホップのIPアドレスリスト
        """
        command = ["cefroute", "add", name, protocol] + next_hops
        print(f"Attempting to add dynamic FIB entry: {' '.join(command)}")
        try:
            self.command_executor.run_command(command, requires_sudo=True)
            print(f"Successfully added dynamic FIB entry: {name}")
        except Exception as e:
            print(f"Error adding dynamic FIB entry: {e}")

    def remove_dynamic_fib_entry(self, name: str, protocol: str, next_hops: List[str]):
        """
        動的FIBエントリをcefrouteコマンドで削除します。
        この操作にはsudo権限が必要です。
        :param name: URI名
        :param protocol: プロトコル
        :param next_hops: ネクストホップのIPアドレスリスト
        """
        command = ["cefroute", "del", name, protocol] + next_hops
        print(f"Attempting to remove dynamic FIB entry: {' '.join(command)}")
        try:
            self.command_executor.run_command(command, requires_sudo=True)
            print(f"Successfully removed dynamic FIB entry: {name}")
        except Exception as e:
            print(f"Error removing dynamic FIB entry: {e}")

    def list_fib_entries(self):
        """
        現在のFIBエントリを表示します (cefroute show)。
        この操作にはsudo権限が必要な場合があります。
        """
        command = ["cefroute", "show"]
        print(f"Listing FIB entries: {' '.join(command)}")
        try:
            output = self.command_executor.run_command(command, requires_sudo=False) # showはsudo不要な場合が多い
            print("Current FIB Entries:")
            print(output)
        except Exception as e:
            print(f"Error listing FIB entries: {e}")
