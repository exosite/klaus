AUTH_MAP = {}

class BaseAuthCache(object):
    def __init__(self):
        pass

    def can_view(self, repo):
        return True


class FailAllCache(BaseAuthCache):
    def __init__(self):
        pass

    def can_view(self, repo):
        return False


class BaseAuth(object):
    def get_cache(self, request):
        return BaseAuthCache()

    def current_user(self, request):
        return 'CURRENT USER'


def register_authorizer(authname, func):
    AUTH_MAP[authname] = func
    print "Registered authorizer: {0}".format(authname)

def make_authorizer(authname):
    if authname in AUTH_MAP:
        return AUTH_MAP[authname]()
    valid_authnames = ','.join(AUTH_MAP.keys())
    error_message = "{0} is not a valid authorizer name.  Options: {1}".format(authname, valid_authnames)
    raise ValueError(error_message)
