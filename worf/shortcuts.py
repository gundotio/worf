from inspect import getframeinfo, stack


def get_debug(msg=""):
    caller = getframeinfo(stack()[1][0])
    return "{}:{} {}".format(caller.filename, caller.lineno, msg)
