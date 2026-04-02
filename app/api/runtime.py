_db_initialized = False


def is_db_initialized() -> bool:
    return _db_initialized


def mark_db_initialized() -> None:
    global _db_initialized
    _db_initialized = True
