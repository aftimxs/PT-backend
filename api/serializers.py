from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework import serializers
from .models import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password

from .helper_functions import match_area_rate


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        product = validated_data.get('product')
        line = validated_data.get('line')

        validated_data = match_area_rate(line.area, validated_data, product)

        return Order.objects.create(**validated_data)

    def update(self, instance, validated_data):
        product = validated_data.get('product')

        if product != instance.product:
            line = validated_data.get('line')
            validated_data = match_area_rate(line.area, validated_data, product)

        # list of fields in validated data
        update_fields = [k for k in validated_data]
        # update the data on those fields
        for k, v in validated_data.items():
            setattr(instance, k, v)

        instance.save(update_fields=update_fields)
        return instance

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

    def update(self, instance, validated_data):
        scrap_id = validated_data.get('id')
        pieces = validated_data.get('pieces')

        if pieces:
            shift_to_update = Shift.objects.get(scrap__id=scrap_id)
            if instance.pieces:
                difference = pieces - instance.pieces
                shift_to_update.total_scrap = shift_to_update.total_scrap + difference
                shift_to_update.bars_scrap = shift_to_update.bars_scrap + difference
            else:
                shift_to_update.total_scrap = shift_to_update.total_scrap + pieces
                shift_to_update.bars_scrap = shift_to_update.bars_scrap + pieces
            shift_to_update.save()

        # remove id because its PK
        validated_data.pop('id', None)
        # list of scrap fields in validated data
        update_fields = [k for k in validated_data]
        # update the data on those fields
        for k, v in validated_data.items():
            setattr(instance, k, v)
        # update has scrap on timeline Bar
        setattr(instance.bar, 'has_scrap', True)
        # save everything
        instance.bar.save(update_fields=['has_scrap'])
        instance.save(update_fields=update_fields)
        return instance

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


class BarCommentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarComments
        fields = '__all__'


class TimelineBarSerializer(serializers.ModelSerializer):
    bar_comments = BarCommentsSerializer(many=True, read_only=True)
    scrap = ScrapSerializer(many=True, read_only=True)

    header = serializers.SerializerMethodField()
    background = serializers.SerializerMethodField()

    def get_header(self, obj):
        match obj.type:
            case 1:
                return 'Good Rate'
            case 2:
                return 'Speed Loss'
            case 3:
                return 'Downtime'

    def get_background(self, obj):
        match obj.type:
            case 1:
                return '#198754'
            case 2:
                return '#ffc107'
            case 3:
                return '#dc3545'
            case 4:
                return 'rgb(61,61,61)'

    class Meta:
        model = TimelineBar
        fields = '__all__'


class ShiftSerializer(serializers.ModelSerializer):
    order = OrderSerializer(many=True, read_only=True)
    operator = OperatorSerializer(many=True, read_only=True)
    info = ProductionInfoSerializer(many=True, read_only=True)
    scrap = ScrapSerializer(many=True, read_only=True)
    timelineBar = TimelineBarSerializer(many=True, read_only=True)

    active = serializers.SerializerMethodField()
    passed = serializers.SerializerMethodField()
    has_data = serializers.SerializerMethodField()

    class Meta:
        model = Shift
        fields = '__all__'

    def get_active(self, obj):
        return obj.active

    def get_passed(self, obj):
        return obj.passed

    def get_has_data(self, obj):
        return obj.has_data


class ShiftOnlyOrderSerializer(serializers.ModelSerializer):
    order = OrderSerializer(many=True, read_only=True)

    active = serializers.SerializerMethodField()
    passed = serializers.SerializerMethodField()
    has_data = serializers.SerializerMethodField()

    class Meta:
        model = Shift
        fields = '__all__'

    def get_active(self, obj):
        return obj.active

    def get_passed(self, obj):
        return obj.passed

    def get_has_data(self, obj):
        return obj.has_data


class ProductionLineSerializer(serializers.ModelSerializer):
    machine = MachineSerializer(many=False, read_only=True)
    scrap = ScrapSerializer(many=True, read_only=True)
    shift = ShiftSerializer(many=True, read_only=True)

    class Meta:
        model = ProductionLine
        fields = '__all__'


class ProductionLineOnlyShiftSerializer(serializers.ModelSerializer):
    shift = ShiftOnlyOrderSerializer(many=True, read_only=True)

    class Meta:
        model = ProductionLine
        fields = '__all__'


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email

        return token


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
                str(user.is_active) + str(user.pk) + str(timestamp)
        )


email_verification_token = EmailVerificationTokenGenerator()


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="Email already exists!")]
    )

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            is_active=False
        )

        user.set_password(validated_data['password'])
        user.save()

        return user


class ConstrainedDictField(serializers.DictField):
    def to_internal_value(self, data):
        # Perform validation on the keys of the dictionary here
        if set(data.keys()) != {"area", "cell", "shift"}:
            raise serializers.ValidationError("Invalid keys for dictionary.")

        return super().to_internal_value(data)


class ExtendedPropsSerializer(serializers.Serializer):
    area = serializers.CharField(max_length=20)
    cell = serializers.IntegerField()
    shift = ShiftOnlyOrderSerializer(many=False, read_only=True)


class CalendarShiftSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=50)
    title = serializers.CharField(max_length=50)
    date = serializers.DateField()
    allDay = serializers.BooleanField()
    editable = serializers.BooleanField()
    backgroundColor = serializers.CharField(max_length=10)
    borderColor = serializers.CharField(max_length=10)
    extendedProps = ExtendedPropsSerializer(many=False, read_only=True)


class CalendarDayShiftSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=50)
    area = serializers.CharField(max_length=20)
    cell = serializers.IntegerField()
    shift = ShiftOnlyOrderSerializer(many=False, read_only=True)


class ChartsExtraInfoSerializer(serializers.Serializer):
    keys = serializers.ListField(child=serializers.CharField(max_length=30))
    index_by = serializers.ListField(child=serializers.CharField(max_length=30))
    color = serializers.ListField(child=serializers.CharField(max_length=30))
    legend_x = serializers.CharField(max_length=20)
    legend_y = serializers.CharField(max_length=20)
    group_mode = serializers.CharField(max_length=20, allow_null=True)
    title = serializers.CharField(max_length=30)
    subtitle = serializers.CharField(max_length=50)


class PartsMadeSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product = serializers.CharField()
    good = serializers.IntegerField()
    scrap = serializers.IntegerField()
    good_percentage = serializers.FloatField()


class TotalPartsMadeDailySerializer(serializers.Serializer):
    day = serializers.DateField()
    good = serializers.IntegerField()
    scrap = serializers.IntegerField()
    good_percentage = serializers.FloatField()


class TotalPartsMadeWeeklySerializer(serializers.Serializer):
    week = serializers.IntegerField()
    good = serializers.IntegerField()
    scrap = serializers.IntegerField()
    good_percentage = serializers.FloatField()


class TotalPartsMadeMonthlySerializer(serializers.Serializer):
    month = serializers.IntegerField()
    good = serializers.IntegerField()
    scrap = serializers.IntegerField()
    good_percentage = serializers.FloatField()


class AccumulatedTotalParts(serializers.Serializer):
    product = serializers.CharField(max_length=10)
    good = serializers.IntegerField()
    scrap = serializers.IntegerField()
    good_percentage = serializers.FloatField()


class PartsMadeByLineSerializer(serializers.Serializer):
    line = serializers.CharField(max_length=10)
    item_count = serializers.IntegerField()


class ProductTimesRunSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product = serializers.CharField()
    runs = serializers.IntegerField()


class ProductActualRateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product = serializers.CharField()
    expected = serializers.FloatField()
    actual = serializers.FloatField()
    shift_count = serializers.IntegerField()


class TotalHourSerializer(serializers.Serializer):
    shift = ShiftSerializer(many=False, read_only=True)
    total = serializers.IntegerField()
    hour = serializers.TimeField()
