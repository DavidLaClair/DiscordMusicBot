class Request:
    def __init__(self, media, member, channel):
        self.vendor = None
        self.url = None
        self.title = None

        self.media = media
        self.member = member
        self.channel = channel

        self.get_vendor()
        self.get_url()
        self.get_title()

    def get_vendor(self):
        url = self.media.url

        if "youtube" in url:
            self.vendor = "youtube"

        if "spotify" in url:
            self.vendor = "spotify"

        return self.vendor

    def get_url(self):
        if self.vendor == "youtube":
            self.url = self.media.url

    def get_title(self):
        if self.vendor == "youtube":
            self.title = self.media.info["title"]
