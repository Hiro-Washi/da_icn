import zenoh

if __name__ == "__main__":    
    config = zenoh.Config()
    session = zenoh.open(config)
    replies = session.get('myhome/kitchen/camera1/image')

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

