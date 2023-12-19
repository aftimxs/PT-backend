from datetime import date, datetime, timedelta, time, timezone


def PRODUCTION_START_S1(shift):
    return datetime.combine(shift.date, time(7, 0), tzinfo=timezone.utc)


def PRODUCTION_END_S1(shift):
    return datetime.combine(shift.date, time(17, 0), tzinfo=timezone.utc)


def PRODUCTION_START_S2(shift):
    return datetime.combine(shift.date, time(17, 0), tzinfo=timezone.utc)


def PRODUCTION_END_S2(shift):
    return datetime.combine(shift.date + timedelta(days=1), time(2, 0), tzinfo=timezone.utc)


def MOLDING_START_S1(shift):
    return datetime.combine(shift.date, time(6, 0), tzinfo=timezone.utc)


def MOLDING_END_S1(shift):
    return datetime.combine(shift.date, time(18, 0), tzinfo=timezone.utc)


def MOLDING_START_S2(shift):
    return datetime.combine(shift.date, time(18, 0), tzinfo=timezone.utc)


def MOLDING_END_S2(shift):
    return datetime.combine(shift.date + timedelta(days=1), time(6, 0), tzinfo=timezone.utc)


def PLEATING_START(shift):
    return datetime.combine(shift.date, time(6, 0), tzinfo=timezone.utc)


def PLEATING_END(shift):
    return datetime.combine(shift.date, time(16, 0), tzinfo=timezone.utc)
