from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import *
from django.db.models import Prefetch
from rest_framework import generics
from django.contrib.auth.models import User

from rest_framework_simplejwt.views import TokenObtainPairView

import datetime
import time


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
        shift_date = getattr(Shift.objects.get(id=shift), 'date')

        # DATA FOR BAR TYPE
        minute_rate = rate / 60
        prev_type = previous_bar['type']
        prev_id = previous_bar['id']

        def check_color(current_type):
            if current_type != prev_type or current_type == 1:

                # DATE AND ID FORMATTING
                split_minute = minute.split(':')
                bar_datetime = datetime.datetime.combine(shift_date,
                                                         datetime.time(int(split_minute[0]), int(split_minute[1])))
                bar_id = bar_datetime.strftime("%d%m%y%H%M") + shift

                # CREATE NEW BAR
                new_bar = TimelineBar.objects.create(
                    id=bar_id,
                    shift=Shift.objects.filter(id=shift)[0],
                    start_time=minute,
                    end_time=minute,
                    type=current_type,
                    bar_length=1,
                    parts_made=parts,
                )
                new_bar.save()
            else:
                # UPDATE PREVIOUS BAR
                bar_to_update = TimelineBar.objects.get(id=prev_id)
                bar_to_update.end_time = minute
                bar_to_update.bar_length = bar_to_update.bar_length + 1
                bar_to_update.parts_made = bar_to_update.parts_made + parts
                bar_to_update.save()

        if parts >= minute_rate:
            check_color(1)
        elif minute_rate > parts > 0:
            check_color(2)
        elif parts == 0:
            check_color(3)

        return Response('hi')
