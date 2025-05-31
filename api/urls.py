from rest_framework.routers import DefaultRouter

from .controllers import *

router = DefaultRouter(trailing_slash="")  # No trailing slash
router.register(r"user", UserViewSet, "user")
router.register(r"product", ProductViewSet, "product")
router.register(r"inventory", InventoryViewSet, "inventory")

urlpatterns = router.urls
