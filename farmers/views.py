from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render,redirect
from fponsuppliers.models import *
from django.http import HttpResponseServerError
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import check_password,make_password
from django.contrib.auth import authenticate
from rest_framework_simplejwt.exceptions import TokenError
from django.utils import timezone
from django.shortcuts import get_object_or_404
from fponsuppliers.backends import *
import traceback
import pandas as pd
from .serializers import *
from .models import *

#####################################################----JWT TOknes-----------#######################################
def create_user_token(user, user_type):
    refresh = RefreshToken.for_user(user)
    refresh['user_type'] = user_type
    print(f"Created token for user type: {user_type}")
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
####################-------------------------------------Farmer Login----------------###########################
class FarmerLogin(APIView):
    permission_classes = [AllowAny]
    def post(self, request, format=None):
        user_type = request.data.get('user_type')
        mobile = request.data.get('mobile')
        ip_address = request.META.get('REMOTE_ADDR')
        print(f"Login attempt with mobile: {mobile}, user_type: {user_type}, IP address: {ip_address}")
        try:
            user = CustomUser.objects.filter(mobile=mobile, user_type=user_type).first()
            if user:
                    tokens = create_user_token(user, user_type)
                    self.update_user_info(user, user_type, ip_address)
                    return Response({
                        'message': "User Logged in Successfully",
                        'tokens': tokens
                    }, status=status.HTTP_200_OK)
            else:
                serializer = LoginSerializer(data=request.data)
                if serializer.is_valid():
                    related_user = serializer.create_user(serializer.validated_data, user_type)
                    tokens = create_user_token(related_user, user_type)
                    self.update_user_info(related_user, user_type, ip_address, is_new=True)
                    return Response({
                        'message': 'User created and logged in successfully',
                        'tokens': tokens
                    }, status=status.HTTP_201_CREATED)
                print(f"Registration failed with errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return Response({'error': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update_user_info(self, user, user_type, ip_address, is_new=False):
        if user_type == 'farmer':
            farmer = get_object_or_404(FarmerProfile, user=user)
            farmer.ip_address = ip_address
            if is_new:
                farmer.created_by = user
                farmer.created_at = timezone.now()
            farmer.last_updated_by = user
            farmer.last_updated_at = timezone.now()
            farmer.save()
#############----------------------Farmer Logout---------------------##################
class FarmerLogout(APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            print(f"Logout attempt with refresh token: {refresh_token}")
            print(f"Token payload: {token.payload}")
            user_type = token.payload.get('user_type')

            if user_type not in ['farmer']:
                return Response({"error": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST)

            token.blacklist()
            return Response({"message": "Successfully logged out"}, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            print("Token error encountered during logout")
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)