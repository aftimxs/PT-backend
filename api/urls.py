from django.urls import path, include
from rest_framework import routers

from . import views
from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from api.views import (MyTokenObtainPairView, RegisterView, MinutesView, ProductStatisticsView, LineStatisticsView,
                       HourTotalPostView, MinutesForGraphView, CalendarLineLookupView)


router = routers.DefaultRouter()
router.register(r'shift', views.ShiftView, 'shift')
router.register(r'shortShift', views.ShortShiftView, 'shortShift')
router.register(r'production-line', views.ProductionLineView, 'production-line')
router.register(r'machine', views.MachineView, 'machine')
router.register(r'product', views.ProductView, 'product')
router.register(r'order', views.OrderView, 'order')
router.register(r'operator', views.OperatorView, 'operator')
router.register(r'scrap', views.ScrapView, 'scrap')
router.register(r'downtime', views.DowntimeView, 'downtime')
router.register(r'speedloss', views.SpeedlossView, 'speedloss')
router.register(r'timeline-bars', views.TimelineBarView, 'timeline-bars')
router.register(r'comments', views.BarCommentsView, 'comments')
router.register(r'calendar', views.CalendarLookupView, 'calendar')
router.register(r'calendar-day', views.CalendarDayLookupView, 'calendar-day')
router.register(r'stats', views.StatsView, 'stats')


urlpatterns = [
    path('', include(router.urls)),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('product-info/', MinutesView.as_view(), name='product-info'),
    path('hour-post/', HourTotalPostView.as_view(), name='hour-post'),
    path('statistics/products', ProductStatisticsView.as_view(), name='products-stats'),
    path('statistics/lines', LineStatisticsView.as_view(), name='line-stats'),
    path('graph-minutes', MinutesForGraphView.as_view(), name='graph-minutes'),
    path('calendar-line', CalendarLineLookupView.as_view(), name='line-calendar'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
