import zenoh

if __name__ == "__main__":
    # 設定ファイルから読み込む方法（オプション）
    # config = zenoh.Config.from_file("my_config.json5")
    # カスタム設定を追加
    #config.insert_json5("mode", '"client"')  # 動作モード（client, peer, router）
    #config.insert_json5("connect/endpoints", '["tcp/192.168.1.100:7447"]')  # 接続先のエンドポイント(IPとポート)
    # "listen/endpoints"	自分が待ち受けるエンドポイント	["tcp/0.0.0.0:7447"]
    # "scouting/multicast/enabled"	マルチキャスト探索の有効化	true または false
    # "plugins"	プラグインの有効化	{"plugin_name": true}

    config = zenoh.Config()
    session = zenoh.open(config)
    replies = session.get('myhome/kitchen/camera1/image')

    for reply in replies:
        try:
            print("Received ('{}': '{}')"
                .format(reply.ok.key_expr, reply.ok.payload.decode("utf-8")))
                #.format(reply.ok.key_expr, reply.ok.payload.deserialize(str))) <- :(
        except Exception as e:
            if reply.err is not None:
                try:
                    error_bytes = bytes(reply.err.payload).decode("utf-8")
                    #error_text = error_bytes.decode("utf-8")
                    print("Received (ERROR1: '{error_bytes}')")
                except Exception as inner_e:
                    print(f"Received (ERROR2: Failed to decode payload: {inner_e}")
            else:
                print(f"Received (ERROR3: {e})")

    session.close()

# Traceback (most recent call last):
#  File "/home/pi/cefore/../da_icn/test/basic/zenoh/example/z_router_client.py", line 4, in <module>
#    session = zenoh.open()
#              ^^^^^^^^^^^^
#TypeError: open() missing 1 required positional argument: 'config'

# Traceback (most recent call last):
#  File "/home/pi/cefore/../da_icn/test/basic/zenoh/example/z_router_client.py", line 11, in <module>
#    .format(reply.ok.key_expr, reply.ok.payload.deserialize(str)))
#                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#AttributeError: 'builtins.ZBytes' object has no attribute 'deserialize'
#
#During handling of the above exception, another exception occurred:
#
#Traceback (most recent call last):
#  File "/home/pi/cefore/../da_icn/test/basic/zenoh/example/z_router_client.py", line 14, in <module>
#    .format(reply.err.payload.decode(str)))
#            ^^^^^^^^^^^^^^^^^
#AttributeError: 'NoneType' object has no attribute 'payload'
#
# -> 原因1：reply.ok.payload は ZBytes 型であり、deserialize() メソッドを持っていません。代わりに、decode() メソッドを使って文字列に変換する必要があります。
# 原因：reply.err が None の場合に reply.err.payload にアクセスしようとしているためです。これは、reply が ok である場合に err が存在しないためです。
# エラーハンドリングの部分を、reply.err が存在するかどうかを確認してから処理するようにします

