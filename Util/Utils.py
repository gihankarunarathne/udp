#!/usr/bin/python3
import datetime, re


def getUTCOffset(utcOffset, default=False):
    """
    Get timedelta instance of given UTC offset string.
    E.g. Given UTC offset string '+05:30' will return
    datetime.timedelta(hours=5, minutes=30))

    :param string utcOffset: UTC offset in format of [+/1][HH]:[MM]
    :param boolean default: If True then return 00:00 time offset on invalid format.
    Otherwise return False on invalid format.
    """
    offset_pattern = re.compile("[+-]\d\d:\d\d")
    match = offset_pattern.match(utcOffset)
    if match:
        utcOffset = match.group()
    else:
        if default:
            print("UTC_OFFSET :", utcOffset, " not in correct format. Using +00:00")
            return datetime.timedelta()
        else:
            return False

    if utcOffset[0] == "-":  # If timestamp in negtive zone, add it to current time
        offset_str = utcOffset[1:].split(':')
        return datetime.timedelta(hours=int(offset_str[0]), minutes=int(offset_str[1]))
    if utcOffset[0] == "+":  # If timestamp in positive zone, deduct it to current time
        offset_str = utcOffset[1:].split(':')
        return datetime.timedelta(hours=-1 * int(offset_str[0]), minutes=-1 * int(offset_str[1]))
