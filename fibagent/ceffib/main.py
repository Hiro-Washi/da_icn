import sys
from cef_fib_manager.fib_manager import FibManager
from cef_fib_manager.fib_entries import STATIC_FIB_ENTRIES, DYNAMIC_FIB_ENTRIES, KNOWN_NEIGHBOR_IPS, generate_fib_entry

def apply_static_fib_entries(fib_manager: FibManager):
    """
    定義済みの静的FIBエントリを適用します。
    """
    print("\n--- Applying Static FIB Entries ---")
    for entry in STATIC_FIB_ENTRIES:
        fib_manager.add_static_fib_entry(
            entry["name"],
            entry["protocol"],
            entry["next_hops"]
        )

def remove_static_fib_entries(fib_manager: FibManager):
    """
    定義済みの静的FIBエントリを削除します。
    """
    print("\n--- Removing Static FIB Entries ---")
    for entry in STATIC_FIB_ENTRIES:
        fib_manager.remove_static_fib_entry(
            entry["name"],
            entry["protocol"],
            entry["next_hops"]
        )

def apply_dynamic_fib_entries(fib_manager: FibManager):
    """
    定義済みの動的FIBエントリを適用します。
    """
    print("\n--- Applying Dynamic FIB Entries ---")
    for entry in DYNAMIC_FIB_ENTRIES:
        fib_manager.add_dynamic_fib_entry(
            entry["name"],
            entry["protocol"],
            entry["next_hops"]
        )

def remove_dynamic_fib_entries(fib_manager: FibManager):
    """
    定義済みの動的FIBエントリを削除します。
    """
    print("\n--- Removing Dynamic FIB Entries ---")
    for entry in DYNAMIC_FIB_ENTRIES:
        fib_manager.remove_dynamic_fib_entry(
            entry["name"],
            entry["protocol"],
            entry["next_hops"]
        )

def main():
    fib_manager = FibManager() # デフォルトのcefnetd.fibパスを使用

    # 隣接ノードIPを基にしたFIBエントリの例
    # ここではKNOWN_NEIGHBOR_IPSから取得していますが、
    # 自動取得できた場合はその結果を使用します。
    producer_ip = KNOWN_NEIGHBOR_IPS["producer_node"][0] # 例として1つ目のIPを使用
    consumer_ips = KNOWN_NEIGHBOR_IPS["consumer_node"]

    # 例として、新しいURI名に対するFIBエントリを生成・追加
    new_uri_fib_entry = generate_fib_entry(
        "ccnx:/my/new/service",
        producer_ip,
        consumer_ips
    )
    # apply_dynamic_fib_entryを使用すると、実行時に即座に反映される
    fib_manager.add_dynamic_fib_entry(
        new_uri_fib_entry["name"],
        new_uri_fib_entry["protocol"],
        new_uri_fib_entry["next_hops"]
    )

    # 静的FIBエントリの適用/削除 (必要に応じてコメントアウトを切り替える)
    apply_static_fib_entries(fib_manager)
    # remove_static_fib_entries(fib_manager)

    # 動的FIBエントリの適用/削除 (必要に応じてコメントアウトを切り替える)
    apply_dynamic_fib_entries(fib_manager)
    # remove_dynamic_fib_entries(fib_manager)

    # 現在のFIBエントリの表示
    fib_manager.list_fib_entries()

if __name__ == "__main__":
    # スクリプトを直接実行する場合、sudo権限が必要な操作があるため、
    # Pythonスクリプト自体をsudoで実行することを推奨します。
    # 例: sudo python3 main.py
    main()
