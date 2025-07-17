import zenoh

if __name__ == "__main__":
    session = zenoh.open()
    replies = session.get('myhome/camera1/one/image')
    for reply in replies:
        try:
            print("Received ('{}': '{}')"
                .format(reply.ok.key_expr, reply.ok.payload.deserialize(str)))
        except:
            print("Received (ERROR: '{}')"
                .format(reply.err.payload.decode(str)))

    session.close()

# Traceback (most recent call last):
#  File "/home/pi/cefore/../da_icn/test/basic/zenoh/example/z_router_client.py", line 4, in <module>
#    session = zenoh.open()
#              ^^^^^^^^^^^^
#TypeError: open() missing 1 required positional argument: 'config'

