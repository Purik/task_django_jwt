from rest_framework import routers

from .endpoints import OTPEndpoint


router = routers.DefaultRouter()
router.register('otp', OTPEndpoint, basename='otp')
