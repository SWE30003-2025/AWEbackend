from rest_framework import viewsets
from rest_framework.response import Response

from api.serializers import CategoryModelSerializer

from base.models import CategoryModel

class CategoryViewSet(viewsets.ViewSet):
    def list(self, request):
        """
        GET /api/category/
        Returns all categories as a flat list.
        """
        queryset = CategoryModel.objects.all().order_by("name")
        serializer = CategoryModelSerializer(queryset, many=True)

        return Response(serializer.data)
