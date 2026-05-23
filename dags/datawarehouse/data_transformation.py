from datetime import timedelta,datetime

def parse_duration(duration_str):
    duration_str = duration_str.replace('P', "").replace('T', "")
    components = ["D", "H", "M", "S"]
    values = {"D": 0, "H": 0, "M": 0, "S": 0}
    for component in components:
        if component in duration_str:
            value, duration_str = duration_str.split(component)
            values[component] = int(value)
    return timedelta(days=values["D"], hours=values["H"], minutes=values["M"], seconds=values["S"])

def transform_data(row):
    # Handle both staging (lowercase 'duration' string) and core (already TIME object)
    raw = row.get("duration") or row.get("Duration")
    if isinstance(raw, str):  # only parse if it's still a string
        duration_td = parse_duration(raw)
        row['Duration'] = (datetime.min + duration_td).time()
    else:
        row['Duration'] = raw  # already a TIME object from DB

    if 'Video_Type' not in row:  # only add if not already set
        duration_td = parse_duration(row.get("duration", "PT0S")) if isinstance(raw, str) else None
        row['Video_Type'] = 'Shorts' if duration_td and duration_td.total_seconds() < 60 else 'Normal'

    return row