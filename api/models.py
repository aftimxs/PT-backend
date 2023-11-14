from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, datetime, timedelta


# Create your models here.
class ProductionLine(models.Model):
    id = models.CharField(primary_key=True, max_length=20)
    area = models.CharField(max_length=15)
    cell = models.IntegerField(null=True)

    # class Meta:
    #     ordering = ['shift__date']


class Product(models.Model):
    part_num = models.CharField(max_length=20, unique=True)
    rate = models.IntegerField()


class Operator(models.Model):
    first_name = models.CharField(max_length=30, null=False)
    last_name = models.CharField(max_length=30, null=False)
    worker_number = models.IntegerField(unique=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ['last_name']


class Shift(models.Model):

    number = [
        (1, 'First'),
        (2, 'Second')
    ]

    status_options = [
        (1, 'success'),
        (2, 'warning'),
        (3, 'danger'),
        (4, 'no info')
    ]

    id = models.CharField(primary_key=True, max_length=50)
    number = models.IntegerField(choices=number, default=1)
    date = models.DateField()
    line = models.ForeignKey(ProductionLine, related_name='shift', default=0, on_delete=models.CASCADE)
    operators = models.ManyToManyField(Operator, blank=True)
    status = models.IntegerField(choices=status_options, default=4)
    total_parts = models.IntegerField(default=0)
    total_scrap = models.IntegerField(default=0)
    total_stopped = models.IntegerField(default=0)
    total_slow = models.IntegerField(default=0)

    @property
    def passed(self):
        if (timezone.now() - timedelta(hours=8)).date() >= self.date:
            return True
        else:
            return False

    @property
    def active(self):
        if int(((timezone.now()-timedelta(hours=8)).date() - self.date).total_seconds()) == 0:
            if self.number == 1 and 6 < (timezone.now()-timedelta(hours=8)).hour < 15:
                return True
            elif self.number == 2 and 17 < (timezone.now()-timedelta(hours=8)).hour < 24:
                return True
            else:
                return False
        else:
            return False

    @property
    def has_data(self):
        if ProductionInfo.objects.filter(shift=self.id):
            return True
        else:
            return False

    class Meta:
        ordering = ['date']


class Machine(models.Model):
    code = models.CharField(max_length=5, unique=True)
    make = models.CharField(max_length=20)
    machine_model = models.CharField(max_length=20)
    serial = models.IntegerField(unique=True)
    line = models.OneToOneField(ProductionLine, related_name='machine', on_delete=models.CASCADE)


class Order(models.Model):
    quantity = models.IntegerField(null=True)
    product = models.ForeignKey(Product, related_name='order', default=1, on_delete=models.CASCADE)
    line = models.ForeignKey(ProductionLine, related_name='orderL', on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, related_name='order',  default=0, on_delete=models.CASCADE)


class ProductionInfo(models.Model):
    hour = models.TimeField(null=True)
    minute = models.TimeField()
    item_count = models.IntegerField()
    line = models.ForeignKey(ProductionLine, related_name='info', default=0, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, related_name='info',  default=0, on_delete=models.CASCADE)

    class Meta:
        ordering = ['minute']


class TimelineBar(models.Model):
    bar_type = [
        (1, 'success'),
        (2, 'warning'),
        (3, 'danger'),
        (4, 'no info')
    ]

    id = models.CharField(primary_key=True, max_length=50)
    shift = models.ForeignKey(Shift, related_name='timelineBar', on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    type = models.IntegerField(choices=bar_type)
    bar_length = models.IntegerField()
    parts_made = models.IntegerField()
    hour = models.TimeField(null=True)
    has_scrap = models.BooleanField(default=False)

    class Meta:
        ordering = ['start_time']


class BarComments(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    reason = models.CharField(max_length=50, null=True)
    comments = models.CharField(max_length=200, null=True)
    bar = models.ForeignKey(TimelineBar, related_name='bar_comments', on_delete=models.CASCADE)


class Scrap(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    pieces = models.IntegerField(null=True)
    reason = models.CharField(max_length=50, null=True)
    comments = models.CharField(max_length=200, null=True)
    bar = models.ForeignKey(TimelineBar, related_name='scrap', on_delete=models.CASCADE, default=None)
    shift = models.ForeignKey(Shift, related_name='scrap', on_delete=models.CASCADE, default=None)


class Downtime(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    shift = models.ForeignKey(Shift, related_name='downtime', on_delete=models.CASCADE)
    reason = models.CharField(max_length=50, null=True)
    description = models.CharField(max_length=150, null=True)
    start = models.TimeField()
    end = models.TimeField()

    class Meta:
        ordering = ['start']


class Speedloss(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    shift = models.ForeignKey(Shift, related_name='speedloss', on_delete=models.CASCADE)
    reason = models.CharField(max_length=50, null=True)
    description = models.CharField(max_length=150, null=True)
    start = models.TimeField()
    end = models.TimeField()

    class Meta:
        ordering = ['start']
