from rest_framework import serializers
from .models import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = '__all__'


class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = '__all__'


class OperatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operator
        fields = '__all__'


class ProductionInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionInfo
        fields = '__all__'


class ScrapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scrap
        fields = '__all__'


class DowntimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Downtime
        fields = '__all__'


class SpeedlossSerializer(serializers.ModelSerializer):
    class Meta:
        model = Speedloss
        fields = '__all__'


class ShiftSerializer(serializers.ModelSerializer):
    order = OrderSerializer(many=True, read_only=True)
    operator = OperatorSerializer(many=True, read_only=True)
    info = ProductionInfoSerializer(many=True, read_only=True)
    downtime = DowntimeSerializer(many=True, read_only=True)
    speedloss = SpeedlossSerializer(many=True, read_only=True)
    scrap = ScrapSerializer(many=True, read_only=True)

    class Meta:
        model = Shift
        fields = '__all__'


class ProductionLineSerializer(serializers.ModelSerializer):
    machine = MachineSerializer(many=False, read_only=True)
    scrap = ScrapSerializer(many=True, read_only=True)
    shift = ShiftSerializer(many=True, read_only=True)

    class Meta:
        model = ProductionLine
        fields = '__all__'


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = '__all__'


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email

        return token
