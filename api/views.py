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

        if area is not None and cell is not None and date is not None and number is not None:
            queryset = (queryset.filter(area=area, cell=cell).
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
    permission_classes = ([IsAuthenticated])


class ScrapView(viewsets.ModelViewSet):
    serializer_class = ScrapSerializer
    permission_classes = ([IsAuthenticated])

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
    queryset = TimelineBar.objects.all()


class TestView(generics.CreateAPIView):
    serializer_class = ProductionInfoSerializer

    # permission_classes = ([IsAuthenticated])

    def post(self, request, *args, **kwargs):
        # REQUEST DATA
        shift = request.data['shift']
        parts = float(request.data['item_count'])
        minute = request.data['minute']

        # DB DATA
        previous_bar = TimelineBar.objects.filter(shift=shift).values().last()
        rate = Order.objects.filter(shift=shift).values('product__rate')[0]['product__rate']

        # DATA FOR BAR TYPE
        minute_rate = rate / 60

        if previous_bar:
            prev_type = previous_bar['type']
            prev_id = previous_bar['id']
        else:
            prev_type = 0
            prev_id = None

        # CREATE NEW BAR
        def new_bar(start, end, current_type, length, part_count):
            bar_id = start.replace(':', '') + shift

            new = TimelineBar.objects.create(
                id=bar_id,
                shift=Shift.objects.filter(id=shift)[0],
                start_time=start,
                end_time=end,
                type=current_type,
                bar_length=length,
                parts_made=part_count,
            )
            new.save()

        def check_color(current_type):
            if current_type != prev_type or current_type == 1 or this_minute.hour != prev_minute.hour or not on_time:
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

        this_minute = datetime.combine(date.today(), datetime.strptime(minute, "%H:%M").time())
        prev_minute = datetime.combine(date.today(), previous_bar['end_time'])

        on_time = this_minute == prev_minute + timedelta(minutes=1)

        def x(first, second):
            return [datetime.combine(date.today(), datetime.strptime(str(second.hour), "%H").time()),
                    datetime.combine(date.today(), datetime.strptime(str(second.hour), "%H").time())-timedelta(minutes=1)]

        if on_time:
            check_rate()
        else:
            # FILL GAP
            s = prev_minute + timedelta(minutes=1)
            e = this_minute - timedelta(minutes=1)

            # CHECK IF IT SPANS MULTIPLE HOURS
            if s.hour != e.hour:
                new_start = datetime.combine(date.today(), datetime.strptime(str(e.hour), "%H").time())
                new_end = new_start - timedelta(minutes=1)

                # FILLER BAR 1
                long = calculate_length(new_end, s)
                new_bar(s.strftime("%H:%M"), new_end.strftime("%H:%M"), 4, long, 0)

                # FILLER BAR 2
                long2 = calculate_length(e, new_start)
                new_bar(new_start.strftime("%H:%M"), e.strftime("%H:%M"), 4, long2, 0)
            else:
                # FILLER BAR
                long = calculate_length(e, s)
                new_bar(s.strftime("%H:%M"), e.strftime("%H:%M"), 4, long, 0)

            # THIS BAR
            check_rate()

        return Response('hi')
