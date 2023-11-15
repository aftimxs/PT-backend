from datetime import date, datetime, timedelta
from django.utils import timezone


def determine_period(period, queryset):
    today = (timezone.now() - timedelta(hours=8)).date()
    match period:
        case 'today':
            queryset = (queryset.filter(date=today))
        case '7days':
            queryset = (queryset.filter(date__range=[today - timedelta(days=7), today]))
        case '30days':
            queryset = (queryset.filter(date__range=[today - timedelta(days=30), today]))
        case '60days':
            queryset = (queryset.filter(date__range=[today - timedelta(days=60), today]))
    return queryset


def get_period_days(grouping, period):
    today = (timezone.now() - timedelta(hours=8)).date()
    days = []
    weeks = []
    months = []
    match grouping:
        case 'daily':
            match period:
                case 'today':
                    days.append(today)
                case '7days':
                    for x in range(7):
                        days.append((today - timedelta(days=x)))
                case '30days':
                    for x in range(30):
                        days.append((today - timedelta(days=x)))
                case '60days':
                    for x in range(60):
                        days.append((today - timedelta(days=x)))
            return days
        case 'weekly':
            match period:
                case '30days':
                    for x in range(4):
                        weeks.append((today - timedelta(weeks=x)).isocalendar().week)
                case '60days':
                    for x in range(8):
                        weeks.append((today - timedelta(weeks=x)).isocalendar().week)
            return weeks
        case 'monthly':
            match period:
                case '60days':
                    for x in range(2):
                        months.append((today - timedelta(weeks=(x*4))).month)
            return months
