from datetime import date, datetime, timedelta
from django.utils import timezone
from .models import Product


def parts_filter(products_request):
    if products_request:
        products_request = products_request.split(',')
        return Product.objects.all().filter(part_num__in=products_request)
    else:
        return Product.objects.all()


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
                        days.insert(0, (today - timedelta(days=x)))
                case '30days':
                    for x in range(30):
                        days.insert(0, (today - timedelta(days=x)))
                case '60days':
                    for x in range(60):
                        days.insert(0, (today - timedelta(days=x)))
            return days
        case 'weekly':
            match period:
                case '30days':
                    for x in range(4):
                        weeks.insert(0, (today - timedelta(weeks=x)).isocalendar().week)
                case '60days':
                    for x in range(8):
                        weeks.insert(0, (today - timedelta(weeks=x)).isocalendar().week)
            return weeks
        case 'monthly':
            match period:
                case '60days':
                    for x in range(2):
                        months.insert(0, (today - timedelta(weeks=(x*4))).month)
            return months


def array_vs_queryset(period_type, period_range, queryset, additive):
    array = [{period_type: x, 'good': 0, 'scrap': 0, 'good_percentage': 0} for x in period_range]
    prev_item_count = 0
    prev_scrap_count = 0
    for array_item in array:
        for queryset_item in queryset:
            if (
                queryset_item.date if period_type == 'day'
                else int(queryset_item.date.isocalendar().week) if period_type == 'week'
                else queryset_item.date.month
                ) == list(array_item.values())[0]:
                good = list(array_item.values())[1] + queryset_item.total_parts + prev_item_count
                bad = list(array_item.values())[2] + queryset_item.total_scrap + prev_scrap_count
                array_item.update({'good': good, 'scrap': bad, 'good_percentage': round(good / (good + bad), 2)})

        if additive == 'True':
            if prev_item_count or prev_scrap_count:
                if list(array_item.values())[1] == 0:
                    array_item.update({'good': prev_item_count})
                if list(array_item.values())[2] == 0:
                    array_item.update({'scrap': prev_scrap_count})
                array_item.update({'good_percentage': round(prev_item_count / (prev_item_count + prev_scrap_count), 2)})

            prev_item_count = list(array_item.values())[1]
            prev_scrap_count = list(array_item.values())[2]

    return array
