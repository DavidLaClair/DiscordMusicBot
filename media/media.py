class Media:
    def __init__(self, vendor:str, url: str=None, title: str=None, is_video: bool=False) -> None:
        self.vendor: str = vendor
        self.url: str = url
        self.title: str = title
        self.is_video: bool = is_video
