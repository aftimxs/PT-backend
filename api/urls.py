from django.urls import path, include
from rest_framework import routers

from . import views
from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from api.views import MyTokenObtainPairView, RegisterView, TestView


router = routers.DefaultRouter()
router.register(r'shift', views.ShiftView, 'shift')
router.register(r'production-line', views.ProductionLineView, 'production-line')
router.register(r'machine', views.MachineView, 'machine')
router.register(r'product', views.ProductView, 'product')
router.register(r'order', views.OrderView, 'order')
router.register(r'operator', views.OperatorView, 'operator')
router.register(r'product-info', views.ProductionInfoView, 'product-info')
router.register(r'scrap', views.ScrapView, 'scrap')
router.register(r'downtime', views.DowntimeView, 'downtime')
router.register(r'speedloss', views.SpeedlossView, 'speedloss')
router.register(r'timeline-bars', views.TimelineBarView, 'timeline-bars')
router.register(r'comments', views.BarCommentsView, 'comments')


urlpatterns = [
    path('', include(router.urls)),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('test/', TestView.as_view(), name='test')
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
