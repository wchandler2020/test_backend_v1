from dotenv import load_dotenv
from django.shortcuts import render
from .otp import get_user_totp_device, login_user, is_verified, IsVerified, get_client_ip
from user.models import User, Profile
from .tableau_utils import fetch_data
from .serializer import (
    UserSerializer,
    MyTokenObtainPairSerializer,
    RegisterUserSerializer,
    ProfileSerializer
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from tableau_api_lib import TableauServerConnection
from tableau_api_lib.utils import querying, flatten_dict_column
import json
import concurrent.futures
import re
from .data import Data
from .get_data import Tableau_Data


load_dotenv()  # take environment variables from .env.
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    def get_token(cls, user):
        token = super().get_token(user)
        


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterUserSerializer


@api_view(['GET'])
def getRoutes(request):
    routes = [
        '/api/token/',
        '/api/register/',
        '/api/token/refresh/',
        '/api/token/logout/',
        '/api/profile-detail/',
        '/api/dashboard/',
        '/api/otp/',
    ]
    return Response(routes)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    if request.method == 'GET':
        # Serialize the user data
        user_serializer = UserSerializer(request.user)
        user_data = user_serializer.data
        response = f'Hi {user_data["username"]} welcome back'
        context = {'user': user_data,'response': response, **user_data}

        return Response(context, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        text = request.data.get('text')
        response = f'Hi, {request.user}, your text is {text}'
        return Response({'response': response}, status=status.HTTP_200_OK)
    return Response({}, status=status.HTTP_400_BAD_REQUEST)

class ProfileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get the profile data for the current user
            profile = request.user.profile
            # Serialize the profile data
            serializer = ProfileSerializer(profile)
            # Return the serialized data as JSON
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            # Handle the case where the profile does not exist for the user
            return Response({"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Handle other exceptions
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class HasOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        device = get_user_totp_device( user)
        if not device:
            return Response(False, status=status.HTTP_200_OK)
        elif device.confirmed == False:
            return Response(False, status=status.HTTP_200_OK)
        return Response(True, status=status.HTTP_200_OK)

class VerifiedView(APIView):
    permission_classes = [IsAuthenticated, IsVerified]

    def get (self, request):
        verified=  is_verified(request, True)
        if verified:
            return Response(True, status=status.HTTP_200_OK)
        return Response(False, status=status.HTTP_200_OK) 

class OTPView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        user = request.user
        device = get_user_totp_device( user)
        if not device:
            device = user.totpdevice_set.create(confirmed=False)
        url = device.config_url
        return Response(url, status=status.HTTP_201_CREATED)



class TOTPVerifyView(APIView):
    permission_classes = (IsAuthenticated,)
    """
    Use this endpoint to verify/enable a TOTP device
    """
    

    def post(self, request, token, format=None):
        user = request.user
        device = get_user_totp_device( user)
        print(get_client_ip(request))
        print(
        request.headers['unique-id'])
        if not device == None and device.verify_token(token):
            if not device.confirmed:
                device.confirmed = True
                device.save()
            login_user(request,device)
            return Response(True, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            token = RefreshToken(refresh_token)
            token.blacklist()
            request.session.flush()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TokenError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TableauDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_serializer = UserSerializer(request.user)
        user_data = user_serializer.data
        client_name = user_data["client_name"]
        tab_data = Tableau_Data()
        data = tab_data.get_tableau_sql_data(client_name)
        chart_data = tab_data.get_chart_data(client_name)
       
        return Response({'client_data': data, 'chart_data_results': chart_data}, status=status.HTTP_200_OK)