from rest_framework import mixins, generics
from rest_framework.response import Response
from rest_framework import status

from webapi import models
from webapi.Utils import Serializers, Permissions

from django.db.models import Q

class UserView(generics.GenericAPIView,
               mixins.RetrieveModelMixin,
               mixins.UpdateModelMixin):

    permission_classes = (Permissions.PeopleAllReadOwnerModify, )
    queryset = models.user_info.objects.all()
    serializer_class = Serializers.UserSerializer
    lookup_field = 'user_id'

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    
class FriendsView(mixins.ListModelMixin,
                  mixins.DestroyModelMixin,
                  generics.GenericAPIView):

    permission_classes = (Permissions.AllAddFriendOwnerReadDeletePermission,)
    queryset = models.friends.objects.all()
    serializer_class = Serializers.FriendsSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        current_user_id = request.user.user_id
        friend_user_id = self.kwargs['friend_id']
        models.friends.objects.filter(user_id=current_user_id, friend_id=friend_user_id).delete()
        models.friends.objects.filter(friend_id=current_user_id, user_id=friend_user_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def post(self, request, *args, **kwargs):
        current_user_id = request.user.user_id
        requested_user_id = self.kwargs['user_id']
        approve = models.friends.objects.filter(user_id=requested_user_id, friend_id=current_user_id).count()
        if approve > 0:
            r1 = models.friends.objects.get_or_create(user_id=requested_user_id, friend_id=current_user_id)[0]
            r1.status = 1
            r2 = models.friends.objects.get_or_create(friend_id=requested_user_id, user_id=current_user_id)[0]
            r2.status = 1
            r1.save()
            r2.save()
        else:
            models.friends.objects.create(user_id=current_user_id, friend_id=requested_user_id, status=0)
            
        return Response(status=status.HTTP_201_CREATED)
    
    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        scope = self.kwargs["scope"]
        if scope == "requests":
            return models.friends.objects.filter(friend_id=user_id, status=0)
        elif scope == "friends":
            return models.friends.objects.filter(user_id=user_id, status__gt=0)
        else :
            request = Q(friend_id=user_id, status=0)
            friends = Q(user_id=user_id, status__gt=0)
            return models.friends.objects.filter(request | friends)

class ActivitiesView(generics.GenericAPIView,
                     mixins.ListModelMixin,
                     mixins.CreateModelMixin):
    
    permission_classes = (Permissions.PeopleFriendReadOwnerModify, )
    serializer_class = Serializers.ActivitySerializer
    lookup_field = 'activity_id'
    createScope = ['access', 'type', 'status', 'description', 'longitude', 'latitude', 'destination', 'keyword', 'start_date', 'end_date']
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
    
    def pre_valid_model(self, serializer, model):
        model.creator_id = self.request.user.user_id
    
    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        return models.activities.objects.filter(creator=user_id)
