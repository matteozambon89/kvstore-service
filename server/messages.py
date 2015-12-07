import sys

LOCAL_PUBLISH=1

def send(message, message_type=LOCAL_PUBLISH):
    if not message_type == LOCAL_PUBLISH:
        raise Exception("Unsupported message type")
    # messages go to stdout, the assumption is that normal messages
    # as opposed to error, logging, etc. go to stdout and the 
    # rest end up on stderr
    sys.stdout.write("%s\n" % message)
    sys.stdout.flush()
