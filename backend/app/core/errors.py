class ServiceError(Exception):
    """Business-rule error raised by services; main.py turns it into a JSON response.

    Services stay free of HTTP details so the AI assistant can reuse them later.
    """

    status_code = 400

    def __init__(self, detail: str, headers: dict[str, str] | None = None):
        super().__init__(detail)
        self.detail = detail
        self.headers = headers or {}


class NotFoundError(ServiceError):
    status_code = 404


class StockError(ServiceError):
    status_code = 409


class TooManyAttempts(ServiceError):
    status_code = 429

    def __init__(self, retry_after: int):
        minutes = max(1, round(retry_after / 60))
        super().__init__(f"Too many attempts. Please wait about {minutes} minute(s) and try again.",
                         headers={"Retry-After": str(retry_after)})
