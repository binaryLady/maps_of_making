from typing import Optional

import httpx


class ErrorType:
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    CONNECTION_REFUSED = "connection_refused"
    DNS = "dns"
    CORS = "cors"
    SSL_CERT = "ssl_cert"
    HTTP_3XX = "http_3xx"
    HTTP_4XX = "http_4xx"
    HTTP_5XX = "http_5xx"
    NOT_MODIFIED = "not_modified"
    PARSE = "parse_error"
    SCHEMA_INVALID = "schema_invalid"
    EMPTY_RESPONSE = "empty_response"
    JSON_DECODE = "json_decode"
    VALIDATION = "validation_error"
    UNKNOWN = "unknown"


def categorize_error(
    exception: Optional[Exception],
    http_status: Optional[int],
    response_text: Optional[str],
) -> tuple[str, str]:
    """Map exception or HTTP status to (error_type, human_readable_message).

    Messages are safe for UI display — no stack traces or auth details.
    """
    if exception is not None:
        if isinstance(exception, httpx.TimeoutException):
            return ErrorType.TIMEOUT, "Endpoint did not respond within the timeout limit"
        if isinstance(exception, httpx.ConnectError):
            return ErrorType.CONNECTION_REFUSED, "Could not connect to endpoint"
        if isinstance(exception, httpx.NetworkError):
            if "name or service not known" in str(exception).lower():
                return ErrorType.DNS, "Domain name could not be resolved"
            return ErrorType.CONNECTION, "Network error connecting to endpoint"
        if isinstance(exception, httpx.SSLError):
            return ErrorType.SSL_CERT, "SSL certificate validation failed"
        if isinstance(exception, ValueError):
            if "json" in str(exception).lower():
                return ErrorType.JSON_DECODE, "Response is not valid JSON"
            return ErrorType.PARSE, "Response could not be parsed"
        if isinstance(exception, TypeError):
            return ErrorType.PARSE, "Response could not be parsed"
        return ErrorType.UNKNOWN, "Unexpected error fetching endpoint"

    if http_status is not None:
        if http_status == 304:
            return ErrorType.NOT_MODIFIED, "Content unchanged (304 Not Modified)"
        if 300 <= http_status < 400:
            return ErrorType.HTTP_3XX, f"Redirect not followed (HTTP {http_status})"
        if 400 <= http_status < 500:
            return ErrorType.HTTP_4XX, f"Endpoint returned HTTP {http_status}"
        if http_status >= 500:
            return ErrorType.HTTP_5XX, f"Endpoint server error (HTTP {http_status})"

    return ErrorType.UNKNOWN, "Unknown error"
