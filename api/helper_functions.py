from datetime import date, datetime, timedelta, time
from django.utils import timezone
from .models import Product, Order, TimelineBar, Stats, ProductionInfo, ProductionLine
from .constants import MOLDING_START_S1, MOLDING_END_S1, MOLDING_START_S2, MOLDING_END_S2, PLEATING_START, PLEATING_END, PRODUCTION_START_S1, PRODUCTION_END_S1, PRODUCTION_START_S2, PRODUCTION_END_S2
from rest_framework import serializers


def parts_filter(products_request):
    if products_request:
        products_request = products_request.split(',')
        return Product.objects.all().filter(part_num__in=products_request)
    else:
        return Product.objects.all()


def determine_period(period, area, queryset):
    today = (timezone.now() - timedelta(hours=8)).date()
    match period:
        case 'today':
            queryset = (queryset.filter(line__area=area, shift__date=today))
        case '7days':
            queryset = (queryset.filter(line__area=area, shift__date__range=[today - timedelta(days=7), today]))
        case '30days':
            queryset = (queryset.filter(line__area=area, shift__date__range=[today - timedelta(days=30), today]))
        case '60days':
            queryset = (queryset.filter(line__area=area, shift__date__range=[today - timedelta(days=60), today]))
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
                queryset_item.shift.date if period_type == 'day'
                else int(queryset_item.shift.date.isocalendar().week) if period_type == 'week'
                else queryset_item.shift.date.month
                ) == list(array_item.values())[0]:
                stats = queryset_item.stats.all()[0]
                good = array_item['good'] + stats.made + prev_item_count
                bad = array_item['scrap'] + stats.scrap + prev_scrap_count
                array_item.update({'good': good, 'scrap': bad, 'good_percentage': round(good / (good + bad), 2)})

        if additive == 'True':
            if prev_item_count or prev_scrap_count:
                if array_item['good'] == 0:
                    array_item.update({'good': prev_item_count})
                if array_item['scrap'] == 0:
                    array_item.update({'scrap': prev_scrap_count})
                array_item.update({'good_percentage': round(prev_item_count / (prev_item_count + prev_scrap_count), 2)})

            prev_item_count = array_item['good']
            prev_scrap_count = array_item['scrap']

    return array


def match_area_rate(area, validated_data, product):
    match area:
        case 'Welding':
            validated_data.update(rate=round(product.rate, 2))
        case 'Molding':
            validated_data.update(rate=round(product.molding_rate, 2))
        case 'Autobag':
            validated_data.update(rate=round(product.autobag_rate, 2))
        case 'Pleating':
            validated_data.update(rate=round(product.pleating_rate, 2))

    return validated_data


def calculate_rates_per_hour(start_time, end_time, instance, shift, rate, time_change):
    rates = shift.get_rates()
    hours = (end_time - start_time).total_seconds() / 3600.0
    for i in range(int(hours)):
        rates[(start_time + timedelta(hours=i)).strftime('%H:%M:%S')] = rate

    if time_change:
        if instance.start < start_time:
            hours_before = (start_time - instance.start).total_seconds() / 3600.0
            for i in range(int(hours_before)):
                del rates[(instance.start + timedelta(hours=i)).strftime('%H:%M:%S')]
        if end_time < instance.end:
            hours_after = (instance.end - end_time).total_seconds() / 3600.0
            for i in range(int(hours_after)):
                del rates[(instance.end - timedelta(hours=i+1)).strftime('%H:%M:%S')]
    shift.set_rates(rates)


def overlap(shift, start, end, **kwargs):
    order_id = kwargs.get('order_id', None)
    orders = Order.objects.filter(shift=shift).exclude(id=order_id if order_id else None)

    for order in orders:
        for f, s in (([order.start, order.end], [start, end]), ([start, end], [order.start, order.end])):
            for x in (f[0], f[1]):
                if s[0] < x < s[1]:
                    return True
    else:
        return False


def order_start_end_validate(start, end, shift_start, shift_end):
    if not shift_start <= start <= (shift_end - timedelta(hours=1)):
        raise serializers.ValidationError({"start": "Value out of range"})
    if not (shift_start + timedelta(hours=1)) <= end <= shift_end:
        raise serializers.ValidationError({"end": "Value out of range"})


def order_validate(quantity, start, end, shift, **kwargs):
    # quantity
    if quantity < 1:
        raise serializers.ValidationError({"quantity": "Can't be 0"})

    # hour format
    if start.minute != 0:
        raise serializers.ValidationError({"start": "Minutes must be 00"})
    if end.minute != 0:
        raise serializers.ValidationError({"end": "Minutes must be 00"})
    if start == end:
        raise serializers.ValidationError(
            {"start": "Can't be the same as end", "end": "Can't be the same as start"})
    if (end - start).total_seconds()/3600.0 < 1:
        raise serializers.ValidationError({"start": "Must be before end", "end": "Must be after start"})

    # range
    match shift.line.area:
        case 'Molding':
            match shift.number:
                case 1:
                    order_start_end_validate(start, end, MOLDING_START_S1(shift), MOLDING_END_S1(shift))
                case 2:
                    order_start_end_validate(start, end, MOLDING_START_S2(shift), MOLDING_END_S2(shift))
        case 'Pleating':
            order_start_end_validate(start, end, PLEATING_START(shift), PLEATING_END(shift))
        case _:
            match shift.number:
                case 1:
                    order_start_end_validate(start, end, PRODUCTION_START_S1(shift), PRODUCTION_END_S1(shift))
                case 2:
                    order_start_end_validate(start, end, PRODUCTION_START_S2(shift), PRODUCTION_END_S2(shift))

    # overlap
    if overlap(shift, start, end, **kwargs):
        raise serializers.ValidationError({"start": "Overlaps another order", "end": "Overlaps another order"})


def new_bar(start, end, bar_date, current_type, length, part_count, fill, shift, shift_id, rate, product, stats):
    bar_id = start.replace(':', '') + shift_id
    hour = start.split(':')
    parts_diff = round(part_count - rate, 2)

    new = TimelineBar.objects.create(
        id=bar_id,
        shift=shift,
        start_time=start,
        end_time=end,
        date=bar_date,
        type=current_type,
        bar_length=length,
        parts_made=part_count,
        hour=hour[0] + ':00:00',
        loss=parts_diff if not fill else parts_diff * 60,
        product=product if not fill else None,
        stats=stats,
        shift_stats=Stats.objects.get(shift__id=shift_id)
    )
    new.save()


def calculate_length(end, start):
    return ((end - start).total_seconds() / 60.0) + 1


def create_missing_minutes(first_min, last_min, total, shift, line):
    minutes = calculate_length(last_min, first_min)
    for i in range(int(minutes)):
        m = first_min + timedelta(minutes=i)
        missing_minute = ProductionInfo.objects.create(
            hour=datetime.strptime(str(m.hour), "%H").time(),
            minute=m,
            item_count=round(total / 60.0, 2) if total else 0,
            date=m.date(),
            line=line,
            shift=shift,
        )
        missing_minute.save()


def check_color(prev_type, this_minute, prev_minute, on_time, minute, parts, shift, shift_id, rate, product, stats, prev_id):

    if parts >= rate:
        current_type = 1
    elif rate > parts > 0:
        current_type = 2
    elif parts == 0:
        current_type = 3

    if current_type != prev_type or this_minute.hour != prev_minute.hour or not on_time:
        new_bar(minute, minute, this_minute.date(), current_type, 1, parts, False, shift, shift_id, rate, product, stats)
    else:
        parts_diff = parts - rate

        TimelineBar.objects.update(
            bar=TimelineBar.objects.get(id=prev_id),
            type=current_type,
            end_time=minute,
            parts_made=parts,
            loss=parts_diff,
            stats=stats,
            shift_stats=Stats.objects.get(shift__id=shift_id)
        )


def determine_fill_bars(beginning, ending, shift):
    result = []

    hours = (((ending - beginning).total_seconds() + 120) / 3600.0)
    shift_datetime = datetime.combine(shift.date, time(0, 0), tzinfo=timezone.utc)

    result.append([beginning, shift_datetime + timedelta(hours=beginning.hour, minutes=59)])
    for i in range(1, int(hours)):
        result.append([shift_datetime + timedelta(hours=beginning.hour + i),
                       shift_datetime + timedelta(hours=beginning.hour + i, minutes=59)])
    result.append([shift_datetime + timedelta(hours=beginning.hour + int(hours)), ending])

    return result
