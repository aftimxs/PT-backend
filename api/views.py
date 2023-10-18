from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import *
from django.db.models import Prefetch
from rest_framework import generics
from django.contrib.auth.models import User


from rest_framework_simplejwt.views import TokenObtainPairView


# Create your views here.
class ShiftView(viewsets.ModelViewSet):
    serializer_class = ShiftSerializer
    queryset = Shift.objects.all()
    permission_classes = ([IsAuthenticated])


class ProductionLineView(viewsets.ModelViewSet):
    serializer_class = ProductionLineSerializer
    permission_classes = ([IsAuthenticated])

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


class TestView(generics.CreateAPIView):
    serializer_class = ProductionInfoSerializer
    permission_classes = ([IsAuthenticated])

    def post(self, request, *args, **kwargs):
        shift = request.data['shift']
        previous_bar = TimelineBar.objects.filter(shift=shift)
        print(previous_bar)

        return Response('hi')
