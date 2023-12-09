from django.contrib import admin
from .models import *


class ShiftAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'date', 'line')


class ProductionLineAdmin(admin.ModelAdmin):
    list_display = ('id', 'area', 'cell')


class MachineAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'make', 'machine_model', 'serial', 'line')


class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'part_num', 'rate', 'pleating_rate', 'autobag_rate', 'molding_rate')


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'quantity', 'rate', 'line', 'shift', 'product', 'start', 'end')


class OperatorAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'worker_number', 'full_name')


class ScrapAdmin(admin.ModelAdmin):
    list_display = ('id', 'reason', 'pieces', 'comments', 'bar', 'shift')


class DowntimeAdmin(admin.ModelAdmin):
    list_display = ('id', 'shift', 'reason', 'description', 'start', 'end')


class SpeedlossAdmin(admin.ModelAdmin):
    list_display = ('id', 'shift', 'reason', 'description', 'start', 'end')


class ProductionInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'hour', 'minute', 'item_count', 'line', 'shift')


class TimelineBarAdmin(admin.ModelAdmin):
    list_display = ('id', 'shift', 'start_time', 'end_time', 'type', 'bar_length', 'parts_made')


class BarCommentsAdmin(admin.ModelAdmin):
    list_display = ('id', 'reason', 'comments', 'bar')


class StatsAdmin(admin.ModelAdmin):
    list_display = ('id', 'made', 'scrap', 'bars_scrap', 'total_slow', 'minutes_slow', 'loss_slow', 'total_stopped', 'minutes_stopped', 'loss_stopped', 'shift', 'order')


# Register your models here.
admin.site.register(Shift, ShiftAdmin)
admin.site.register(ProductionLine, ProductionLineAdmin)
admin.site.register(Machine, MachineAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Operator, OperatorAdmin)
admin.site.register(Scrap, ScrapAdmin)
admin.site.register(Downtime, DowntimeAdmin)
admin.site.register(Speedloss, SpeedlossAdmin)
admin.site.register(ProductionInfo, ProductionInfoAdmin)
admin.site.register(TimelineBar, TimelineBarAdmin)
admin.site.register(BarComments, BarCommentsAdmin)
admin.site.register(Stats, StatsAdmin)
