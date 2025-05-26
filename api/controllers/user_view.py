from rest_framework import viewsets, status
from rest_framework.response import Response

from base.models import UserModel

from api.serializers import UserModelSerializer

class UserViewSet(viewsets.ViewSet):
    def list(self, request):
        """
        Retrieve all UserModel records.
        GET /api/user
        """
        users = UserModel.objects.all()
        serializer = UserModelSerializer(users, many=True)
        return Response(serializer.data)