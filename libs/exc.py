from requests import Response


class HTTPStatusException(Exception):
    def __init__(self, status, message="", url=None, resp: Response = None):
        self.status = status
        self.message = 'HTTP Status: {} - {}'.format(status, message)
        self.url = url
        self.response = resp
        super().__init__(self.message)


class InvalidCookieException(Exception):
    def __init__(self, resource_id, message="", url=None):
        self.message = 'Invalid Cookie: {} - {}'.format(resource_id, message)
        self.url = url
        super().__init__(self.message)


class NoAvailableResourceException(Exception):
    def __init__(self, social_media, allowed_usage, message=""):
        self.message = 'No Available Resource: {} - {}'.format(
            social_media, allowed_usage)
        super().__init__(self.message)


class InstagramError(Exception):
    def __init__(self, code, message="", url=None, resp: Response = None):
        self.code = code
        self.message = message
        self.url = url
        self.response = resp
        super().__init__(self.message)


class TwitterGuestTokenError(Exception):
    def __init__(self):
        self.message = 'Error Generate Guest Token'
        super().__init__(self.message)


class FacebookError(Exception):
    def __init__(self, code, message="", url=None, subcode=None, type=None, fbtrace_id=None):
        self.code = code
        self.message = message
        self.url = url
        self.subcode = subcode
        self.type = type
        self.fbtrace_id = fbtrace_id
        super().__init__(self.message)


class TwitterFormatError(Exception):
    def __init__(self, message="Format Changed"):
        self.message = message
        super().__init__(self.message)


class YoutubeError(Exception):
    def __init__(self, code=None, message="", resp: Response = None):
        self.message = message
        self.response = resp
        self.code = code
        super().__init__(self.message)


class CaptchaError(Exception):
    def __init__(self,  resp: Response):
        self.resp = resp
        super().__init__(self.resp.url)


class UnknownLayoutError(Exception):
    def __init__(self,  layout_name):
        self.layout_name = layout_name
        super().__init__(self.layout_name)


class InstagramExecutionError(Exception):
    def __init__(self,  message="", detail=None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class GoogleMapsError(Exception):
    def __init__(self, message=""):
        self.message = message
        super().__init__(self.message)


class TiktokError(Exception):
    def __init__(self, status_code, message=""):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class TiktokCaptchaError(Exception):
    def __init__(self, message="Tiktok Captcha Error"):
        self.message = message
        super().__init__(self.message)
