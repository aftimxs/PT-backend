from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist

from django.db.models import Prefetch
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from .serializers import *
from .helper_functions import (determine_period, get_period_days, parts_filter, array_vs_queryset, new_bar,
                               calculate_length, create_missing_minutes, check_color, determine_fill_bars)


# Create your views here.
class ShiftView(viewsets.ModelViewSet):
    serializer_class = ShiftSerializer
    queryset = Shift.objects.all().order_by('date').prefetch_related(
        Prefetch('info', queryset=ProductionInfo.objects.order_by('minute')))
    # permission_classes = ([IsAuthenticated])


class ShortShiftView(viewsets.ModelViewSet):
    serializer_class = ShiftOnlyOrderSerializer
    queryset = Shift.objects.all().order_by('date')
    # permission_classes = ([IsAuthenticated])


class StatsView(viewsets.ModelViewSet):
    serializer_class = StatsSerializer
    queryset = Stats.objects.all()
    # permission_classes = ([IsAuthenticated])


class ProductionLineView(viewsets.ModelViewSet):
    serializer_class = ProductionLineSerializer

    # permission_classes = ([IsAuthenticated])

    def get_queryset(self):
        queryset = ProductionLine.objects.all()
        area = self.request.query_params.get('area')
        cell = self.request.query_params.get('cell')
        date = self.request.query_params.get('date')
        number = self.request.query_params.get('number')

        if date is not None and number is not None and area is not None:
            if area == 'All':
                queryset = (queryset.
                            prefetch_related(Prefetch('shift', queryset=Shift.objects.filter(number=number, date=date))))
            else:
                if cell is not None:
                    queryset = (queryset.filter(area=area, cell=cell).
                            prefetch_related(Prefetch('shift', queryset=Shift.objects.filter(number=number, date=date))))
                else:
                    queryset = (queryset.filter(area=area).
                                prefetch_related(Prefetch('shift', queryset=Shift.objects.filter(number=number, date=date))))

        return queryset


class CalendarLookupView(viewsets.ModelViewSet):
    serializer_class = CalendarShiftSerializer

    def get_queryset(self):
        queryset = Shift.objects.all()
        area = self.request.query_params.get('area')
        year = self.request.query_params.get('year')
        month = self.request.query_params.get('month')

        if year is not None and month is not None and area is not None:
            if area == 'All':
                queryset = Shift.objects.all().filter(date__year=year, date__month=month)
            else:
                queryset = Shift.objects.all().filter(line__area=area, date__year=year, date__month=month)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        class CalendarShift(object):
            def __init__(self, id, title, date, allDay, editable, backgroundColor, borderColor, extendedProps):
                self.id = id
                self.title = title
                self.date = date
                self.allDay = allDay
                self.editable = editable
                self.backgroundColor = backgroundColor
                self.borderColor = borderColor
                self.extendedProps = extendedProps

        shifts = []
        for shift in queryset:
            def color():
                if shift.passed:
                    if shift.active:
                        return '#66bb6a'
                    else:
                        if shift.has_data:
                            return '#ffa726'
                        else:
                            return '#f44336'
                else:
                    return '#0288d1'
            shifts.append(CalendarShift(
                shift.id,
                "{area} {cell} (S:{number})".format(area=shift.line.area, cell=shift.line.cell, number=shift.number),
                shift.date,
                True,
                not (shift.passed or shift.has_data or shift.active),
                color(),
                color(),
                {'area': shift.line.area, 'cell': shift.line.cell, 'shift': shift}
            ))

        return Response(CalendarShiftSerializer(shifts, many=True).data)


class CalendarDayLookupView(viewsets.ModelViewSet):
    serializer_class = CalendarDayShiftSerializer

    def get_queryset(self):
        queryset = Shift.objects.all()
        area = self.request.query_params.get('area')
        year = self.request.query_params.get('year')
        month = self.request.query_params.get('month')
        day = self.request.query_params.get('day')

        if year is not None and month is not None and day is not None and area is not None:
            if area == 'All':
                queryset = Shift.objects.all().filter(date__year=year, date__month=month, date__day=day)
            else:
                queryset = Shift.objects.all().filter(line__area=area, date__year=year, date__month=month, date__day=day)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        class CalendarDayShift(object):
            def __init__(self, id, area, cell, shift):
                self.id = id
                self.area = area
                self.cell = cell
                self.shift = shift

        shifts = []
        for shift in queryset:
            shifts.append(CalendarDayShift(
                shift.id,
                shift.line.area,
                shift.line.cell,
                shift
            ))

        return Response(CalendarDayShiftSerializer(shifts, many=True).data)


class CalendarLineLookupView(generics.ListAPIView):
    serializer_class = CalendarLineSerializer
    # permission_classes = ([IsAuthenticated])

    def get_queryset(self):
        queryset = Shift.objects.all()
        line = self.request.query_params.get('line')
        area = self.request.query_params.get('area')
        month = datetime.strptime(self.request.query_params.get('date'), '%Y-%m-%d').month

        if line != 'undefined' and month:
            queryset = queryset.filter(line__id=line, date__month=month)
        elif area != 'undefined' and month:
            if area == 'All':
                queryset = queryset.filter(date__month=month)
            else:
                queryset = queryset.filter(line__area=area, date__month=month)
        else:
            raise serializers.ValidationError({"error": "Line and date required"})

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        x = {'days': []}
        for shift in queryset:
            x['days'].append(shift.date)

        serializer = CalendarLineSerializer(x, many=False)
        return Response(serializer.data)


class MachineView(viewsets.ModelViewSet):
    serializer_class = MachineSerializer
    permission_classes = ([IsAuthenticated])

    def get_queryset(self):
        queryset = Machine.objects.all()
        line = self.request.query_params.get('line')

        if line is not None:
            queryset = queryset.filter(line=line)
        return queryset


class ProductView(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    # permission_classes = ([IsAuthenticated])

    def get_queryset(self):
        queryset = Product.objects.all()
        area = self.request.query_params.get('area')

        if area is not None:
            match area:
                case 'Welding':
                    queryset = queryset.exclude(rate=0)
                case 'Molding':
                    queryset = queryset.exclude(molding_rate=0)
                case 'Autobag':
                    queryset = queryset.exclude(autobag_rate=0)
                case 'Pleating':
                    queryset = queryset.exclude(pleating_rate=0)
                case _:
                    queryset = queryset

        return queryset


class OrderView(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    # permission_classes = ([IsAuthenticated])

    def destroy(self, request, *args, **kwargs):
        # look for instance or raise 404
        instance = get_object_or_404(Order, pk=kwargs['pk'])

        if instance:
            # remove quantity from shift
            instance.shift.quantity = instance.shift.quantity - instance.quantity

            # remove product from shift
            if instance.shift.items:
                x = instance.shift.get_items()
                index = x.index(instance.product.part_num)
                del x[index]
                instance.shift.set_items(x)

            if instance.shift.rate_per_hour:
                rates = instance.shift.get_rates()
                start = instance.start
                end = instance.end

                hours = (end - start).total_seconds() / 3600.0

                for i in range(int(hours)):
                    del rates[(start + timedelta(hours=i)).strftime('%H:%M:%S')]
                instance.shift.set_rates(rates)

            instance.shift.save()

        # delete instance
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OperatorView(viewsets.ModelViewSet):
    queryset = Operator.objects.all()
    serializer_class = OperatorSerializer
    permission_classes = ([IsAuthenticated])


class ProductionInfoView(viewsets.ModelViewSet):
    queryset = ProductionInfo.objects.all().order_by('minute')
    serializer_class = ProductionInfoSerializer
    # permission_classes = ([IsAuthenticated])


class ScrapView(viewsets.ModelViewSet):
    serializer_class = ScrapSerializer
    # permission_classes = ([IsAuthenticated])

    def get_queryset(self):
        queryset = Scrap.objects.all()
        shift = self.request.query_params.get('shift')
        product = self.request.query_params.get('product')

        if shift is not None:
            if product is not None:
                queryset = (queryset.filter(shift=shift, product=product))
            else:
                queryset = (queryset.filter(shift=shift))
        return queryset

    def destroy(self, request, *args, **kwargs):
        if request.data:
            scrap_id = request.data['id']
            pieces = request.data['pieces']
            shift = request.data['shift']
            bar_id = request.data['bar']

            bar = TimelineBar.objects.get(id=bar_id)
            bar_dt = datetime.combine(bar.date, bar.hour, tzinfo=timezone.utc)

            if pieces:
                shift_to_update = Stats.objects.get(shift__id=shift)
                order_to_update = Stats.objects.get(order__shift__id=shift, order__start__lte=bar_dt, order__end__gt=bar_dt)

                shift_to_update.scrap = shift_to_update.scrap - pieces
                shift_to_update.bars_scrap = shift_to_update.bars_scrap - pieces
                order_to_update.scrap = order_to_update.scrap - pieces
                order_to_update.bars_scrap = order_to_update.bars_scrap - pieces

                shift_to_update.save()
                order_to_update.save()

            bar_to_update = TimelineBar.objects.get(id=bar_id)
            bar_to_update.has_scrap = False
            bar_to_update.save()

            self.get_queryset().filter(id=scrap_id).delete()
        else:
            instance = self.get_object()
            self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DowntimeView(viewsets.ModelViewSet):
    serializer_class = DowntimeSerializer
    permission_classes = ([IsAuthenticated])

    def get_queryset(self):
        queryset = Downtime.objects.all()
        shift = self.request.query_params.get('shift')

        if shift is not None:
            queryset = (queryset.filter(shift=shift))
        return queryset


class SpeedlossView(viewsets.ModelViewSet):
    serializer_class = SpeedlossSerializer
    permission_classes = ([IsAuthenticated])

    def get_queryset(self):
        queryset = Speedloss.objects.all()
        shift = self.request.query_params.get('shift')

        if shift is not None:
            queryset = (queryset.filter(shift=shift))
        return queryset


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    # def _send_email_verification(self, user: CustomUser):
    #     current_site = get_current_site(self.request)
    #     subject = 'Activate Your Account'
    #     body = render_to_string(
    #         'emails/email_verification.html',
    #         {
    #             'domain': current_site.domain,
    #             'uid': urlsafe_base64_encode(force_bytes(user.pk)),
    #             'token': email_verification_token.make_token(user),
    #         }
    #     )
    #     EmailMessage(to=[user.email], subject=subject, body=body).send()


class TimelineBarView(viewsets.ModelViewSet):
    serializer_class = TimelineBarSerializer

    def get_queryset(self):
        queryset = TimelineBar.objects.all()
        shift = self.request.query_params.get('shift')
        type = self.request.query_params.get('type')

        if shift is not None:
            queryset = (queryset.filter(shift=shift))
            if type is not None:
                queryset = (queryset.filter(shift=shift, type=type))

        return queryset


class MinutesView(generics.ListCreateAPIView):
    serializer_class = ProductionInfoSerializer
    queryset = ProductionInfo.objects.all().order_by('minute')
    # permission_classes = ([IsAuthenticated])

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = ProductionInfoSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            # REQUEST DATA
            shift_id = request.data['shift']
            line_id = request.data['line']
            parts = float(request.data['item_count'])
            minute = request.data['minute']
            hour = request.data['hour']

            shift = Shift.objects.get(id=shift_id)
            line = ProductionLine.objects.get(id=line_id)
            hour_dt = time(hour=int(hour.split(':')[0]), minute=0)

            if shift.number == 2 and hour_dt.hour < 7:
                hour_w_date = datetime.combine(shift.date + timedelta(days=1), hour_dt, tzinfo=timezone.utc)
            else:
                hour_w_date = datetime.combine(shift.date, hour_dt, tzinfo=timezone.utc)

            try:
                order = Order.objects.get(shift=shift_id, start__lte=hour_w_date, end__gt=hour_w_date)
            except ObjectDoesNotExist:
                return Response(data={'Inactive': 'No active order at that time'}, status=status.HTTP_404_NOT_FOUND)

            stats = Stats.objects.get(order=order)

            # DB DATA
            previous_bar = TimelineBar.objects.filter(shift=shift_id).order_by('date').values().last()
            rate = order.rate
            product = order.product.part_num

            # DATA FOR BAR TYPE
            minute_rate = rate / 60

            if previous_bar:
                prev_type = previous_bar['type']
                prev_id = previous_bar['id']
                prev_minute = datetime.combine(previous_bar['date'], previous_bar['end_time'], tzinfo=timezone.utc)
            else:
                prev_type = 0
                prev_id = None

                match shift.line.area:
                    case 'Molding':
                        match shift.number:
                            case 1:
                                prev_minute = MOLDING_START_S1(shift) - timedelta(minutes=1)
                            case 2:
                                prev_minute = MOLDING_START_S2(shift) - timedelta(minutes=1)
                            case 3:
                                prev_minute = MOLDING_START_S3(shift) - timedelta(minutes=1)
                    case 'Pleating':
                        prev_minute = PLEATING_START(shift) - timedelta(minutes=1)
                    case _:
                        match shift.number:
                            case 1:
                                prev_minute = PRODUCTION_START_S1(shift) - timedelta(minutes=1)
                            case 2:
                                prev_minute = PRODUCTION_START_S2(shift) - timedelta(minutes=1)

            if shift.number == 2 and hour_dt.hour < 7:
                this_minute = datetime.combine(shift.date + timedelta(days=1), datetime.strptime(minute, "%H:%M").time(), tzinfo=timezone.utc)
            else:
                this_minute = datetime.combine(shift.date, datetime.strptime(minute, "%H:%M").time(), tzinfo=timezone.utc)

            on_time = this_minute == prev_minute + timedelta(minutes=1)

            if on_time:
                check_color(prev_type, this_minute, prev_minute, True, minute, parts, shift, shift_id, minute_rate, product, stats, prev_id)
            else:
                # FILL GAP
                s = prev_minute + timedelta(minutes=1)
                e = this_minute - timedelta(minutes=1)

                # CHECK IF IT SPANS MULTIPLE HOURS
                if s.hour != e.hour:
                    fill_bars = determine_fill_bars(beginning=s, ending=e, shift=shift)
                    # filler bars
                    for bar in fill_bars:
                        long = calculate_length(end=bar[1], start=bar[0])
                        new_bar(bar[0].strftime("%H:%M"), bar[1].strftime("%H:%M"), bar[0].date(), 4, long, 0, True, shift, shift_id, minute_rate, product, stats)
                else:
                    # filler bar
                    long = calculate_length(end=e, start=s)
                    new_bar(s.strftime("%H:%M"), e.strftime("%H:%M"), s.date(), 4, long, 0, True, shift, shift_id, minute_rate, product, stats)

                # fill minutes gap
                create_missing_minutes(first_min=s, last_min=e, total=0, shift=shift, line=line)

                # make this posts bar
                check_color(prev_type, this_minute, prev_minute, False, minute, parts, shift, shift_id, minute_rate, product, stats, prev_id)

            # make this posts minute
            new_minute = ProductionInfo.objects.create(
                hour=request.data['hour'],
                minute=request.data['minute'],
                item_count=request.data['item_count'],
                date=request.data['date'],
                line=ProductionLine.objects.get(id=request.data['line']),
                shift=shift,
            )
            new_minute.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MinutesForGraphView(generics.ListAPIView):
    # permission_classes = ([IsAuthenticated])

    def get_queryset(self):
        queryset = ProductionInfo.objects.all().order_by('date', 'minute')
        shift = self.request.query_params.get('shift')

        if shift:
            queryset = queryset.filter(shift__id=shift)
            return queryset
        else:
            raise serializers.ValidationError({"error": "Shift required"})

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        shift_id = self.request.query_params.get('shift')
        orders = Order.objects.filter(shift__id=shift_id)

        info = [{'id': 'reference', 'color': "#ffb74d", 'data': []}]

        x = 1
        for order in orders:
            info.append({'id': None, 'color': "#ffffff", 'data': []})
            for minute_info in queryset:
                minute_dt = datetime.combine(minute_info.date, minute_info.minute, tzinfo=timezone.utc)
                if order.start <= minute_dt < order.end:
                    info[x]['data'].append({'x': minute_dt, 'y': minute_info.item_count})
                    info[0]['data'].append({'x': minute_dt, 'y': round(order.rate/60.0, 2)})
                    if info[x]['id'] is None:
                        info[x]['id'] = order.product.part_num
            x = x + 1

        return Response(GraphMinutesSerializer(info, many=True).data)


class BarCommentsView(viewsets.ModelViewSet):
    queryset = BarComments.objects.all()
    serializer_class = BarCommentsSerializer
    # permission_classes = ([IsAuthenticated])


class HourTotalPostView(generics.CreateAPIView):
    serializer_class = TotalHourSerializer
    queryset = ProductionInfo.objects.all().order_by('minute')
    # permission_classes = ([IsAuthenticated])

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            shift_id = request.data['shift']
            total = float(request.data['total'])
            hour = request.data['hour']

            line = ProductionLine.objects.get(shift=shift_id)
            shift = Shift.objects.get(id=shift_id)

            f_min = datetime.strptime(hour, "%H:%M:%S")

            if shift.number == 2 and f_min.hour < 7:
                start = datetime.combine(shift.date + timedelta(days=1), f_min.time(), tzinfo=timezone.utc)
            else:
                start = datetime.combine(shift.date, f_min.time(), tzinfo=timezone.utc)
            end = (start + timedelta(minutes=59))

            try:
                order = Order.objects.get(shift=shift_id, start__lte=start, end__gt=end)
            except ObjectDoesNotExist:
                return Response(data={'Inactive': 'No active order at that time'}, status=status.HTTP_404_NOT_FOUND)

            rate = order.rate
            product = order.product.part_num
            stats = Stats.objects.get(order=order)

            if total >= rate:
                new_bar(start=hour, end=end, bar_date=start.date(), current_type=1, length=60, part_count=total, fill=False, shift=shift,
                        shift_id=shift_id, rate=rate, product=product, stats=stats)
            elif rate > total > 0:
                new_bar(start=hour, end=end, bar_date=start.date(), current_type=2, length=60, part_count=total, fill=False, shift=shift,
                        shift_id=shift_id, rate=rate, product=product, stats=stats)
            elif total == 0:
                new_bar(start=hour, end=end, bar_date=start.date(), current_type=3, length=60, part_count=total, fill=False, shift=shift,
                        shift_id=shift_id, rate=rate, product=product, stats=stats)

            create_missing_minutes(first_min=start, last_min=end, total=total, shift=shift, line=line)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductStatisticsView(generics.ListAPIView):
    # permission_classes = ([IsAuthenticated])

    def get_queryset(self):
        queryset = Order.objects.all()
        period = self.request.query_params.get('period')
        area = self.request.query_params.get('area')

        if period is not None and area is not None:
            queryset = determine_period(period, area, queryset)
            return queryset.exclude(stats__made__exact=0)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        bar_type = self.request.query_params.get('bar_type')
        data_request = self.request.query_params.get('data_request')
        period = self.request.query_params.get('period')
        area = self.request.query_params.get('area')

        match period:
            case 'today':
                sub_period = 'Today'
            case '7days':
                sub_period = 'the last 7 days'
            case '30days':
                sub_period = 'the last 30 days'
            case '60days':
                sub_period = 'the last 60 days'

        if bar_type is not None:
            match bar_type:
                case 'Bar':
                    if data_request is not None:
                        match data_request:
                            case 'parts-made':
                                products_request = self.request.query_params.get('products')
                                products_queryset = parts_filter(products_request)

                                products = [{'product_id': product.id, 'product': product.part_num, 'good': 0,
                                             'scrap': 0, 'good_percentage': 0} for product in products_queryset]
                                for product in products:
                                    for order in queryset:
                                        if order.product.id == product['product_id']:
                                            stats = order.stats.all()[0]
                                            good = product['good'] + stats.made
                                            bad = product['scrap'] + stats.scrap
                                            product.update({'good': good, 'scrap': bad,
                                                            'good_percentage': round(good/(good+bad), 2)})

                                extras = {'keys': ['good', 'scrap'], 'index_by': ['product'], 'color': ['#66bb6a', '#d32f2f'],
                                          'legend_x': 'Product', 'legend_y': 'Count', 'group_mode': 'grouped',
                                          'title': f'{area.upper()} pieces by part', 'subtitle': f'{products_request} for {sub_period}'}

                                serializer_list = [PartsMadeSerializer(products, many=True).data,
                                                ChartsExtraInfoSerializer(extras, many=False).data]

                                return Response(serializer_list)

                            case 'accumulated-total':
                                count = [{'product': 'All', 'good': 0, 'scrap': 0, 'good_percentage': 0}]
                                for x in count:
                                    for order in queryset:
                                        stats = order.stats.all()[0]
                                        good = x['good'] + stats.made
                                        bad = x['scrap'] + stats.scrap
                                        x.update({'good': good, 'scrap': bad, 'good_percentage': round(good/(good+bad), 2)})

                                extras = {'keys': ['good', 'scrap'], 'index_by': ['product'], 'legend_x': 'Product',
                                          'legend_y': 'Count', 'group_mode': 'grouped', 'color': ['#66bb6a', '#d32f2f'],
                                          'title': f'{area.upper()} total accumulated pieces', 'subtitle': f'for {sub_period}'}

                                serializer_list = [AccumulatedTotalParts(count, many=True).data,
                                                   ChartsExtraInfoSerializer(extras, many=False).data]

                                return Response(serializer_list)

                            case 'accumulated-total-period':
                                period = self.request.query_params.get('period')
                                grouping = self.request.query_params.get('grouping')
                                additive = self.request.query_params.get('additive')

                                if grouping:
                                    sub_additive = 'Additive' if additive == 'True' else 'Non-Additive'
                                    match grouping:
                                        case 'daily':
                                            days_range = get_period_days(grouping, period)
                                            response_array = array_vs_queryset('day', days_range, queryset, additive)

                                            extras = {'keys': ['good', 'scrap'], 'index_by': ['day'],
                                                      'legend_x': 'Days', 'legend_y': 'Count', 'color': ['#66bb6a', '#d32f2f'],
                                                      'title': f'{area.upper()} daily accumulated pieces',
                                                      'subtitle': f'{sub_additive} for {sub_period}'}

                                            serializer_list = [TotalPartsMadeDailySerializer(response_array, many=True).data,
                                                               ChartsExtraInfoSerializer(extras, many=False).data]

                                            return Response(serializer_list)

                                        case 'weekly':
                                            weeks_range = get_period_days(grouping, period)
                                            response_array = array_vs_queryset('week', weeks_range, queryset, additive)

                                            extras = {'keys': ['good', 'scrap'],
                                                      'index_by': ['week'],
                                                      'legend_x': 'Week', 'legend_y': 'Count', 'color': ['#66bb6a', '#d32f2f'],
                                                      'title': f'{area.upper()} weekly accumulated pieces', 'subtitle': f'{sub_additive} for {sub_period}'}

                                            serializer_list = [TotalPartsMadeWeeklySerializer(response_array, many=True).data,
                                                               ChartsExtraInfoSerializer(extras, many=False).data]

                                            return Response(serializer_list)

                                        case 'monthly':
                                            months_range = get_period_days(grouping, period)
                                            response_array = array_vs_queryset('month', months_range, queryset, additive)

                                            extras = {'keys': ['good', 'scrap'],
                                                      'index_by': ['month'],
                                                      'legend_x': 'Month', 'legend_y': 'Count', 'color': ['#66bb6a', '#d32f2f'],
                                                      'title': f'{area.upper()} monthly accumulated pieces', 'subtitle': f'{sub_additive} for {sub_period}'}

                                            serializer_list = [TotalPartsMadeMonthlySerializer(response_array, many=True).data,
                                                               ChartsExtraInfoSerializer(extras, many=False).data]

                                            return Response(serializer_list)
                                else:
                                    return Response({'detail': "Request data 'grouping' is missing"}, status=status.HTTP_400_BAD_REQUEST)

                            case 'total-runs':
                                products_request = self.request.query_params.get('products')
                                products_queryset = parts_filter(products_request)

                                products = [{'product_id': product.id, 'product': product.part_num, 'runs': 0} for product in products_queryset]
                                for product in products:
                                    for order in queryset:
                                        if order.product.id == product['product_id']:
                                            product.update({'runs': product['runs'] + 1})

                                extras = {'keys': ['runs'], 'index_by': ['product'], 'legend_x': 'Runs', 'legend_y': 'Count',
                                          'color': ['#0288d1'], 'title': f'{area.upper()} total runs',
                                          'subtitle': f'{products_request} for {sub_period}'}

                                serializer_list = [ProductTimesRunSerializer(products, many=True).data,
                                                   ChartsExtraInfoSerializer(extras, many=False).data]

                                return Response(serializer_list)

                            case 'expected-vs-actual-rate':
                                products_request = self.request.query_params.get('products')
                                products_queryset = parts_filter(products_request)

                                match area:
                                    case 'Welding':
                                        products = [{'product_id': product.id, 'product': product.part_num,
                                                     'expected': round(product.rate, 2), 'actual': product.rate, 'shift_count': 0}
                                                    for product in products_queryset]
                                    case 'Molding':
                                        products = [{'product_id': product.id, 'product': product.part_num,
                                                     'expected': round(product.molding_rate, 2), 'actual': product.molding_rate, 'shift_count': 0}
                                                    for product in products_queryset]
                                    case 'Autobag':
                                        products = [{'product_id': product.id, 'product': product.part_num,
                                                     'expected': round(product.autobag_rate, 2), 'actual': product.autobag_rate, 'shift_count': 0}
                                                    for product in products_queryset]
                                    case 'Pleating':
                                        products = [{'product_id': product.id, 'product': product.part_num,
                                                     'expected': round(product.pleating_rate, 2), 'actual': product.pleating_rate, 'shift_count': 0}
                                                    for product in products_queryset]

                                for product in products:
                                    parts = 0
                                    minutes = 0
                                    shift_count = 0
                                    for order in queryset:
                                        if order.product.id == product['product_id']:
                                            stats = order.stats.all()[0]
                                            parts = parts + (stats.made-stats.scrap)
                                            minutes = minutes + order.active_minutes
                                            shift_count += 1
                                    if parts != 0 and minutes != 0:
                                        product.update({'actual': round(((parts/minutes)*60), 2), 'shift_count': shift_count})

                                extras = {'keys': ['expected', 'actual'], 'index_by': ['product'],
                                          'legend_x': 'Expected vs Actual Rate', 'legend_y': 'Rate', 'group_mode': "grouped",
                                          'color': ['#66bb6a', '#0288d1'], 'title': f'{area.upper()} expected vs Actual rate',
                                          'subtitle': f'{products_request} for {sub_period}'}

                                serializer_list = [ProductActualRateSerializer(products, many=True).data,
                                                   ChartsExtraInfoSerializer(extras, many=False).data]

                                return Response(serializer_list)


class LineStatisticsView(generics.ListAPIView):
    # permission_classes = ([IsAuthenticated])

    def get_queryset(self):
        queryset = Shift.objects.all()
        period = self.request.query_params.get('period')

        if period is not None:
            queryset = determine_period(period, queryset)
            return queryset.exclude(total_parts__exact=0)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        data_request = self.request.query_params.get('data_request')

        if data_request is not None:
            match data_request:
                case 'parts-made':
                    lines = [{'line': line.id, 'item_count': 0} for line in ProductionLine.objects.all()]
                    for line in lines:
                        for shift in queryset:
                            if shift.line.id in line.values():
                                line.update({'item_count': list(line.values())[1] + shift.total_parts})

                    return Response(PartsMadeSerializer(lines, many=True).data)

                case 'total-runs':
                    products = [{'product_id': product.id, 'product': product.part_num, 'run_count': 0} for product in Product.objects.all()]
                    for product in products:
                        for shift in queryset:
                            if shift.order.values()[0]['product_id'] in product.values():
                                product.update({'run_count': list(product.values())[2] + 1})

                    return Response(ProductTimesRunSerializer(products, many=True).data)