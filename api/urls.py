from rest_framework.routers import DefaultRouter
from .controllers import *

router = DefaultRouter()  # Use default, includes trailing slashes
router.register(r"user", UserViewSet, "user")
router.register(r"product", ProductViewSet, "product")
router.register(r"inventory", InventoryViewSet, "inventory")
router.register(r"order", OrderViewSet, "order")
router.register(r"category", CategoryViewSet, "category")

urlpatterns = router.urls
