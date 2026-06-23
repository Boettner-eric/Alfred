from datetime import datetime, timedelta, timezone


def time_ago(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    Modified from: http://stackoverflow.com/a/1551394/141084
    """
    now = datetime.utcnow()
    if type(time) is str:
        diff = now - \
            datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = now - now
    else:
        raise ValueError('invalid date %s of type %s' % (time, type(time)))
    second_diff = round(diff.seconds, 0)
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(second_diff // 60) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(second_diff // 3600) + " hours ago"
    if day_diff == 1:
        return "1 day ago"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 14:
        return "1 week ago"
    if day_diff < 31:
        return str(day_diff//7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff//30) + " months ago"
    return str(day_diff//365) + " years ago"


def format_duration_phrase(minutes):
    if minutes == 1:
        return "a minute"
    if minutes < 60:
        return f"{minutes} minutes"
    hours = minutes // 60
    mins = minutes % 60
    hour_part = "1 hour" if hours == 1 else f"{hours} hours"
    if mins == 0:
        return hour_part
    if mins == 1:
        return f"{hour_part} 1 minute"
    return f"{hour_part} {mins} minutes"


def time_till(event_start, event_end):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    Modified from: http://stackoverflow.com/a/1551394/141084
    """
    event_start, event_end = event_start.replace(
        tzinfo=None), event_end.replace(tzinfo=None)
    subtitle = f'{event_start.hour}:{event_start.minute:02d} - {event_end.hour}:{event_end.minute:02d}'
    now = datetime.now()
    diff = event_start - now

    day_diff = event_start.date() - now.date()

    if event_start < now < event_end:
        return 'now'

    if day_diff < timedelta(days=0):
        return ''

    if day_diff == timedelta(days=0):
        minutes_until = int(diff.total_seconds() // 60)
        if minutes_until < 1:
            return "right now"
        if minutes_until < 1440:
            return f"in {format_duration_phrase(minutes_until)} | Today from {subtitle}"
    if day_diff == timedelta(days=1):
        return f"Tomorrow from {subtitle}"
        # day of the week instead here
    if day_diff < timedelta(days=7):
        return f"in {day_diff.days} days | {event_start.strftime('%A')} from {subtitle}"
    if day_diff < timedelta(days=14):
        return "1 week from now"
    if day_diff < timedelta(days=31):
        return str(day_diff.days//7) + " weeks from now"
    if day_diff < timedelta(days=365):
        return str(day_diff.days//30) + " months from now"
    return str(day_diff.days//365) + " years from now"
