import fastjsonschema
from .schema import REDCAP_SCHEMA

_validate_func = fastjsonschema.compile(REDCAP_SCHEMA)

def validate_candidate(candidate: dict) -> bool:
    try:
        _validate_func(candidate)
        return True
    except Exception:
        return False