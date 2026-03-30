""" misc helper functions """

def parse_int(value: str) -> int:
    value = value.strip().lower()
    multipliers = {
        "k": 1_000,
        "m": 1_000_000,
        "b": 1_000_000_000,
    }
    if value[-1] in multipliers:
        return int(float(value[:-1]) * multipliers[value[-1]])
    return int(value)
