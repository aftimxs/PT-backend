from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import *
from django.db.models import Prefetch
from rest_framework import generics
from django.contrib.auth.models import User

from rest_framework_simplejwt.views import TokenObtainPairView

from datetime import date, datetime, timedelta

from .helper_functions import determine_period, get_period_days, parts_filter, array_vs_queryset


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
                not shift.passed,
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

        if shift is not None:
            queryset = (queryset.filter(shift=shift))
        return queryset

    def destroy(self, request, *args, **kwargs):
        if request.data:
            scrap_id = request.data['id']
            pieces = request.data['pieces']
            shift = request.data['shift']
            bar = request.data['bar']

            if pieces:
                shift_to_update = Shift.objects.get(id=shift)
                shift_to_update.total_scrap = shift_to_update.total_scrap - pieces
                shift_to_update.save()

            bar_to_update = TimelineBar.objects.get(id=bar)
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
            shift = request.data['shift']
            parts = float(request.data['item_count'])
            minute = request.data['minute']

            # DB DATA
            previous_bar = TimelineBar.objects.filter(shift=shift).values().last()
            rate = Order.objects.get(shift=shift).rate
            shift_num = getattr(Shift.objects.get(id=shift), 'number')

            # DATA FOR BAR TYPE
            minute_rate = rate / 60

            if previous_bar:
                prev_type = previous_bar['type']
                prev_id = previous_bar['id']
                prev_end_min = previous_bar['end_time']
            else:
                prev_type = 0
                prev_id = None
                if shift_num == 1:
                    prev_end_min = datetime.strptime("05:59", "%H:%M").time()
                elif shift_num == 2:
                    prev_end_min = datetime.strptime("16:59", "%H:%M").time()

            this_minute = datetime.combine(date.today(), datetime.strptime(minute, "%H:%M").time())
            prev_minute = datetime.combine(date.today(), prev_end_min)

            on_time = this_minute == prev_minute + timedelta(minutes=1)

            # CREATE NEW BAR
            def new_bar(start, end, current_type, length, part_count):
                bar_id = start.replace(':', '') + shift
                hour = start.split(':')
                parts_diff = round(part_count-minute_rate, 2)

                new = TimelineBar.objects.create(
                    id=bar_id,
                    shift=Shift.objects.filter(id=shift)[0],
                    start_time=start,
                    end_time=end,
                    type=current_type,
                    bar_length=length,
                    parts_made=part_count,
                    hour=hour[0]+':00:00',
                    loss=parts_diff,
                )
                new.save()

            def check_color(current_type):
                if current_type != prev_type or this_minute.hour != prev_minute.hour or not on_time:
                    new_bar(minute, minute, current_type, 1, parts)
                else:
                    parts_diff = round(parts - minute_rate, 2)

                    TimelineBar.objects.update(
                        bar=TimelineBar.objects.get(id=prev_id),
                        type=current_type,
                        end_time=minute,
                        parts_made=parts,
                        loss=parts_diff
                    )

            def check_rate():
                if parts >= minute_rate:
                    check_color(1)
                elif minute_rate > parts > 0:
                    check_color(2)
                elif parts == 0:
                    check_color(3)

            def calculate_length(end, start):
                return ((end - start).total_seconds() / 60.0) + 1

            def create_missing_minutes(first_min, last_min):
                minutes = calculate_length(last_min, first_min)
                for i in range(int(minutes)):
                    m = first_min + timedelta(minutes=i)
                    missing_minute = ProductionInfo.objects.create(
                        hour=datetime.strptime(str(m.hour), "%H").time(),
                        minute=m,
                        item_count=0,
                        line=ProductionLine.objects.filter(id=request.data['line'])[0],
                        shift=Shift.objects.filter(id=request.data['shift'])[0],
                    )
                    missing_minute.save()

            def determine_fill_bars(beginning, ending):
                result = []

                hours = (ending.hour - beginning.hour)

                result.append([beginning, datetime.combine(date.today(),
                                                           datetime.strptime(str(beginning.hour + 1),
                                                                             "%H").time()) - timedelta(minutes=1)])

                for i in range(1, hours):
                    result.append(
                        [datetime.combine(date.today(), datetime.strptime(str(beginning.hour + i), "%H").time()),
                         datetime.combine(date.today(),
                                          datetime.strptime(str(beginning.hour + i + 1), "%H").time()) - timedelta(
                             minutes=1)]
                    )

                result.append([datetime.combine(date.today(), datetime.strptime(str(ending.hour), "%H").time()), ending])

                return result

            if on_time:
                check_rate()
            else:
                # FILL GAP
                s = prev_minute + timedelta(minutes=1)
                e = this_minute - timedelta(minutes=1)

                # CHECK IF IT SPANS MULTIPLE HOURS
                if s.hour != e.hour:
                    fill_bars = determine_fill_bars(s, e)

                    for bar in fill_bars:
                        long = calculate_length(bar[1], bar[0])
                        new_bar(bar[0].strftime("%H:%M"), bar[1].strftime("%H:%M"), 4, long, 0)

                else:
                    # FILLER BAR
                    long = calculate_length(e, s)
                    new_bar(s.strftime("%H:%M"), e.strftime("%H:%M"), 4, long, 0)

                create_missing_minutes(s, e)

                # THIS BAR
                check_rate()

            new_minute = ProductionInfo.objects.create(
                hour=request.data['hour'],
                minute=request.data['minute'],
                item_count=request.data['item_count'],
                line=ProductionLine.objects.filter(id=request.data['line'])[0],
                shift=Shift.objects.filter(id=request.data['shift'])[0],
            )
            new_minute.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
            shift = request.data['shift']
            total = float(request.data['total'])
            start = request.data['hour']

            rate = Order.objects.get(shift=shift).rate
            line = ProductionLine.objects.get(shift=shift)
            f_min = datetime.strptime(start, "%H:%M:%S")
            end = (datetime.strptime(start, "%H:%M:%S") + timedelta(minutes=59)).time()

            # CREATE NEW BAR
            def new_bar(current_type, length):
                bar_id = start.replace(':', '') + shift
                parts_diff = round(total - rate, 2)

                create_missing_minutes(f_min)

                new = TimelineBar.objects.create(
                    id=bar_id,
                    shift=Shift.objects.get(id=shift),
                    start_time=start,
                    end_time=end,
                    type=current_type,
                    bar_length=length,
                    parts_made=total,
                    hour=start,
                    loss=parts_diff,
                )
                new.save()

            def create_missing_minutes(first_min):
                for i in range(int(60)):
                    m = first_min + timedelta(minutes=i)
                    missing_minute = ProductionInfo.objects.create(
                        hour=datetime.strptime(str(m.hour), "%H").time(),
                        minute=m,
                        item_count=round(total/60.0, 2),
                        line=line,
                        shift=Shift.objects.get(id=request.data['shift']),
                    )
                    missing_minute.save()

            if total >= rate:
                new_bar(1, 60)
            elif rate > total > 0:
                new_bar(2, 60)
            elif total == 0:
                new_bar(3, 60)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductStatisticsView(generics.ListAPIView):
    # permission_classes = ([IsAuthenticated])

    def get_queryset(self):
        queryset = Shift.objects.all()
        period = self.request.query_params.get('period')
        area = self.request.query_params.get('area')

        if period is not None and area is not None:
            queryset = determine_period(period, area, queryset)
            return queryset.exclude(total_parts__exact=0)

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
                                    for shift in queryset:
                                        if shift.order.values()[0]['product_id'] in product.values():
                                            good = list(product.values())[2] + shift.total_parts
                                            bad = list(product.values())[3] + shift.total_scrap
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
                                    for shift in queryset:
                                        good = list(x.values())[1] + shift.total_parts
                                        bad = list(x.values())[2] + shift.total_scrap
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
                                    for shift in queryset:
                                        if shift.order.values()[0]['product_id'] == list(product.values())[0]:
                                            product.update({'runs': list(product.values())[2] + 1})

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
                                    for shift in queryset:
                                        if shift.order.values()[0]['product_id'] == list(product.values())[0]:
                                            parts = parts + (shift.total_parts-shift.total_scrap)
                                            minutes = minutes + shift.active_minutes
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