async def get_group_title(id: int) -> str:
    result = "LATER"

    if id == 0:
        result = "TODAY"
    elif id == 1:
        result = "LAST_WEEK"
    elif id == 2:
        result = "LAST_MONTH"
    elif id == 3:
        result = "LATER"

    return result
