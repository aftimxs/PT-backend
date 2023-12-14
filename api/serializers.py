from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework import serializers
from .models import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password

from datetime import date, datetime, timedelta, time

from .helper_functions import match_area_rate, calculate_rates_per_hour, order_validate


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class StatsSerializer(serializers.ModelSerializer):

    def update(self, instance, validated_data):
        stats_id = validated_data.get('id', instance.id)
        order = validated_data.get('order', instance.order)
        scrap = validated_data.get('scrap')

        if 'scrap' in validated_data and order:
            if scrap < instance.bars_scrap:
                raise serializers.ValidationError({"message": f"Invalid amount (min: {instance.bars_scrap})"})
            if scrap > instance.made:
                raise serializers.ValidationError({"message": f"Invalid amount (max: {instance.made})"})

            shift_stats = Stats.objects.get(shift__order__stats__id=stats_id)
            if instance.scrap:
                difference = scrap - instance.scrap
                shift_stats.scrap = shift_stats.scrap + difference
            else:
                shift_stats.scrap = shift_stats.scrap + scrap
            shift_stats.save()

        # list of fields in validated data
        update_fields = [k for k in validated_data]
        # update the data on those fields
        for k, v in validated_data.items():
            setattr(instance, k, v)

        instance.save(update_fields=update_fields)
        return instance

    class Meta:
        model = Stats
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    stats = StatsSerializer(many=True, read_only=True)

    has_data = serializers.SerializerMethodField()

    def get_has_data(self, obj):
        return obj.has_data

    def create(self, validated_data):
        product = validated_data.get('product')
        line = validated_data.get('line')
        shift = validated_data.get('shift')
        quantity = validated_data.get('quantity')
        start = validated_data.get('start')
        end = validated_data.get('end')

        order_validate(quantity, start, end, shift)
        validated_data = match_area_rate(line.area, validated_data, product)

        # get the rates for each hour
        start_time = datetime.combine(date.today(), start)
        if end.hour == 0:
            end_time = datetime.combine(date.today() + timedelta(days=1), end)
        else:
            end_time = datetime.combine(date.today(), end)

        hours = (end_time - start_time).total_seconds() / 3600.0

        if shift.rate_per_hour:
            rates = shift.get_rates()
        else:
            rates = {}
        for i in range(int(hours)):
            rates[(start_time + timedelta(hours=i)).strftime('%H:%M:%S')] = validated_data.get('rate')
        shift.set_rates(rates)

        # set ref line
        if shift.reference_line:
            ref = shift.get_reference_line()
        else:
            ref = []
        ref.append({'x': start.strftime('%H:%M:%S'), 'y': round(validated_data.get('rate') / 60.0, 2)})
        ref.append({'x': end.strftime('%H:%M:%S'), 'y': round(validated_data.get('rate') / 60.0, 2)})
        shift.set_reference_line(ref)

        # update shift total quantity
        shift.quantity = shift.quantity + quantity

        # update shift items
        if shift.items:
            x = shift.get_items()
            x.append(product.part_num)
            shift.set_items(x)
        else:
            shift.set_items([product.part_num])

        if end.hour == 0:
            validated_data.update(end=time(23, 59))

        shift.save()
        order = Order.objects.create(**validated_data)
        stats = Stats.objects.create(
            order=order
        )
        stats.save()
        return order

    def update(self, instance, validated_data):
        product = validated_data.get('product')
        quantity = validated_data.get('quantity')
        start = validated_data.get('start')
        end = validated_data.get('end')
        shift = validated_data.get('shift', instance.shift)

        order_validate(quantity, start, end, shift, order_id=instance.id)

        if start != instance.start or end != instance.end:
            calculate_rates_per_hour(start, end, instance, shift, instance.rate, True)

        if product != instance.product:
            line = validated_data.get('line', instance.line)
            validated_data = match_area_rate(line.area, validated_data, product)

            x = shift.get_items()
            index = x.index(instance.product.part_num)
            x[index] = product.part_num
            shift.set_items(x)

            calculate_rates_per_hour(start, end, instance, shift, validated_data.get('rate'), False)

        if quantity != instance.quantity:
            difference = quantity - instance.quantity
            shift.quantity = shift.quantity + difference

        shift.save()

        if end.hour == 0:
            validated_data.update(end=time(23, 59))
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


class ScrapSerializer(serializers.ModelSerializer):

    def update(self, instance, validated_data):
        scrap_id = validated_data.get('id')
        pieces = validated_data.get('pieces')

        bar_hour = instance.bar.hour

        if pieces:
            if pieces > instance.bar.parts_made:
                raise serializers.ValidationError({"message": f"Invalid amount (max: {instance.bar.parts_made})"})

            shift_to_update = Stats.objects.get(shift__scrap__id=scrap_id)
            order_to_update = Stats.objects.get(order__shift__scrap__id=scrap_id, order__start__lte=bar_hour,
                                                order__end__gte=bar_hour)
            if instance.pieces:
                difference = pieces - instance.pieces
                # shift
                shift_to_update.scrap = shift_to_update.scrap + difference
                shift_to_update.bars_scrap = shift_to_update.bars_scrap + difference
                # order
                order_to_update.scrap = order_to_update.scrap + difference
                order_to_update.bars_scrap = order_to_update.bars_scrap + difference
            else:
                # shift
                shift_to_update.scrap = shift_to_update.scrap + pieces
                shift_to_update.bars_scrap = shift_to_update.bars_scrap + pieces
                # order
                order_to_update.scrap = order_to_update.scrap + pieces
                order_to_update.bars_scrap = order_to_update.bars_scrap + pieces
            shift_to_update.save()
            order_to_update.save()

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


class ProductionInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionInfo
        fields = '__all__'


class TimelineBarSerializer(serializers.ModelSerializer):
    bar_comments = BarCommentsSerializer(many=True, read_only=True)
    scrap = ScrapSerializer(many=True, read_only=True)
    minutes = ProductionInfoSerializer(many=True, read_only=True)

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
    stats = StatsSerializer(many=True, read_only=True)

    active = serializers.SerializerMethodField()
    passed = serializers.SerializerMethodField()
    has_data = serializers.SerializerMethodField()

    def create(self, validated_data):
        number = validated_data.get('number')
        date = validated_data.get('date')

        if (timezone.now()-timedelta(hours=8)).date() >= date:
            match number:
                case 1:
                    if (timezone.now()-timedelta(hours=8)).hour > 10:
                        raise serializers.ValidationError({"number": "Unavailable"})
                case 2:
                    if (timezone.now() - timedelta(hours=8)).hour > 21:
                        raise serializers.ValidationError({"number": "Unavailable"})

        shift = Shift.objects.create(**validated_data)
        stats = Stats.objects.create(
            shift=shift
        )
        stats.save()
        return shift

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


class CalendarLineSerializer(serializers.Serializer):
    days = serializers.ListField(child=serializers.CharField(max_length=20))


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


class GraphMinutesAxisSerializer(serializers.Serializer):
    x = serializers.TimeField()
    y = serializers.FloatField()
    product = serializers.CharField(max_length=25, allow_null=True)


class GraphMinutesSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=20)
    color = serializers.CharField(max_length=25)
    data = GraphMinutesAxisSerializer(many=True, read_only=True)
