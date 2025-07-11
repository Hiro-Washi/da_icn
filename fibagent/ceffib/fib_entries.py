from typing import Dict, List, Any

# 静的FIBエントリの定義
STATIC_FIB_ENTRIES: List[Dict[str, Any]] = [
    {
        "name": "ccnx:/test/video/demo",
        "protocol": "udp",
        "next_hops": ["172.18.0.21", "172.18.0.31", "172.18.0.32"]
    },
    {
        "name": "ccnx:/my/data",
        "protocol": "udp",
        "next_hops": ["172.18.0.22"]
    }
]

# 動的FIBエントリの定義
DYNAMIC_FIB_ENTRIES: List[Dict[str, Any]] = [
    {
        "name": "ccnx:/dynamic/route",
        "protocol": "udp",
        "next_hops": ["172.18.0.23", "172.18.0.33"]
    }
]

# 隣接ノードのIPアドレスを管理する辞書 (手動設定)
# これは、自動取得が難しい場合のフォールバックとして利用されます。
KNOWN_NEIGHBOR_IPS: Dict[str, List[str]] = {
    "producer_node": ["172.18.0.21", "172.18.0.22", "172.18.0.23"],
    "consumer_node": ["172.18.0.31", "172.18.0.32", "172.18.0.33"],
    # ... 他の隣接ノードのIPアドレス
}

# FIBエントリ生成のヘルパー関数（オプション）
def generate_fib_entry(uri_prefix: str, producer_ip: str, consumer_ips: List[str]) -> Dict[str, Any]:
    """
    URIプレフィックス、プロデューサIP、コンシューマIPリストからFIBエントリを生成します。
    """
    return {
        "name": uri_prefix,
        "protocol": "udp",
        "next_hops": [producer_ip] + consumer_ips
    }
