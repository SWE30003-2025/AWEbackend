from rest_framework.routers import DefaultRouter
from .controllers.order_view import OrderViewSet
from .controllers import *

router = DefaultRouter()  # Use default, includes trailing slashes
router.register(r"user", UserViewSet, "user")
router.register(r"product", ProductViewSet, "product")
router.register(r"inventory", InventoryViewSet, "inventory")
router.register(r"order", OrderViewSet, "order")

urlpatterns = router.urls
