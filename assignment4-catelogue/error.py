def problem(status: int, title: str, detail: str, error_type: str = "about:blank"):
    return {
        "type": error_type,
        "title": title,
        "status": status,
        "detail": detail,
    }
