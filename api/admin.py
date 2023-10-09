from django.contrib import admin
from .models import *


class ShiftAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'date', 'line')


class ProductionLineAdmin(admin.ModelAdmin):
    list_display = ('id', 'area', 'cell')


class MachineAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'make', 'machine_model', 'serial', 'line')


class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'part_num', 'rate')


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'quantity', 'line', 'shift', 'product')


class OperatorAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'worker_number', 'full_name')


class ScrapAdmin(admin.ModelAdmin):
    list_display = ('id', 'reason', 'pieces', 'comments', 'shift', 'minute')


class DowntimeAdmin(admin.ModelAdmin):
    list_display = ('id', 'shift', 'reason', 'description', 'start', 'end')


class SpeedlossAdmin(admin.ModelAdmin):
    list_display = ('id', 'shift', 'reason', 'description', 'start', 'end')


class ProductionInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'hour', 'minute', 'item_count', 'line', 'shift')


class UsersAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'password')


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
admin.site.register(Users, UsersAdmin)


