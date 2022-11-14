class Request:
    def __init__(self, vendor, url, member, channel, info=None):
        self.vendor = vendor
        self.url = url
        self.info = info
        self.member = member
        self.channel = channel
