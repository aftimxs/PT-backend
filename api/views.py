from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import *
from django.db.models import Prefetch
from rest_framework import generics
from django.contrib.auth.models import User

from rest_framework_simplejwt.views import TokenObtainPairView

from datetime import date, datetime, timedelta


# Create your views here.
class ShiftView(viewsets.ModelViewSet):
    serializer_class = ShiftSerializer
    queryset = Shift.objects.all()
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
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = ([IsAuthenticated])


class OrderView(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = ([IsAuthenticated])


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


class TestView(generics.ListCreateAPIView):
    serializer_class = ProductionInfoSerializer
    queryset = ProductionInfo.objects.all().order_by('minute')
    # permission_classes = ([IsAuthenticated])

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = ProductionInfoSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        # REQUEST DATA
        shift = request.data['shift']
        parts = float(request.data['item_count'])
        minute = request.data['minute']

        # DB DATA
        previous_bar = TimelineBar.objects.filter(shift=shift).values().last()
        rate = Order.objects.filter(shift=shift).values('product__rate')[0]['product__rate']
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

            new = TimelineBar.objects.create(
                id=bar_id,
                shift=Shift.objects.filter(id=shift)[0],
                start_time=start,
                end_time=end,
                type=current_type,
                bar_length=length,
                parts_made=part_count,
                hour=hour[0]+':00:00'
            )
            new.save()

        def check_color(current_type):
            if current_type != prev_type or this_minute.hour != prev_minute.hour or not on_time:
                new_bar(minute, minute, current_type, 1, parts)
            else:
                # UPDATE PREVIOUS BAR
                bar_to_update = TimelineBar.objects.get(id=prev_id)
                bar_to_update.end_time = minute
                bar_to_update.bar_length = bar_to_update.bar_length + 1
                bar_to_update.parts_made = bar_to_update.parts_made + parts
                bar_to_update.save()

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

        return Response('hi')


class BarCommentsView(viewsets.ModelViewSet):
    queryset = BarComments.objects.all()
    serializer_class = BarCommentsSerializer
    # permission_classes = ([IsAuthenticated])
