from fponsuppliers.models import *
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.mail import send_mail
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from rest_framework_simplejwt.exceptions import TokenError
from django.utils import timezone
from django.shortcuts import get_object_or_404
from fponsuppliers.backends import *
from django.db import transaction
from rest_framework import status
from datetime import timedelta
import traceback
import pandas as pd
from .serializers import *
from .models import *
from .data import *
from django.db import IntegrityError
from fponsuppliers.serializers import *
import random
import requests
import json
#################################################################
class FarmerLogin(APIView):
    permission_classes = [AllowAny]
    def post(self, request, format=None):
        user_type = request.data.get('user_type')
        mobile = request.data.get('mobile')
        email = request.data.get('email')
        login_type = request.data.get('login_type')
        ip_address = request.META.get('REMOTE_ADDR')

        if not user_type or not login_type:
            return Response({'error': 'user_type and login_type are required'}, status=status.HTTP_400_BAD_REQUEST)

        if login_type not in ['email', 'mobile']:
            return Response({'error': 'Invalid login_type'}, status=status.HTTP_400_BAD_REQUEST)

        if login_type == 'email' and not email:
            return Response({'error': 'Email is required for email login'}, status=status.HTTP_400_BAD_REQUEST)

        if login_type == 'mobile' and not mobile:
            return Response({'error': 'Mobile is required for mobile login'}, status=status.HTTP_400_BAD_REQUEST)

        otp = random.randint(100000, 999999)
        print(f"Login attempt with {login_type}: {mobile or email}, user_type: {user_type}, IP address: {ip_address}")
        print(f"\nOtp is {otp}")

        try:
            if login_type == 'email':
                user = CustomUser.objects.filter(email=email, user_type=user_type, email_verified=True).first()
                print(f"User object:{user}")
                is_existing_user = FarmerProfile.objects.filter(user=user).exists() if user else False
                print(f"Is existing Farmer:{is_existing_user}")
                if user:
                    send_otp_via_email(email, otp)
                    store_otp(email, otp)
                    return Response({
                        'message': f"OTP sent successfully to {user.email}",
                        'otp': otp,
                        'is_existing_user': is_existing_user
                    }, status=status.HTTP_200_OK)
                else:
                    send_otp_via_email(email,otp)
                    store_otp(email,otp)
                    return Response({
                        'message': f"OTP sent successfully to {email}",
                        'otp': otp,
                        'is_existing_user': False
                    }, status=status.HTTP_200_OK)

            elif login_type == 'mobile':
                user = CustomUser.objects.filter(mobile=mobile, user_type=user_type).first()
                print(f"User object:{user}")
                is_existing_user = FarmerProfile.objects.filter(user=user).exists() if user else False
                print(f"Is existing Farmer:{is_existing_user}")
                if user:
                    sendmobile_otp(mobile,otp)
                    store_otp(mobile,otp)
                    return Response({
                        'message': f"OTP sent successfully to {user.mobile}",
                        'otp': otp,
                        'is_existing_user': is_existing_user
                    }, status=status.HTTP_200_OK)
                else:
                    sendmobile_otp(mobile,otp)
                    store_otp(mobile, otp)
                    return Response({
                        'message': f"OTP sent successfully to {mobile}",
                        'otp': otp,
                        'is_existing_user': False
                    }, status=status.HTTP_200_OK)

        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

#################------------------------------------------Verify Otp-------------------###############
class VerifyOTP(APIView):
    permission_classes = [AllowAny]
    def post(self, request, format=None):
        login_type = request.data.get('login_type')
        mobile = request.data.get('mobile')
        email = request.data.get('email', '')
        otp = request.data.get('otp')
        user_type = request.data.get('user_type')
        user_language = request.data.get('user_language')

        if not login_type or not otp or not user_type:
            return Response({'error': 'login_type, identifier, user_type, and otp are required'}, status=status.HTTP_400_BAD_REQUEST)

        if login_type not in ['email', 'mobile']:
            return Response({'error': 'Invalid login_type'}, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"Login type:{login_type}, Mobile:{mobile},Email:{email} OTP:{otp}, UserType:{user_type}")

        try:
            user = None
            if login_type == 'email':
                user = CustomUser.objects.filter(email=email, user_type=user_type).first()
                print(f"User is {user}")
            elif login_type == 'mobile':
                user = CustomUser.objects.filter(mobile=mobile, user_type=user_type).first()
                print(f"User is {user}")

            otp_record = OTPVerification.objects.filter(
                otp=otp,
                mobile=mobile if login_type == 'mobile' else None,
                email=email if login_type == 'email' else None
            ).order_by('-expires_at').first()
            print(f"OTP Record is :{otp_record}")

            if otp_record is None or otp_record.expires_at < timezone.now():
                return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)
            is_existing_user = False
            if user is None:
                if not user_language:
                    return Response({'error': 'User language is required'}, status=status.HTTP_400_BAD_REQUEST)
                user_data = {
                    'email': email if login_type == 'email' else None,
                    'mobile': mobile if login_type == 'mobile' else None,
                    'user_type': user_type,
                    'user_language': user_language, 
                }
                print(f"User data:{user_data}")
                serializer = FarmerRegistrationSerializer(data=user_data, user_type=user_type)
                if serializer.is_valid():
                    user = serializer.save()
                    is_existing_user=False
                    is_land=False
                    print(f"Serializer validated data: {serializer.validated_data}")
                else:
                    print(f"Serializer errors: {serializer.errors}")
                    return Response({'error': 'Failed to create user'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                is_existing_user = FarmerProfile.objects.filter(user=user).exists()
                if is_existing_user:
                    farmer_profile = FarmerProfile.objects.get(user=user)
                    user_language = farmer_profile.fk_language.id
                    print(f"User Language is :{user_language}")
                    print(f"Farmer Record :{farmer_profile}")
                

            if user is None:
                return Response({'error': 'User not found or created'}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                farmer_profile, created = FarmerProfile.objects.update_or_create(
                    user=user,
                    defaults={'fk_language_id': user_language}
                )
                print(f"Farmer Record Created :{farmer_profile}")
                is_land = FarmerLandAddress.objects.filter(fk_farmer=farmer_profile).exists()
                print(f"Land in Record :{is_land}")

            tokens = create_farmer_token(user, user_type)
            print(f"Tokens: {tokens}")
            ip_address = request.META.get('REMOTE_ADDR')

            update_farmer_info(user, user_type, ip_address, mobile=mobile if login_type == 'mobile' else None, is_new=not is_existing_user)
            otp_record.delete()

            return Response({
                'message': 'OTP verified successfully',
                'is_authenticated': True,
                'is_land':is_land,
                'is_existing_user': is_existing_user,
                'tokens': tokens
            }, status=status.HTTP_200_OK)

        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
############---------------------------------Verify Email----------------------------##################
class SendEmailVerification(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.filter(email=email).first()
            print(f"USER IS :{user}")
            if user is None:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            try:
                farmer_profile=FarmerProfile.objects.get(user=user)
                print(f"Farmer profile{farmer_profile}")
            except FarmerProfile.DoesNotExist:
                return Response({'status':'error','message':'Farmer not Found'})
            otp = random.randint(100000, 999999)
            print(f"Verification attempt with email: {email}")
            print(f"\n Otp is {otp}")
            send_otp_via_email(email, otp)
            store_otp(email, otp)
            return Response({
                'message': f"OTP sent successfully to {email}",
            }, status=status.HTTP_200_OK)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
######################--------------------------------------Verify Email Address------------------#################
class VerifyEmail(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        user=request.user
        print(f"User is {user}\n")
        print(f"User Types is {user.user_type}")
        email = request.data.get('email')
        otp = request.data.get('otp') 
        if not email or  not otp:
            return Response({'error': 'email and otp are required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if user.user_type=="farmer":
                user = CustomUser.objects.filter(email=email).first()
                if user is None:
                    return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
                try:
                    farmer_profile=FarmerProfile.objects.get(user=user)
                    print(f"Farmer profile{farmer_profile}")
                except FarmerProfile.DoesNotExist:
                    return Response({'status':'error','message':'Farmer not Found'})
                #------Save Details
                user.email_verified=True
                user.save()
                farmer_profile.email_verified=True
                farmer_profile.sms_status=False
                farmer_profile.save()
                otp_record = OTPVerification.objects.filter(email=email,otp=otp).order_by('-expires_at').first()
                if otp_record is None:
                    return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
                if otp_record.expires_at < timezone.now():
                    return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)
                otp_record.delete() 
                return Response({
                   'message': 'Email verified successfully',
                   'sms_status':farmer_profile.sms_status
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'User type is not farmer'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
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
##############-----------------------------------Part of an FPO or not-----------------------###########
class FarmerFpoPart(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        user=request.user
        print(f"User is {user.user_type}")
        try:
            if user.user_type =="farmer":
                try:
                    farmer = FarmerProfile.objects.get(user=user)
                except FarmerProfile.DoesNotExist:
                    return Response({'error': 'Farmer not found'}, status=status.HTTP_404_NOT_FOUND)

                fpo = farmer.fpo_name
                fpo_name = fpo.fpo_name if fpo else None
                return Response({'message': 'success', 'Fpo Name': fpo_name}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'User type is not farmer'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'error': 'An error occurred.',
                'details': str(e),
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
###############-------------------------------Get ALL States----------------############
class GetallStates(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        user=request.user
        print(f"User is {user.user_type}")
        try:
            if user.user_type=="farmer":
                try:
                    farmer_profile=FarmerProfile.objects.get(user=user)
                    print(f"Farmer is :{farmer_profile.user}")
                    user_language=farmer_profile.fk_language.id
                    print(f"Language is :{user_language}")
                except FarmerProfile.DoesNotExist:
                    return Response({'status': 'error', 'msg': 'No Farmer Data Found'}, status=status.HTTP_404_NOT_FOUND)
                
                states = StateMaster.objects.filter(is_deleted=False)
                states_serializer = StatesSerializer(states, many=True, context={'user_language': user_language})
                print(f"States Data: {states_serializer.data}")
                return Response({'success': 'ok','data': states_serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'User type is not farmer'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

###############-------------------------------Get ALL CROPS----------------############
class GetallCrops(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        user=request.user
        print(f"User is {user.user_type}")
        try:
            user_language=request.query_params.get('user_language')
            if user.user_type=="farmer":

                try:
                    data=CropMaster.objects.filter(fk_language_id=user_language)
                except CropMaster.DoesNotExist:
                    return Response({'status': 'error', 'msg': 'No such Data Found'}, status=status.HTTP_404_NOT_FOUND)
                states_serializer=CropMasterSerializer(data,many=True)
                print(f"States Data: {states_serializer.data}")
                return Response({'success': 'ok','data': states_serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'User type is not farmer'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
#############################################---------------------------Get Crop Variety Details----------------################
class GetCropVariety(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        user=request.user
        print(f"User is '{user.user_type}")
        try:
            if user.user_type=="farmer":
                try:
                    farmer_profile=FarmerProfile.objects.get(user=user)
                    print(f"Farmer profile is {farmer_profile}")
                    user_language=farmer_profile.fk_language.id
                    print(f"Language is :{user_language}")
                except FarmerProfile.DoesNotExist:
                    return Response({'status': 'error', 'msg': 'No Farmer Data Found'}, status=status.HTTP_404_NOT_FOUND)
                crop_id=request.query_params.get('crop_id')
                varieties = CropVariety.objects.filter(fk_crops_id=crop_id)
                print(f"Varieties are {varieties}")
                serializer = CropVarietySerializer(varieties, many=True, context={'user_language': user_language})
                return Response({'message': 'success', 'data': serializer.data}, status=200)
            else:
                return Response({'message':'Only Farmer can access this data'}, status=403)
        except Exception as e:
            return Response({'error': 'An error occurred.', 'details': str(e), 'traceback': traceback.format_exc()}, status=500)
################------------------------------Get State Wise District------------------#########
class GetStateWiseDistrict(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        user=request.user
        print(f"User is {user.user_type}")
        try:
            state = request.query_params.get('state')

            if not state:
                return Response({'error': 'State and user_language are required fields.'}, status=status.HTTP_400_BAD_REQUEST)
            if user.user_type=="farmer":
                try:
                    farmer_profile=FarmerProfile.objects.get(user=user)
                    print(f"Farmer profile is {farmer_profile}")
                    user_language=farmer_profile.fk_language.id
                    print(f"Language is :{user_language}")
                except FarmerProfile.DoesNotExist:
                    return Response({'status': 'error', 'msg': 'No Farmer Data Found'}, status=status.HTTP_404_NOT_FOUND)
                
                districts = DistrictMaster.objects.filter(fk_state_id=state,is_deleted=False )
                serializer = DistrictMasterSerializer(districts, many=True,context={'user_language': user_language})
                return Response({'success': 'Ok', 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'User type is not farmer'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
#################--------------------------------------------Service Providers-----------------------------########################
class ServiceProviderList(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        print(f"User is {user.user_type}")
        try:
            if user.user_type == 'farmer':
                try:
                    farmer_profile=FarmerProfile.objects.get(user=user)
                    print(f"Farmer profile is {farmer_profile}")
                    user_language=farmer_profile.fk_language.id
                    print(f"Language is :{user_language}")
                except FarmerProfile.DoesNotExist:
                    return Response({'status': 'error', 'msg': 'No Farmer Data Found'}, status=status.HTTP_404_NOT_FOUND)
                service_providers = Service_Provider.objects.filter(is_deleted=False)
                serializer = ServiceProviderSerializer(
                        service_providers, many=True, context={'user_language': user_language}
                    )
                return Response({'status': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'status': 'error', 'message': 'User type is not farmer'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
###############################-----------------------------Initial Screen Crops---------------#########################      
class GetInitialScreenCrops(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        if user.user_type != "farmer":
            return Response({"error": "User is not a farmer"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            try:
                farmer_profile=FarmerProfile.objects.get(user=user)
                print(f"Farmer profile is {farmer_profile}")
                user_language=farmer_profile.fk_language.id
                print(f"Language is :{user_language}")
            except FarmerProfile.DoesNotExist:
                return Response({'status': 'error', 'msg': 'No Farmer Data Found'}, status=status.HTTP_404_NOT_FOUND)
            crop_data_by_type_and_season = {}
            crop_mappers = CropMapper.objects.filter(is_deleted=False)
            
            for crop_mapper in crop_mappers:
                if user_language == 1:
                    crop = crop_mapper.eng_crop
                elif user_language == 2:
                    crop = crop_mapper.hin_crop
                else:
                    return Response({"error": "Invalid language parameter"}, status=status.HTTP_400_BAD_REQUEST)
                
                if crop:
                    pop_mapper = crop_mapper.pop_map
                    season_mapper = pop_mapper.season_map if pop_mapper else None
                    
                    crop_type = pop_mapper.eng_pop if user_language == 1 else pop_mapper.hin_pop
                    season = season_mapper.eng_season if user_language == 1 else season_mapper.hin_season
                    crop_image_obj = CropImages.objects.filter(fk_cropmaster=crop_mapper).first()
                    crop_image_url = crop_image_obj.crop_image.url if crop_image_obj and crop_image_obj.crop_image else None
                    
                    crop_data = {
                        'id': crop_mapper.id,  
                        'status': crop.crop_status,
                        'crop_name': crop.crop_name,
                        'season_name': season.season if season else None,
                        'filter_id': pop_mapper.id if pop_mapper else None, 
                        'season_id': season_mapper.id if season_mapper else None,
                        'crop_image': crop_image_url  
                    }
                    
                    crop_type_name = crop_type.name if crop_type else "Unknown"
                    
                    if crop_type_name in crop_data_by_type_and_season:
                        crop_data_by_type_and_season[crop_type_name].append(crop_data)
                    else:
                        crop_data_by_type_and_season[crop_type_name] = [crop_data]
            
            return Response(crop_data_by_type_and_season)
        
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
############----------------------------------Get Disease Videos----------------------------##############
class GetDiseaseVideos(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            user_language = request.query_params.get('user_language')
            if not user_language:
                return Response({'status': 'error','message': 'Missing required field: user_language'}, status=status.HTTP_400_BAD_REQUEST)

            res=DiseaseVideo.objects.filter(fk_language_id=user_language)
            return Response({'status':'success', 'data': list(res.values())})

        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            

    
#####################################--------------------Get POP Type-------------------------#############
class CropTypes(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            if user.user_type != "farmer":
                return Response({'status': 'error', 'message': 'Only farmers can access this data'}, status=status.HTTP_403_FORBIDDEN)
            
            try:
                farmer_profile = FarmerProfile.objects.get(user=user)
                user_language = farmer_profile.fk_language.id
            except FarmerProfile.DoesNotExist:
                return Response({'status': 'error', 'msg': 'No Farmer Data Found'}, status=status.HTTP_404_NOT_FOUND)
            
            pop_mappers = POPMapper.objects.filter(is_deleted=False)
            serializer = POPCropTypeSerializer(pop_mappers, many=True, context={'user_language': user_language})
            print(f"Data:{serializer.data}")
            
            if not serializer.data:
                return Response({'status': 'error', 'message': 'No data found'}, status=status.HTTP_404_NOT_FOUND)
            
            return Response({'message': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)
        
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            print(f"Error: {error_message}")
            print(f"Traceback: {trace}")
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
############################--------------------------------Get all Farm by Farmers--------------------###################
class FarmerAddGetallLandInfo(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request): 
        user = request.user
        print(f"User is {user.user_type}")
        try:
            if user.user_type == 'farmer':
                try:
                    farmer=FarmerProfile.objects.get(user=user)
                except FarmerProfile.DoesNotExist:
                    return Response({'status':'error','message':'Farmer not Found'})
                farmer_lands = FarmerLandAddress.objects.filter(fk_farmer=farmer)
                serializer = FarmerLandAddressSerializer(farmer_lands, many=True)
                return Response({'data': serializer.data},status=status.HTTP_200_OK)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    def post(self,request,format=None):
        user = request.user
        print(f"User is {user.user_type}")
        try:
            if user.user_type == 'farmer':
                try:
                    farmer_profile=FarmerProfile.objects.get(user=user)
                except FarmerProfile.DoesNotExist:
                    return Response({'status':'error','message':'Farmer not Found'})
            else:
                return Response({'status':'error','message':'You are not authorized to perform this action'})
            land_address = FarmerLandAddress(
                fk_farmer=farmer_profile,
                address=request.data.get('address'),
                pincode=request.data.get('pincode', ''),
                fk_state_id=request.data.get('state'),
                fk_district_id=request.data.get('district'),
                village=request.data.get('village', ''),
                fk_crops_id=request.data.get('crop_id',''),
                land_area=request.data.get('land_area', None),
                lat1=request.data.get('lat1', None),
                lat2=request.data.get('lat2', None),
                fk_variety_id=request.data.get('variety_id',None),
                fk_croptype_id=request.data.get('filter_id'),
                his_land=request.data.get('is_land')
            )
            land_address.save()
            return Response({'status':'success','message':'Land added successfully'},status=status.HTTP_200_OK)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    def put(self, request,format=None):
        user = request.user
        print(f"User is {user.user_type}")
        try:
            data=request.data
            land_id=data.get('land_id')
            if not land_id:
                return Response({'status':'error','message':'Land ID is required'},status=status.HTTP_400_BAD_REQUEST)
            if user.user_type == 'farmer':
                try:
                    farmer_profile=FarmerProfile.objects.get(user=user)
                except FarmerProfile.DoesNotExist:
                    return Response({'status':'error','message':'Farmer not Found'})
                try:
                    land_address=FarmerLandAddress.objects.get(id=land_id,fk_farmer=farmer_profile)
                except FarmerLandAddress.DoesNotExist:
                    return Response({'status':'error','message':'Land not Found'})
                land_address_data = ['address', 'pincode', 'fk_state_id', 'fk_district_id', 'village', 'fk_crops_id', 'land_area', 'lat1', 'lat2', 'fk_variety_id', 'is_land',
                                     'sowing_date']
                for field in land_address_data:
                    if field in data:
                        setattr(land_address, field, data[field])
                land_address.save()
                return Response({'status':'success','message':'Land Updated successfully'},status=status.HTTP_200_OK)
            else:
                return Response({'status':'error','message':'You are not authorized to perform this action'})
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        
##################---------------------------------Get Farmer Land Details,Update Farmer land + profile details-----------###
class FarmerDetailsGetUpdate(APIView):
    permission_classes = [IsAuthenticated]
    def put(self,request,format=None):
        user = request.user
        print(f"User is {user.user_type}")
        try:
            data=request.data
            if user.user_type == 'farmer':
                try:
                    farmer_profile=FarmerProfile.objects.get(user=user)
                except FarmerProfile.DoesNotExist:
                    return Response({'status':'error','message':'Farmer not Found'})
                farmer_data = ['name', 'fk_language_id','email','sms_status']
                for field in farmer_data:
                    if field in data:
                        setattr(farmer_profile, field, data[field])
                # ADD EMAIL TO CUSTOM USER        
                if "email" in data:
                    user.email=data["email"]
                    user.save()
                farmer_profile.save()
             
                return Response({'status':'success','message': 'Farmer profile Updated successfully'})
            else:
                return Response({'status':'error','message':'Invalid User'})
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    def get(self,request,format=None):
        user = request.user
        print(f"User is {user.user_type}")
        try:
            land_id = request.query_params.get('land_id')
            if not land_id:
                return Response({'status':'error','message':'Land ID is required'})
            if user.user_type == 'farmer':
                try:
                    farmer_profile=FarmerProfile.objects.get(user=user)
                except FarmerProfile.DoesNotExist:
                    return Response({'status':'error','message':'Farmer not Found'})
                try:
                    farm_land = FarmerLandAddress.objects.get(id=land_id, fk_farmer=farmer_profile)
                except FarmerLandAddress.DoesNotExist:
                    return Response({'status': 'error', 'msg': 'Farm land does not exist'}, status=status.HTTP_404_NOT_FOUND)

            serializer = FarmerLandAddressSerializer(farm_land)
            print(f"Data:{serializer.data}")
            return Response({'status': 'success', 'farm_details': serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
########################----------------------Farmer Profile Details-----------------------############
class GetFarmProfileDetails(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,format=None):
        user=request.user
        print(f"User is {user.user_type}")
        try:
            if user.user_type=="farmer":
                try:
                    farmer_profile=FarmerProfile.objects.get(user=user)
                except FarmerProfile.DoesNotExist:
                    return Response({'status':'error','message':'Farmer not Found'})

                serializer=FarmerProfileSerializer(farmer_profile)
                return Response({'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'status':'error','message':'You are not authorized to perform this action'})
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

###################---------------------------------COMMUNITY-----------------------------########################
###################---------------------------------COMMUNITY-----------------------------########################

##-----------1.Add Post BY Farmer or FPO
class AddCommunityPost(APIView):
    permission_classes=[IsAuthenticated]
    parser_classes = [MultiPartParser,FormParser]
    def post(self, request):
        user=request.user
        print(f"User is {user.user_type}")
        try:
            description = request.data.get('description')
            video_file = request.FILES.get('video_file')
            image_file = request.FILES.get('image_file')
            user_type = request.data.get('user_type')
            if not description or not user_type:
                return Response({'status': 'error', 'msg': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
            
            if user.user_type == "farmer" and user_type =="farmer":
                try:
                    farmer_profile = FarmerProfile.objects.get(user=user)
                    obj = CommunityPost.objects.create(fk_user=farmer_profile, description=description, created_at=datetime.now())
                    farmer_profile.add_coins(10)
                    farmer_profile.save()
                except FarmerProfile.DoesNotExist:
                    return Response({'status': 'error', 'msg': 'FarmerProfile does not exist'}, status=status.HTTP_404_NOT_FOUND)
            elif user.user_type == "fpo" and user_type == "fpo":
                try:
                    fpo_profile = FPO.objects.get(user=user)
                    obj = CommunityPost.objects.create(fk_fpo=fpo_profile, description=description, created_at=datetime.now())
                    fpo_profile.addfpo_coins(10)
                    fpo_profile.save()
                except FPO.DoesNotExist:
                    return Response({'status': 'error', 'msg': 'FPOProfile does not exist'}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({'status': 'error', 'msg': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)

            if video_file or image_file:
                media = PostsMedia.objects.create(fk_post=obj, video_file=video_file, image_file=image_file)
                print(f"Media created: {media}")
                print(f"Image file path: {media.image_file.url if media.image_file else 'No image file'}")
            

            return Response({'status': 'success', 'msg': 'Post Created Successfully'}, status=status.HTTP_200_OK)

        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
###############################----------------------------------Add Comment on Post----------------------#################################
from datetime import datetime, date
class CommentOnPost(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user=request.user
        print(f"User is {user}")
        try:
            data = request.data
            post_id = data.get('post_id')
            comment_text = data.get('comment_text')
            user_type = data.get('user_type')
            if not post_id or not comment_text or not user_type:
                return Response({'status': 'error', 'msg': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                fk_post = CommunityPost.objects.get(id=post_id)
            except CommunityPost.DoesNotExist:
                return Response({'status': 'error', 'msg': 'Community post does not exist'}, status=status.HTTP_404_NOT_FOUND)
            try:
                if user.user_type == "farmer" and user_type=="farmer":
                    user = FarmerProfile.objects.get(user=user)
                    comment = PostComments.objects.create(fk_user=user, fk_post=fk_post, text=comment_text, created_at=datetime.now())
                
                elif user.user_type == "fpo" and user_type=="fpo":
                    user = FPO.objects.get(id=user)
                    comment = PostComments.objects.create(fk_fpo=user, fk_post=fk_post, text=comment_text, created_at=datetime.now())
                else:
                    return Response({'status': 'error', 'msg': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)
            except FarmerProfile.DoesNotExist:
                return Response({'status': 'error', 'msg': 'Farmer profile does not exist'}, status=status.HTTP_404_NOT_FOUND)
            except FPO.DoesNotExist:
                return Response({'status': 'error', 'msg': 'FPO profile does not exist'}, status=status.HTTP_404_NOT_FOUND)

            profile_pic_url = None
            if hasattr(user, 'profile') and user.profile:
                profile_pic_url = user.profile.url
            return Response({
                'status': 'success',
                'msg': 'Comment Added Successfully',
                'comment': {
                    'id': comment.id,
                    'post_id': comment.fk_post.id,
                    'user_id': user.id,
                    'user_name': user.name,
                    'user_type': user_type,
                    'profile_pic': profile_pic_url,
                    'post_comment': comment.text,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
###########################----------------------------Reply On POST------------------------#################################
class ReplyOnPostComment(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user=request.user
        print(f"User is {user.user_type}")
        try:
            fk_postcomment_id = request.data.get('fk_postcomment_id')
            text = request.data.get('text')
            user_type = request.data.get('user_type')
            if not fk_postcomment_id or not text or not user_type:
                return Response({'status': 'error', 'msg': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                fk_postcomment = PostComments.objects.get(id=fk_postcomment_id)
                print(f"POST Comment : {fk_postcomment}")
            except PostComments.DoesNotExist:
                return Response({'status': 'error', 'msg': 'Post comment does not exist'}, status=status.HTTP_404_NOT_FOUND)
            if user.user_type=="farmer" and user_type == "farmer":
                try:
                    fk_user = FarmerProfile.objects.get(user=user)
                except FarmerProfile.DoesNotExist:
                    return Response({'status': 'error', 'msg': 'Farmer profile does not exist'}, status=status.HTTP_404_NOT_FOUND)
                comment_reply = CommentReply.objects.create(fk_user=fk_user, fk_postcomment=fk_postcomment, text=text, created_at=datetime.now())
            elif user.user_type=="fpo" and user_type == "fpo":
                try:
                    fk_user = FPO.objects.get(user=user)
                except FPO.DoesNotExist:
                    return Response({'status': 'error', 'msg': 'FPO profile does not exist'}, status=status.HTTP_404_NOT_FOUND)
                comment_reply = CommentReply.objects.create(fk_fpo=fk_user, fk_postcomment=fk_postcomment, text=text, created_at=datetime.now())
            else:
                return Response({'status': 'error', 'msg': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)
            profile_pic_url = None
            if hasattr(fk_user, 'profile') and fk_user.profile:
                profile_pic_url = fk_user.profile.url
            return Response({
                'status': 'success',
                'msg': 'Reply on comment successfully added',
                'reply': {
                    'reply_id': comment_reply.id,
                    'comment_id': fk_postcomment.id,
                    'user_id': fk_user.id,
                    'user_type': user_type,
                    'user_name': fk_user.name if user_type == "farmer" else fk_user.name,
                    'profile_pic': profile_pic_url,
                    'text': comment_reply.text,
                    'created_dt': comment_reply.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
###########################---------------------------Like Post By Differente uSers---------------######################
class LikeUnlikePost(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user_type = request.data.get("user_type")
        fk_post_id = request.data.get("fk_post_id")
        action = request.data.get("action")  # 'like' or 'unlike'
        
        if user_type not in ["farmer", "fpo"]:
            return Response({"status": "error", "msg": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            post = CommunityPost.objects.get(id=fk_post_id)
        except CommunityPost.DoesNotExist:
            return Response({"status": "error", "msg": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        if user_type == "farmer":
            user_profile = FarmerProfile.objects.get(user=user)
        else:
            user_profile = FPO.objects.get(user=user)

        like_record, created = PostsLike.objects.get_or_create(
            fk_post=post,
            fk_user=user_profile if user_type == "farmer" else None,
            fk_fpo=user_profile if user_type == "fpo" else None
        )

        if action == "like":
            if created:  # If the like record was created
                like_record.created_at = timezone.now()
                like_record.save()
                post_like_count = PostsLike.objects.filter(fk_post=post).count()
                return Response({"status": "success", "msg": "Post liked", "like_count": post_like_count}, status=status.HTTP_200_OK)
            else:
                return Response({"status": "error", "msg": "Post already liked"}, status=status.HTTP_400_BAD_REQUEST)
        
        elif action == "unlike":
            if not created:  # If the like record was not newly created
                like_record.delete()
                post_like_count = PostsLike.objects.filter(fk_post=post).count()
                return Response({"status": "success", "msg": "Post unliked", "like_count": post_like_count}, status=status.HTTP_200_OK)
            else:
                return Response({"status": "error", "msg": "Post not liked before"}, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            return Response({"status": "error", "msg": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
#################################-------------------Get ALL Info about POST-------------------##################
class CommunityPostsList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_profile = None
        try:
            if user.user_type == "farmer":
                user_profile = FarmerProfile.objects.get(user=user)
            elif user.user_type == "fpo":
                user_profile = FPO.objects.get(user=user)
            else:
                return Response({'status': 'error', 'msg': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)
            
            filter_type = request.query_params.get('filter_type', 'all')
            if filter_type == 'farmer':
                posts = CommunityPost.objects.filter(fk_user__isnull=False).order_by('-created_at')
            elif filter_type == 'fpo':
                posts = CommunityPost.objects.filter(fk_fpo__isnull=False).order_by('-created_at')
            else:
                posts = CommunityPost.objects.all().order_by('-created_at')
            
            final_list = []
            for post in posts:
                post_img = PostsMedia.objects.filter(fk_post_id=post.id).first()
                like_objects = PostsLike.objects.filter(fk_post_id=post.id)
                is_liked = like_objects.filter(fk_user=user_profile).exists() if user_profile else False
                
                users_liked = [
                    {
                        'user_id': like.fk_user.id if like.fk_user else (like.fk_fpo.id if like.fk_fpo else None),
                        'user_name': like.fk_user.name if like.fk_user else (like.fk_fpo.name if like.fk_fpo else None),
                        'post_id': like.fk_post.id if like.fk_post else None
                    }
                    for like in like_objects
                ]
                
                final_dict = {
                    "user_name": post.fk_user.name if post.fk_user else (post.fk_fpo.name if post.fk_fpo else ''),
                    'user_id': post.fk_user.id if post.fk_user else (post.fk_fpo.id if post.fk_fpo else ''),
                    "post_id": post.id,
                    'profile_pic': post.fk_user.profile.url if post.fk_user and hasattr(post.fk_user, 'profile') and post.fk_user.profile else (post.fk_fpo.profile.url if post.fk_fpo and hasattr(post.fk_fpo, 'profile') and post.fk_fpo.profile else ''),
                    'post_image': post_img.image_file.url if post_img and post_img.image_file else '',
                    'post_video': post_img.video_file.url if post_img and post_img.video_file else '',
                    'like_count': like_objects.count(),
                    'is_likedbysameuser': is_liked,
                    'users_liked': users_liked,
                    'description': post.description if post.description else '',
                    'created_at': post.created_at if post.created_at else '',
                    'comment_list': []
                }
                
                comment_list = []
                comment_objects = PostComments.objects.filter(fk_post_id=post.id).order_by('-created_at')
                for comment in comment_objects:
                    comment_dict = {
                        'user_name': comment.fk_user.name if comment.fk_user else (comment.fk_fpo.name if comment.fk_fpo else ''),
                        'user_id': comment.fk_user.id if comment.fk_user else (comment.fk_fpo.id if comment.fk_fpo else ''),
                        'profile_pic': comment.fk_user.profile.url if comment.fk_user and hasattr(comment.fk_user, 'profile') and comment.fk_user.profile else (comment.fk_fpo.profile.url if comment.fk_fpo and hasattr(comment.fk_fpo, 'profile') and comment.fk_fpo.profile else ''),
                        'id': comment.id if comment.id else '',
                        'post_comment': comment.text if comment.text else '',
                        'created_at': comment.created_at if comment.created_at else '',
                        'reply_comments': []
                    }
                    
                    reply_list = []
                    reply_objects = CommentReply.objects.filter(fk_postcomment_id=comment.id).order_by('-created_at')
                    for reply in reply_objects:
                        reply_dict = {
                            'user_name': reply.fk_user.name if reply.fk_user else (reply.fk_fpo.name if reply.fk_fpo else ''),
                            'user_id': reply.fk_user.id if reply.fk_user else (reply.fk_fpo.id if reply.fk_fpo else ''),
                            'profile_pic': reply.fk_user.profile.url if reply.fk_user and hasattr(reply.fk_user, 'profile') and reply.fk_user.profile else (reply.fk_fpo.profile.url if reply.fk_fpo and hasattr(reply.fk_fpo, 'profile') and reply.fk_fpo.profile else ''),
                            'id': reply.id if reply.id else '',
                            'text': reply.text if reply.text else '',
                            'created_at': reply.created_at if reply.created_at else '',
                        }
                        reply_list.append(reply_dict)
                    
                    comment_dict['reply_comments'] = reply_list
                    comment_list.append(comment_dict)
                
                final_dict['comment_list'] = comment_list
                final_list.append(final_dict)
            
            return Response({'status': 'success', 'message': "Community post list", 'data': final_list}, status=status.HTTP_200_OK)
        
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


###########################----------------------------DISEASE DETECTION-------------------------##################
####################################--------------------Disease Outbreak Notification--------------------------###################
class DiseaseOutBreak(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,format=None):
        user=request.user
        print(f"User is :{user}")
        try:
            if user.user_type=="farmer":
                try:
                    farmer_profile = FarmerProfile.objects.get(user=user)
                    print(f"Farmer profile is :{farmer_profile}")
                    user_language = farmer_profile.fk_language.id
                except FarmerProfile.DoesNotExist:
                    return Response({'status': 'error', 'msg': 'No Farmer Data Found'}, status=status.HTTP_404_NOT_FOUND)
                try:
                    farm=FarmerLandAddress.objects.filter(fk_farmer=farmer_profile)
                except FarmerLandAddress.DoesNotExist:
                    return Response({'status': 'error', 'msg': 'No Farmer Land Data Found'}, status=status.HTTP_404_NOT_FOUND)
                serializer = DiseaseOutBreakSerializer(farm, many=True, context={'user_language': user_language, 'current_farmer': farmer_profile})
                return Response({'status': 'success', 'disease_data': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'status': 'error', 'message': 'User type is not farmer'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            print(f"Error: {error_message}")
            print(f"Traceback: {trace}")
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
                
                
#########---------------------------------------------Disease Detection----------------------------------- ###################
def process_image(image, model_name):
    pipe = pipeline("image-classification", model=model_name, device='cpu')
    predictions = pipe(image)
    max_prediction = max(predictions, key=lambda x: x['score'])
    disease_name = max_prediction['label']
    return disease_name, predictions


class DetectDiseaseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        print(f"User is {user.user_type}")

        try:
            service_provider_id = request.data.get('service_provider_id')
            crop_id = request.data.get('crop_id')
            image = request.FILES.get('image')
            filter_type = request.data.get('filter_type')
            farmer_land_id = request.data.get('farmer_land_id')

            if user.user_type != "farmer":
                return Response({'error': 'Invalid user type'}, status=status.HTTP_403_FORBIDDEN)

            try:
                farmer_profile = FarmerProfile.objects.get(user=user)
                user_language=farmer_profile.fk_language.id
                print(f"User language IS: {user_language}")
                farmer_profile.add_coins(10)
                farmer_profile.save()
            except FarmerProfile.DoesNotExist:
                return Response({'error': 'No Farmer Data Found'}, status=status.HTTP_404_NOT_FOUND)

            fk_farm_id, state, district = None, None, None
            if farmer_land_id:
                try:
                    farm = FarmerLandAddress.objects.get(id=farmer_land_id, fk_farmer=farmer_profile, fk_crops__id=crop_id)
                    print(f"Farme Data is :{farm}")
                    fk_farm_id = farm.id
                    if user_language == 1:  
                        state = farm.fk_state.eng_state if farm.fk_state else None
                        print(f"State is :{state}")
                        district = farm.fk_district.eng_district if farm.fk_district else None
                        print(f"District is :{district}")
                    elif user_language == 2:  
                        state = farm.fk_state.hin_state if farm.fk_state else None
                        print(f"State is :{state}")
                        district = farm.fk_district.hin_district if farm.fk_district else None
                        print(f"District is :{district}")
                    else:
                        return Response({'error': 'Invalid user language'}, status=status.HTTP_400_BAD_REQUEST)

                except FarmerLandAddress.DoesNotExist:
                    return Response({'error': 'Invalid farmer land ID'}, status=status.HTTP_404_NOT_FOUND)

            # Determine model name based on crop ID and filter type
            related_crop_ids = {
                '1': ['1', '1'],
                '2': ['2', '2'],
            }

            model_name_map = {
                'leaf': {
                    '1': "Amanaccessassist/finetuner-potato-leaf",
                    '2': "Amanaccessassist/finetune-mango-leaf",
                },
                'finished product': {
                    '1': "Amanaccessassist/finetuned-potato-chips",
                },
                'crop': {
                    '1': "Amanaccessassist/finetuned-potato-food",
                    '2': "Amanaccessassist/finetuned-mango-food",
                }
            }

            model_name = model_name_map.get(filter_type.lower(), {}).get(crop_id)
            if not model_name:
                return Response({'error': 'Invalid crop ID or filter type'}, status=status.HTTP_400_BAD_REQUEST)

            # Process image and get disease information
            pil_image = Image.open(image)
            disease_name, disease_images = process_image(pil_image, model_name)

            if user_language == 1:
                obj = DiseaseMaster.objects.filter(name=disease_name, fk_crops__id__in=related_crop_ids[crop_id], fk_language_id=user_language).first()
            elif user_language == 2:
                try:
                    language = LanguageSelection.objects.get(id=user_language)
                    disease_translations = DiseaseTranslation.objects.filter(fk_disease__name=disease_name, fk_language=language)
                    if disease_translations.exists():
                        disease_translation = disease_translations.first()
                        disease_name = disease_translation.translation_name
                        obj = DiseaseMaster.objects.filter(name=disease_name, fk_crops__id__in=related_crop_ids[crop_id]).first()
                    else:
                        return Response({'error': f'Disease translation not found for language {user_language}'}, status=status.HTTP_404_NOT_FOUND)
                except LanguageSelection.DoesNotExist:
                    return Response({'error': 'Invalid language ID'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'Invalid user language'}, status=status.HTTP_400_BAD_REQUEST)

            if not obj:
                return Response({'error': 'Disease not found in database'}, status=status.HTTP_404_NOT_FOUND)

            disease_images_queryset = Disease_Images_Master.objects.filter(fk_disease__id=obj.id)
            disease_images_serialized = DiseaseImagesMasterSerializer(disease_images_queryset, many=True).data

            upload_disease = Upload_Disease.objects.create(
                fk_provider_id=service_provider_id,
                fk_crop_id=crop_id,
                fk_disease=obj,
                filter_type=filter_type,
                uploaded_image=image,
                fk_user=farmer_profile,
                fk_farmer_land_id=fk_farm_id,
                state=state,
                district=district
            )

            disease_images_serialized.insert(0, {'disease_file': upload_disease.uploaded_image.url if upload_disease.uploaded_image else None})

            product_disease_queryset = DiseaseProductInfo.objects.filter(
                fk_disease__name=disease_name,
                fk_crop__id__in=related_crop_ids[crop_id]
            ).distinct().prefetch_related('fk_product')

            product_disease_serialized = DiseaseProductInfoSerializer(product_disease_queryset, many=True).data

            disease_results = {
                'disease_id': obj.id,
                'disease': obj.name,
                'crop_id': int(crop_id),
                'symptom': obj.symptom,
                'treatmentbefore': obj.treatmentbefore,
                'treatmentfield': obj.treatmentfield,
                'treatment': obj.treatment,
                'message': obj.message,
                'suggestiveproduct': obj.suggestiveproduct,
                'images': disease_images_serialized,
                'base_path': '/media/disease'
            }

            return Response({
                'disease_results': disease_results,
                'product_disease': product_disease_serialized
            }, status=status.HTTP_200_OK)

        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
#############################----------------------Disease Vdieo--------------------##################
class GetDiseaseVideo(APIView):
    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            print(f"User is: {user.user_type}")
            user_language = request.query_params.get('user_language')
            if not user_language:
                return Response({'message': 'user_language is required'}, status=status.HTTP_400_BAD_REQUEST)

            if user.user_type == "farmer":
                try:
                    farmer_profile = FarmerProfile.objects.get(user=user)
                    print(f"Farmer Object: {farmer_profile}")
                except FarmerProfile.DoesNotExist:
                    return Response({'message': 'Farmer profile does not exist'}, status=status.HTTP_404_NOT_FOUND)

                res = DiseaseVideo.objects.get(fk_language_id=user_language)
                serializer = DiseaseVideoSerializer(res)
                return Response({'message': 'success', 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Invalid user type'}, status=status.HTTP_403_FORBIDDEN)
        
        except Exception as e:
            return JsonResponse({'message': 'An error occurred', 'error': traceback.format_exc()}, status=500)
######################----------------------------------------Get Single Diagnosis Report--------------------##############      
class GetSingleDiagnosisReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        print(f"User is {user}")
        try:
            diag_id = request.query_params.get('diag_id')
            if not diag_id:
                return Response({'status': 'error', 'message': 'Diagnosis report ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                farmer_profile = FarmerProfile.objects.get(user=user)
                print(f"Farmer profile: {farmer_profile}")
                user_language = farmer_profile.fk_language
                print(f"Farmer Language is: {user_language}")
            except FarmerProfile.DoesNotExist:
                return Response({'status': 'error', 'message': 'Farmer profile not found for this user'}, status=status.HTTP_404_NOT_FOUND)
            
            user_disease = Upload_Disease.objects.filter(
                id=diag_id, fk_user=farmer_profile, is_deleted=False
            ).select_related("fk_disease", "fk_crop")
            
            if not user_disease.exists():
                return Response({'status': 'error', 'message': 'Diagnosis report not found'}, status=status.HTTP_404_NOT_FOUND)
            
            first_disease = user_disease.first()
            disease = first_disease.fk_disease.name if first_disease.fk_disease else None
            cropid = first_disease.fk_crop.id if first_disease.fk_crop else None
            disease_results = UploadDiseaseSerializer(user_disease, many=True, context={'user_language': user_language}).data
            product_disease = DiseaseProductInfo.objects.filter(
                fk_disease__name=disease,
                fk_crop_id=cropid
            ).prefetch_related('fk_product')
            
            product_disease_results = DiseaseProductInfoSerializer(product_disease, many=True).data
            
            return Response({
                'status': 'success',
                'disease_results': disease_results,
                'product_disease_results': product_disease_results
            })
        
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class GetDiagnosisReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        print(f"User is {user}")
        try:
            if user.user_type == "farmer":
                try:
                    farmer_profile = FarmerProfile.objects.get(user=user)
                    user_language = farmer_profile.fk_language.id
                    print(f"Farmer profile: {farmer_profile}")
                except FarmerProfile.DoesNotExist:
                    return Response({'status': 'error', 'message': 'Farmer profile not found for this user'}, status=status.HTTP_404_NOT_FOUND)
                
                user_disease = Upload_Disease.objects.filter(
                    fk_user=farmer_profile,
                    is_deleted=False
                ).order_by('-id')
                print(f"User Diseases: {user_disease}")
                
                if not user_disease.exists():
                    return Response({'message': 'Record Not Found'}, status=status.HTTP_404_NOT_FOUND)
                
                disease_details = UploadDiseaseSerializer(user_disease, many=True, context={'user_language': user_language}).data
                return Response({'status': 'success', 'disease_details': disease_details})
            else:
                return Response({'status': 'error', 'message': 'Invalid user type'}, status=status.HTTP_403_FORBIDDEN)
        
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request):
        user=request.user
        print(f"User is {user.user_type}")
        try:
            disease_id = request.data.get('disease_id')
            if user.user_type=="farmer":
                try:
                    farmer_profile=FarmerProfile.objects.get(user=user)
                    print(f"Farmer profile :{farmer_profile}")
                except FarmerProfile.DoesNotExist:
                    return Response({'status': 'error','message': 'Farmer profile not found for this user'}, status=status.HTTP_404_NOT_FOUND)
                data= Upload_Disease.objects.filter(fk_user=farmer_profile, id=disease_id)
                print(f"Deleted Record :{data}")
                data.update(is_deleted=True)

                if data:
                    return Response({'status': 'success', 'message': 'Disease deleted successfully'}, status=status.HTTP_200_OK)
                else:
                    return Response({'status': 'error', 'message': 'Record not found'}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({'status': 'error','message': 'Only farmer can delete disease'}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
###################################################--GOVT SCHEMES--#######################################################
class GetallGovtSchemes(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        user=request.user
        print(f"User is {user.user_type}")
        try:
            filter_type = request.query_params.get('filter_type', 'all')
            if not filter_type:
                return Response({'status': 'error','message': 'Filter type is required'}, status=status.HTTP_400_BAD_REQUEST)
            if user.user_type=="farmer":
                try:
                    farmer_profile=FarmerProfile.objects.get(user=user)
                    user_language=farmer_profile.fk_language.id
                    print(f"Farmer profile :{farmer_profile}")
                except FarmerProfile.DoesNotExist:
                    return Response({'status': 'error','message': 'Farmer profile not found for this user'}, status=status.HTTP_404_NOT_FOUND)
                schemes = GovtSchemes.objects.all()
                if user_language:
                    schemes = schemes.filter(fk_language_id=user_language)
                if filter_type == 'central':
                    schemes = schemes.filter(scheme_by__in=['Central Schemes', 'केन्द्र सरकार की योजनाएं'])
                elif filter_type == 'state':
                    schemes = schemes.filter(scheme_by__in=['State Schemes', 'राज्य सरकार की योजनाएं'])
                serializer = GovtSchemesSerializer(schemes, many=True)
                return Response({'status': 'success', 'schemes': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'status': 'error','message': 'Only farmer can view government schemes'}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class GovtSchemesbyID(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        user=request.user
        print(f"User is {user.user_type}")
        try:
            govt_id =request.query_params.get ('govt_id')
            
            if not govt_id:
                return Response({'message': 'govt_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            if user.user_type=="farmer":
                try:
                    farmer_profile=FarmerProfile.objects.get(user=user)
                    user_language=farmer_profile.fk_language.id
                    print(f"Farmer profile :{farmer_profile}")
                except FarmerProfile.DoesNotExist:
                    return Response({'status': 'error','message': 'Farmer profile not found for this user'}, status=status.HTTP_404_NOT_FOUND)
                govt_schemes = GovtSchemes.objects.filter(id=govt_id, fk_language_id=user_language)
                if not govt_schemes.exists():
                    return Response({'message': 'No schemes found'}, status=status.HTTP_404_NOT_FOUND)
            
                serializer = GovtSchemesSerializer(govt_schemes, many=True)
                return Response({'message': 'Successful', 'schemes': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'status': 'error','message': 'Only farmer can view government schemes by ID'}, status=status.HTTP_403_FORBIDDEN)
        
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )   
##################################################--CURRENT NEWS---################################################
class GetCurrentNews(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        user=request.user
        print(f"User is {user.user_type}")
        try:
            filter_type = request.query_params.get('filter_type', 'all')
            limit = request.query_params.get('limit', 20)  
            offset = request.query_params.get('offset', 0) 
            if not filter_type:
                return Response({'message': 'FilterType is Required'}, status=status.HTTP_400_BAD_REQUEST)
            if user.user_type=="farmer":
                try:
                    farmer_profile=FarmerProfile.objects.get(user=user)
                    user_language=farmer_profile.fk_language.id
                    print(f"Farmer profile :{farmer_profile}")
                except FarmerProfile.DoesNotExist:
                    return Response({'status': 'error','message': 'Farmer profile not found for this user'}, status=status.HTTP_404_NOT_FOUND)
                news = CurrentNews.objects.all()
                if user_language:
                    news = news.filter(fk_language_id=user_language)
                if filter_type in ["ABPLIVE", "KRISHAKJAGAT", "KISANSAMADHAAN", "KRISHIJAGRAN", "KISANTAK"]:
                    news = news.filter(source=filter_type)
                news = news.exclude(title__isnull=True).exclude(content__isnull=True).exclude(image__isnull=True)
                news = news.order_by('-created_at')
                paginator=CurrentNewsPagination()
                paginator.limit = limit
                paginator.offset = offset
                result_page = paginator.paginate_queryset(news, request)
                serializer = CurrentNewsSerializer(result_page, many=True)
                return paginator.get_paginated_response(serializer.data)
            else:
                return Response({'status': 'error','message': 'Only farmer can view current news'}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )   
#######---  Get Current News by Id--------------------#
class GetCurrentNewsbyID(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        user=request.user
        print(f"Users is {user.user_type}")
        try:
            news_id = request.query_params.get('news_id')
            if not news_id:
                return Response({'message': 'news_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            if user.user_type=="farmer":
                news = CurrentNews.objects.filter(id=news_id).first()
                if not news:
                    return Response({'message': 'No news found'}, status=status.HTTP_404_NOT_FOUND)
            
                serializer = CurrentNewsSerializer(news)
                return Response({'message': 'Successful', 'news': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'status': 'error','message': 'Only farmer can view current news by ID'}, status=status.HTTP_403_FORBIDDEN)
        
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )   
################################################--------FERTILIZERS CALCULATOR----------------###############################
class Fertilizerswithtest(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request):
        user=request.user
        print(f"User is {user.user_type}")
        try:
            data = request.data
            farm_id = data.get('farm_id')
            crop_id = data.get('crop_id')
            nitrogen = data.get('nitrogen')
            phosphorous = data.get('phosphorous')
            potassium = data.get('potassium')

            if crop_id not in [1]:
                return Response({'error': 'Crop ID is not supported'}, status=status.HTTP_400_BAD_REQUEST)

            if nitrogen is None or phosphorous is None or potassium is None:
                return Response({'error': 'Missing required nutrient values'}, status=status.HTTP_400_BAD_REQUEST)
            if user.user_type=="farmer":
                try:
                    farmer_profile = FarmerProfile.objects.get(user=user)
                    user_language=farmer_profile.fk_language.id
                except FarmerProfile.DoesNotExist:
                    return Response({'error': 'FarmerProfile not found'}, status=status.HTTP_404_NOT_FOUND)

                if farm_id:
                    try:
                        farm = FarmerLandAddress.objects.get(id=farm_id, fk_farmer=farmer_profile, fk_crops__id=crop_id)
                    except FarmerLandAddress.DoesNotExist:
                        return Response({'error': 'Invalid farmer land ID'}, status=status.HTTP_404_NOT_FOUND)

            # Determine NPK status
                npk = []
                N = "Low" if nitrogen < 240 else "Medium" if 240 <= nitrogen <= 480 else "High"
                P = "Low" if phosphorous < 11 else "Medium" if 11 <= phosphorous <= 22 else "High"
                K = "Low" if potassium < 110 else "Medium" if 110 <= potassium <= 280 else "High"
                npk.append({
                'N': N,
                'Nitrogen_Value': nitrogen,
                'P': P,
                'Phosphorous_Value': phosphorous,
                'K': K,
                'Potassium_Value': potassium
            })

                results = []

            # Calculations for Urea
                kgha_n = round(nitrogen * 2.17)
                bag_n = round(kgha_n / 50)
                price_n = round(kgha_n * 5.31)

            # Calculations for Super Phosphate
                kgha_p = round(phosphorous * 6.25)
                bag_p = round(kgha_p / 50)
                price_p = round(kgha_p * 6)

            # Calculations for Potash
                kgha_k = round(potassium * 1.66)
                bag_k = round(kgha_k / 50)
                price_k = round(kgha_k * 12.04)

                results.append({
                'Urea': {
                    'Kg/ha': kgha_n,
                    '(50 kg bag)': bag_n,
                    'Price (Rs)': price_n
                },
                'Super Phosphate': {
                    'Kg/ha': kgha_p,
                    '(50 kg bag)': bag_p,
                    'Price (Rs)': price_p
                },
                'Potash': {
                    'Kg/ha': kgha_k,
                    '(50 kg bag)': bag_k,
                    'Price (Rs)': price_k
                }
                })

                return Response({'NPK Status': npk, 'results': results}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Only farmer can calculate fertilizers'}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )   
    def get(self, request,format=None):
        try:
            user = request.user
            farm_id = request.query_params.get('farm_id')
            crop_id = request.query_params.get('crop_id')
            if crop_id not in ["1"]:
                return Response({'error': 'Crop ID is not supported'}, status=status.HTTP_400_BAD_REQUEST)

            if user.user_type != "farmer":
                return Response({'error': 'User is not authorized to access this information'}, status=status.HTTP_403_FORBIDDEN)

            try:
                farmer_profile = FarmerProfile.objects.get(user=user)
                user_language=farmer_profile.fk_language.id
            except FarmerProfile.DoesNotExist:
                return Response({'error': f'FarmerProfile not found for user_id: {user}'}, status=status.HTTP_404_NOT_FOUND)

            if farm_id:
                try:
                    farm = FarmerLandAddress.objects.get(id=farm_id, fk_farmer=farmer_profile, fk_crops__id=crop_id)
                    if user_language == 1:  
                        state = farm.fk_state.eng_state if farm.fk_state else None
                        print(f"State is :{state}")
                        district = farm.fk_district.eng_district if farm.fk_district else None
                        print(f"District is :{district}")
                    elif user_language == 2:  
                        state = farm.fk_state.hin_state if farm.fk_state else None
                        print(f"State is :{state}")
                        district = farm.fk_district.hin_district if farm.fk_district else None
                        print(f"District is :{district}")
                    else:
                        return Response({'error': 'Invalid user language'}, status=status.HTTP_400_BAD_REQUEST)
                except FarmerLandAddress.DoesNotExist:
                    return Response({'error': 'Invalid farmer land ID'}, status=status.HTTP_404_NOT_FOUND)

            try:
                if user_language==1:
                    crop_name = CropMapper.objects.get(id=crop_id).eng_crop.crop_name
                    print(f"English Crop Name is :{crop_name}")
                elif user_language==2:
                    crop_name = CropMapper.objects.get(id=crop_id).hin_crop.crop_name
                    print(f"Hindi Crop Name is :{crop_name}")
            except CropMapper.DoesNotExist:
                return Response({'error': 'Invalid Crop ID'}, status=status.HTTP_404_NOT_FOUND)

            fertilizers = Fertilizer.objects.filter(fk_language=user_language, fk_crop_id=crop_id)
            if not fertilizers.exists():
                return Response({'error': f'No fertilizers data found for the crop: {crop_name}'}, status=status.HTTP_404_NOT_FOUND)

            results = []
            for fertilizer in fertilizers.values('nitrogen', 'phosphorus', 'potassium'):
                nitrogen = fertilizer['nitrogen']
                phosphorus = fertilizer['phosphorus']
                potassium = fertilizer['potassium']

                # Calculations for Urea
                kgha_n = round(nitrogen * 2.17)
                bag_n = round(kgha_n / 50)
                price_n = round(kgha_n * 5.31)

                # Calculations for Super Phosphate
                kgha_p = round(phosphorus * 6.25)
                bag_p = round(kgha_p / 50)
                price_p = round(kgha_p * 6)

                # Calculations for Potash
                kgha_k = round(potassium * 1.66)
                bag_k = round(kgha_k / 50)
                price_k = round(kgha_k * 12.04)

                results.append({
                    'Urea': {
                        'Kg/ha': kgha_n,
                        '(50 kg bag)': bag_n,
                        'Price (Rs)': price_n
                    },
                    'Super Phosphate': {
                        'Kg/ha': kgha_p,
                        '(50 kg bag)': bag_p,
                        'Price (Rs)': price_p
                    },
                    'Potash': {
                        'Kg/ha': kgha_k,
                        '(50 kg bag)': bag_k,
                        'Price (Rs)': price_k
                    }
                })

            return Response({'message': 'Successful', 'results': results}, status=status.HTTP_200_OK)

        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )   
###################-----------------------------------------Advance Fertilizer Calculator----------------------#############  
class AdvanceFertilizercalculator(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request):
        user=request.user
        print(f"User is {user.user_type}")
        try:
            data = request.data
            farm_id = data.get('farm_id')
            crop_id = data.get('crop_id')
            daep = data.get('daep', 0)
            complexes = data.get('complexes', 0)
            urea = data.get('urea', 0)
            ssp = data.get('ssp', 0)
            mop = data.get('mop', 0)
            if crop_id not in [1]:
                return Response({'error': 'Crop ID is not supported'}, status=status.HTTP_400_BAD_REQUEST)
            if user.user_type=="farmer":
                try:
                    farmer_profile = FarmerProfile.objects.get(user=user)
                    user_language=farmer_profile.fk_language.id
                except FarmerProfile.DoesNotExist:
                    return Response({'error': 'FarmerProfile not found for user_id'}, status=status.HTTP_404_NOT_FOUND)
            
                try:
                    if user_language==1:
                        crop_name = CropMapper.objects.get(id=crop_id).eng_crop.crop_name
                        print(f"English Crop Name is :{crop_name}")
                    elif user_language==2:
                        crop_name = CropMapper.objects.get(id=crop_id).hin_crop.crop_name
                        print(f"Hindi Crop Name is :{crop_name}")
                except CropMaster.DoesNotExist:
                    return Response({'error': 'Invalid Crop ID'}, status=status.HTTP_404_NOT_FOUND)
            
                if farm_id:
                    try:
                        farm = FarmerLandAddress.objects.get(id=farm_id, fk_farmer=farmer_profile, fk_crops__id=crop_id)
                    except FarmerLandAddress.DoesNotExist:
                        return Response({'error': 'Invalid farmer land ID'}, status=status.HTTP_404_NOT_FOUND)
            
                fertilizers = Fertilizer.objects.filter(fk_language=user_language, fk_crop_id=crop_id)
                print(f"Fertilizer object :{fertilizers}")
                if not fertilizers.exists():
                    return Response({'error': f'No fertilizers data found for the crop: {crop_name}'}, status=status.HTTP_404_NOT_FOUND)

            # DAEP Calculation - Nitrogen, Phosphorous, Potassium
                daep_nitrogen = round(daep * 9)
                daep_phosporous = round(daep * 23)
                daep_potassium = round(daep * 0)

            # Complex 17:17:17 Calculation - Nitrogen, Phosphorous, Potassium
                complex_nitrogen = round(complexes * 8.5)
                complex_phosporous = round(complexes * 8.5)
                complex_potassium = round(complexes * 8.5)

            # Urea Calculation - Nitrogen, Phosphorous, Potassium
                urea_nitrogen = round(urea * 23)
                urea_phosporous = round(urea * 0)
                urea_potassium = round(urea * 0)

            # SSP Calculation - Nitrogen, Phosphorous, Potassium
                ssp_nitrogen = round(ssp * 0)
                ssp_phosporous = round(ssp * 8)
                ssp_potassium = round(ssp * 0)

            # MOP Calculation - Nitrogen, Phosphorous, Potassium
                mop_nitrogen = round(mop * 0)
                mop_phosporous = round(mop * 0)
                mop_potassium = round(mop * 30)

            # Total N, P, K
                nitrogen = daep_nitrogen + complex_nitrogen + urea_nitrogen + ssp_nitrogen + mop_nitrogen
                phosporous = daep_phosporous + complex_phosporous + urea_phosporous + ssp_phosporous + mop_phosporous
                potassium = daep_potassium + complex_potassium + urea_potassium + ssp_potassium + mop_potassium

                results = []
                finalres1 = []
                finalres2 = []
                finalres3 = []
                finalres4 = []
                total = []

                for i in fertilizers:
                    or_nitrogen = i.nitrogen
                    or_phosphorus = i.phosphorus
                    or_potassium = i.potassium

                # Required Quantity Of NPK
                    reqnpk_nitrogen = or_nitrogen - nitrogen
                    reqnpk_phosphorous = or_phosphorus - phosporous
                    reqnpk_potassium = or_potassium - potassium

                # Required Quantity of Fertilizers
                    req_ferti_N = round(reqnpk_nitrogen * 2.17)
                    req_ferti_P = round(reqnpk_phosphorous * 6.25)
                    req_ferti_K = round(reqnpk_potassium * 1.66)

                # Amount Required To Buy Fertilizers
                    req_amount_N = round(req_ferti_N * 5.31)
                    req_amount_P = round(req_ferti_P * 6)
                    req_amount_K = round(req_ferti_K * 12.04)

                    total.append({
                    'Total': {
                        'Total Nitrogen': nitrogen,
                        'Total Phosphorous': phosporous,
                        'Total Potassium': potassium
                      }
                    })
                    finalres1.append({
                    'Required quantity of NPK (kg/ha)': {
                        'Required Nitrogen': reqnpk_nitrogen,
                        'Required Phosphorous': reqnpk_phosphorous,
                        'Required Potassium': reqnpk_potassium
                    }
                    })
                    finalres2.append({
                    'Required quantity of Fertilizers (kg/ha)': {
                        'Required Nitrogen': req_ferti_N,
                        'Required Phosphorous': req_ferti_P,
                        'Required Potassium': req_ferti_K
                    }
                    })
                    finalres3.append({
                    'Amount Required to buy Fertilizers': {
                        'Amount N': req_amount_N,
                        'Amount P': req_amount_P,
                        'Amount K': req_amount_K
                    }
                    })
                    finalres4.append({
                    'Total Amount Required': req_amount_N + req_amount_P + req_amount_K
                    })

                results.append({
                'DAEP': {
                    'N': daep_nitrogen,
                    'P': daep_phosporous,
                    'K': daep_potassium
                },
                'Complex 17:17': {
                    'N': complex_nitrogen,
                    'P': complex_phosporous,
                    'K': complex_potassium
                },
                'Urea': {
                    'N': urea_nitrogen,
                    'P': urea_phosporous,
                    'K': urea_potassium
                },
                'SSP': {
                    'N': ssp_nitrogen,
                    'P': ssp_phosporous,
                    'K': ssp_potassium
                },
                'MOP': {
                    'N': mop_nitrogen,
                    'P': mop_phosporous,
                    'K': mop_potassium
                    }
                    })

                return Response({
                'message': 'Successful',
                'results': results,
                'total': total,
                'Required NPK': finalres1,
                'Required Fertilizer': finalres2,
                'Required Amount': finalres3,
                'Total Amount Required': finalres4
            }, status=status.HTTP_200_OK)
            else:
                return Response({
                'error': 'Invalid user type'
                }, status=status.HTTP_403_FORBIDDEN)
        
        except Exception as e:
            return Response({
            'error': 'An error occurred.',
            'details': str(e),
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#######################################---------------CROP Suggestion----###########################
class CropSuggestion(APIView):
    permission_classes = [IsAuthenticated]  
    def post(self, request,format=None):
        user=request.user
        current_month = timezone.now().month
        try:
            if user.user_type == "farmer":
                try:
                    farmer = FarmerProfile.objects.get(user=user)
                    user_language = farmer.fk_language.id
                except FarmerProfile.DoesNotExist:
                    return Response({'message': 'Farmer Not Found'}, status=status.HTTP_404_NOT_FOUND)
                suggested_crops = SuggestedCrop.objects.filter(
                start_month__lte=current_month,
                end_month__gte=current_month
                ).exclude(fk_crop__isnull=True)
                if  not suggested_crops.exists():
                    return Response({'status':'error','message':"No Crops were suggested during the current month"})
                crops_data = []
                for crop in suggested_crops:
                    crop_info = {
                        'crop_id': crop.fk_crop.id if crop.fk_crop else None,
                        'crop_name': None,
                        'crop_image': None
                                }
                    if crop.fk_crop:
                        if user_language == 1:  
                            crop_info['crop_name'] = crop.fk_crop.eng_crop.crop_name if crop.fk_crop.eng_crop else None
                        elif user_language == 2:  
                            crop_info['crop_name'] = crop.fk_crop.hin_crop.crop_name if crop.fk_crop.hin_crop else None
                        crop_images = CropImages.objects.filter(fk_cropmaster=crop.fk_crop)
                        if crop_images.exists():
                            crop_info['crop_image'] = crop_images.first().crop_image.url
                
                    crops_data.append(crop_info)
                return Response({'message': 'Successful', 'crops': crops_data}, status=status.HTTP_200_OK)

            else:
                return Response({'message': 'Invalid user type'}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({
            'error': 'An error occurred.',
            'details': str(e),
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self,request,format=None):
        user=request.user
        print(f"User is {user.user_type}")
        crop_id=request.query_params.get('crop_id')
        if not crop_id:
            return Response({'message':'Crop id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if user.user_type=="farmer":
                try:
                    farmer = FarmerProfile.objects.get(user=user)
                    user_language = farmer.fk_language.id
                except FarmerProfile.DoesNotExist:
                    return Response({'message': 'Farmer Not Found'}, status=status.HTTP_404_NOT_FOUND)
                try:
                    crop = CropMapper.objects.get(id=crop_id)
                except CropMapper.DoesNotExist:
                    return Response({'error': 'Crop not found'},status=status.HTTP_404_NOT_FOUND)
                suggested_crop = SuggestedCrop.objects.filter(fk_crop=crop, fk_language_id=user_language).first()
                if not suggested_crop:
                    return Response({'message': 'No suggested crop found for the given crop and language'}, status=status.HTTP_404_NOT_FOUND)

                serializer = SuggestedCropSerializer(suggested_crop,context={'user_language': user_language})
                return Response({'crop_details': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Invalid user type'}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({
            'error': 'An error occurred.',
            'details': str(e),
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                


##########################################------VEGETABLE POP-----------#########################################
def sync_multi_language_data(farmer, farm, crop_id, current_language_id,filter_type):
    all_languages = LanguageSelection.objects.all()
    for lang in all_languages:
        if lang.id != current_language_id:
            current_preferences = VegetablePreferenceCompletion.objects.filter(
                fk_farmer=farmer,
                fk_farmland=farm,
                fk_croptype_id=filter_type,
                fk_crop_id=crop_id,
                fk_language_id=current_language_id
            )
            print(f"Current Preferences are:{current_preferences}")

            for pref in current_preferences:
                existing_prefs = VegetablePreferenceCompletion.objects.filter(
                    fk_farmer=farmer,
                    fk_farmland=farm,
                    fk_crop_id=crop_id,
                    fk_croptype_id=filter_type,
                    fk_language_id=lang.id,
                    preference_number=pref.preference_number
                )
                print(f"Existing Preferences are:{existing_prefs}")

                if existing_prefs.exists():
                    existing_pref = existing_prefs.first()
                    existing_pref.name = pref.name
                    existing_pref.start_date = pref.start_date
                    existing_pref.completion_date = pref.completion_date
                    existing_pref.is_completed = pref.is_completed
                    existing_pref.total_days = pref.total_days
                    existing_pref.progress = pref.progress
                    existing_pref.save()
                else:
                    VegetablePreferenceCompletion.objects.create(
                        fk_farmer=farmer,
                        fk_farmland=farm,
                        fk_crop_id=crop_id,
                        fk_croptype_id=filter_type,
                        fk_language_id=lang.id,
                        preference_number=pref.preference_number,
                        name=pref.name,
                        start_date=pref.start_date,
                        completion_date=pref.completion_date,
                        is_completed=pref.is_completed,
                        total_days=pref.total_days,
                        progress=pref.progress
                    )

    # Sync VegetableStageCompletion
    for lang in all_languages:
        if lang.id != current_language_id:
            current_stages = VegetableStageCompletion.objects.filter(
                fk_farmer=farmer,
                fk_farmland=farm,
                fk_crop_id=crop_id,
                fk_croptype_id=filter_type,
                fk_language_id=current_language_id
            )

            for stage in current_stages:
                try:
                    target_vegetable_pop = VegetablePop.objects.get(
                        fk_crop_id=crop_id,
                        fk_language_id=lang.id,
                        fk_croptype_id=filter_type,
                        stage_number=stage.stage_number,
                        preference=stage.vegetable_pop.preference
                    )
                    print(f"Target vegetabel Pop :{target_vegetable_pop}")

                    existing_stages = VegetableStageCompletion.objects.filter(
                        vegetable_pop=target_vegetable_pop,
                        fk_farmer=farmer,
                        fk_farmland=farm,
                        fk_crop_id=crop_id,
                        fk_croptype_id=filter_type,
                        fk_language_id=lang.id,
                        stage_number=stage.stage_number,
                    )

                    if existing_stages.exists():
                        existing_stage = existing_stages.first()
                        existing_stage.start_date = stage.start_date
                        existing_stage.completion_date = stage.completion_date
                        existing_stage.is_completed = stage.is_completed
                        existing_stage.total_days_spent = stage.total_days_spent
                        existing_stage.save()
                    else:
                        VegetableStageCompletion.objects.create(
                            vegetable_pop=target_vegetable_pop,
                            fk_farmer=farmer,
                            fk_farmland=farm,
                            fk_crop_id=crop_id,
                            fk_croptype_id=filter_type,
                            fk_language_id=lang.id,
                            stage_number=stage.stage_number,
                            start_date=stage.start_date,
                            completion_date=stage.completion_date,
                            is_completed=stage.is_completed,
                            total_days_spent=stage.total_days_spent
                        )
                except VegetablePop.DoesNotExist:
                    return Response({'error': 'Vegetable Pop not found'}, status=status.HTTP_404_NOT_FOUND)
class VegetableStagesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @transaction.atomic
    def post(self, request, format=None):
        user = request.user
        farm_id = request.data.get('land_id')
        filter_type = request.data.get('filter_type')
        required_fields = ['land_id', 'filter_type']
        for field in required_fields:
            if not request.data.get(field):
                return Response({'message': f'Missing or empty field: {field}'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if user.user_type == "farmer":
                try:
                    farmer = FarmerProfile.objects.get(user=user)
                    user_language=farmer.fk_language.id
                    print(f"Farmer Language is :{farmer}")
                except FarmerProfile.DoesNotExist:
                    return Response({'message': 'Farmer Not Found'}, status=status.HTTP_404_NOT_FOUND)
                farm = None
                if farm_id:
                    try:
                        farm = FarmerLandAddress.objects.get(id=farm_id, fk_farmer=farmer)
                        print(f"Farm Id is :{farm}")
                        crop_id=farm.fk_crops.id
                        print(f"Crops Id is :{crop_id}")
                    except FarmerLandAddress.DoesNotExist:
                        return Response({'error': 'Invalid farmer land ID'}, status=status.HTTP_404_NOT_FOUND)

                # Synchronize data across all languages
                sync_multi_language_data(farmer, farm, crop_id, user_language,filter_type)

                veges = VegetablePop.objects.filter(
                    fk_crop_id=crop_id,
                    fk_language_id=user_language,
                    fk_croptype_id=filter_type
                ).order_by("preference", "stage_number")

                today = timezone.now().date()
                stage_data = []
                preference_data = []

                preferences = VegetablePop.objects.filter(
                    fk_crop_id=crop_id,
                    fk_croptype_id=filter_type,
                    fk_language_id=user_language
                ).values('preference', 'stages').distinct().order_by('preference')

                preference_completion_map = {}
                for pref in preferences:
                    try:
                        preference_completion = VegetablePreferenceCompletion.objects.get(
                        fk_farmer=farmer,
                        fk_farmland=farm,
                        fk_crop_id=crop_id,
                        fk_language_id=user_language,
                        fk_croptype_id=filter_type,
                        preference_number=pref['preference'],
                            )
                        created = False
                    except VegetablePreferenceCompletion.MultipleObjectsReturned:
                        preference_completion = VegetablePreferenceCompletion.objects.filter(
                                                fk_farmer=farmer,
                                                fk_farmland=farm,
                                                fk_crop_id=crop_id,
                                                fk_language_id=user_language,
                                                fk_croptype_id=filter_type,
                                                preference_number=pref['preference']
                                                ).first()
                    except VegetablePreferenceCompletion.DoesNotExist:
                        preference_completion = VegetablePreferenceCompletion.objects.create(
                                                fk_farmer=farmer,
                                                fk_farmland=farm,
                                                fk_crop_id=crop_id,
                                                fk_language_id=user_language,
                                                fk_croptype_id=filter_type,
                                                preference_number=pref['preference'],
                                                name=pref['stages'],
                                                start_date=None
                                                    )
                        created = True
                    preference_completion_map[pref['preference']] = preference_completion
                    print(f"Preference Complete for :{preference_completion}")

                for vege in veges:
                    stage_completion, created = VegetableStageCompletion.objects.get_or_create(
                        vegetable_pop=vege,
                        fk_farmer=farmer,
                        fk_farmland=farm,
                        fk_language_id=user_language,
                        fk_croptype_id=filter_type,
                        fk_crop_id=crop_id,
                        stage_number=vege.stage_number,
                        defaults={'start_date': None}
                    )

                    preference_completion = preference_completion_map.get(vege.preference)

                    if preference_completion:
                        if vege.preference == 1:
                            if stage_completion.start_date is None:
                                stage_completion.start_date = today
                                stage_completion.save()
                        
                            if preference_completion.start_date is None:
                                preference_completion.start_date = today
                                preference_completion.save()
                        else:
                            previous_preferences = [p for p in preference_completion_map if p < vege.preference]
                            all_previous_completed = all(
                                preference_completion_map[p].is_completed
                                for p in previous_preferences
                                if preference_completion_map.get(p)
                            )

                            if all_previous_completed:
                                if stage_completion.start_date is None:
                                    if previous_preferences:
                                        previous_preference = max(previous_preferences)
                                        previous_preference_completion = preference_completion_map.get(previous_preference)
                                    if previous_preference_completion and previous_preference_completion.completion_date:
                                        stage_completion.start_date = previous_preference_completion.completion_date
                                    else:
                                        stage_completion.start_date = today
                            else:
                                stage_completion.start_date = today
                            stage_completion.save()
                         
                        if preference_completion.start_date is None:
                            preference_completion.start_date = stage_completion.start_date
                            preference_completion.save()

                    # Calculate progress for this preference
                    total_stages = VegetablePop.objects.filter(
                        fk_crop_id=crop_id,
                        preference=vege.preference,
                        fk_croptype_id=filter_type,
                        fk_language_id=user_language
                    ).count()

                    completed_stages = VegetableStageCompletion.objects.filter(
                        fk_farmer=farmer,
                        fk_farmland=farm,
                        vegetable_pop__fk_crop_id=crop_id,
                        fk_croptype_id=filter_type,
                        fk_language_id=user_language,
                        fk_crop_id=crop_id,
                        vegetable_pop__preference=vege.preference,
                        is_completed=True
                    ).count()

                    progress = int((completed_stages / total_stages) * 100) if total_stages > 0 else 0
                    if preference_completion:
                        preference_completion.progress = progress
                        preference_completion.save()

                        if progress == 100 and not preference_completion.is_completed:
                            preference_completion.is_completed = True
                            preference_completion.completion_date = today
                            preference_completion.total_days = (today - preference_completion.start_date).days if preference_completion.start_date else 0
                            preference_completion.save()
                            
                            next_preference = vege.preference + 1
                            next_preference_stages = VegetablePop.objects.filter(
                                fk_crop_id=crop_id,
                                preference=next_preference,
                                fk_language_id=user_language,
                                fk_croptype_id=filter_type
                            ).order_by('stage_number')
                            
                            if next_preference_stages.exists():
                                try:
                                    next_preference_completion = VegetablePreferenceCompletion.objects.get(
                                                        fk_farmer=farmer,
                                                        fk_farmland=farm,
                                                        fk_crop_id=crop_id,
                                                        fk_language_id=user_language,
                                                        fk_croptype_id=filter_type,
                                                        preference_number=next_preference
                                                        )
                                except VegetablePreferenceCompletion.MultipleObjectsReturned:
                                    next_preference_completion = VegetablePreferenceCompletion.objects.filter(
                                                            fk_farmer=farmer,
                                                            fk_farmland=farm,
                                                            fk_crop_id=crop_id,
                                                            fk_language_id=user_language,
                                                            fk_croptype_id=filter_type,
                                                            preference_number=next_preference
                                                                ).first()
                                except VegetablePreferenceCompletion.DoesNotExist:
                                    next_preference_completion = VegetablePreferenceCompletion.objects.create(
                                                                fk_farmer=farmer,
                                                                fk_farmland=farm,
                                                                fk_crop_id=crop_id,
                                                                fk_language_id=user_language,
                                                                fk_croptype_id=filter_type,
                                                                preference_number=next_preference,
                                                                start_date=today,
                                                                is_completed=False,
                                                                progress=0
                                                                        )
                                print(f"Next Prefrences Data :{next_preference_completion}")
                            if not created:
                                next_preference_completion = VegetablePreferenceCompletion.objects.filter(
                                                        fk_farmer=farmer,fk_farmland=farm,fk_crop_id=crop_id,
                                                         fk_language_id=user_language,fk_croptype_id=filter_type,
                                                        preference_number=next_preference).first()

                                for next_stage in next_preference_stages:
                                    VegetableStageCompletion.objects.get_or_create(
                                        vegetable_pop=next_stage,
                                        fk_farmer=farmer,
                                        fk_farmland=farm,
                                        fk_croptype_id=filter_type,
                                        fk_crop_id=crop_id,
                                        fk_language_id=user_language,
                                        stage_number=next_stage.stage_number,
                                        defaults={'start_date': today, 'is_completed': False, 'total_days_spent': 0}
                                    )

                    products = []
                    for product in vege.fk_product.all():
                        suppliers = product.fk_supplier.all()
                        supplier_ids = [supplier.id for supplier in suppliers]
                        latest_price = ProductPrices.objects.filter(fk_product=product).order_by('-id').first()
                        product_data = {
                            'product_id': product.id,
                            'product_name': product.productName,
                            'product_image': product.product_image.url if product.product_image else None,
                            'product_description': product.productDescription,
                            'Category': product.Category,
                            'supplier_ids': supplier_ids,
                            'price': latest_price.unit_price if latest_price else None
                        }
                        products.append(product_data)

                    # Add stage data to stage_data list
                    stage_data.append({
                        'stage_id': vege.id,
                        'stages': vege.stages,
                        'stage_name': vege.stage_name,
                        "stage_audio": vege.audio.url if vege.audio else None,
                        'stage_video': vege.video.url if vege.video else None, 
                        'sow_period': vege.sow_period,
                        'description': vege.description,
                        'stage_number': vege.stage_number,
                        'preference': vege.preference,
                        'is_completed': stage_completion.is_completed,
                        'days_spent': stage_completion.total_days_spent,
                        'start_date': stage_completion.start_date,
                        'user_language':user_language,
                        'products': products
                    })

                for preference_number, preference_completion in preference_completion_map.items():
                    preference_data.append({
                        'preference_id': preference_completion.id,
                        'stages': preference_completion.name,
                        'is_completed': preference_completion.is_completed,
                        'preference_number': preference_completion.preference_number
                    })

                return Response({'stages': stage_data, 'preferences': preference_data})
    
        except Exception as e:
            return Response({
                'error': 'An error occurred.',
                'details': str(e),
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

###-------Mark Stage Complete
class MarkVegetableStageCompleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, format=None):
        user = request.user
        farm_id = request.data.get('land_id')
        filter_type = request.data.get('filter_type')
        preference_number = request.data.get('preference_number')
        submit_task = request.FILES.get('submit_task')

        required_fields = ['land_id', 'filter_type', 'preference_number']
        for field in required_fields:
            if not request.data.get(field):
                return Response({'message': f'Missing or empty field: {field}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if user.user_type == "farmer":
                try:
                    farmer = FarmerProfile.objects.get(user=user)
                    user_language=farmer.fk_language.id
                    print(f"Farmer Language is :{farmer}")
                except FarmerProfile.DoesNotExist:
                    return Response({'message': 'Farmer Not Found'}, status=status.HTTP_404_NOT_FOUND)

                farm = None
                if farm_id:
                    try:
                        farm = FarmerLandAddress.objects.get(id=farm_id, fk_farmer=farmer)
                        crop_id=farm.fk_crops.id
                        print(f"Crops Id is :{crop_id}")
                    except FarmerLandAddress.DoesNotExist:
                        return Response({'error': 'Invalid farmer land ID'}, status=status.HTTP_404_NOT_FOUND)

                with transaction.atomic():
                    stages = VegetablePop.objects.filter(
                        fk_crop_id=crop_id,
                        preference=preference_number,
                        fk_croptype_id=filter_type,
                        fk_language_id=user_language
                    )
                    print(f"Stages are :{stages}")

                    if not stages.exists():
                        return Response({'message': 'No stages found for this preference'}, status=status.HTTP_404_NOT_FOUND)

                    today = timezone.now().date()
                    completed_stages_data = []

                    for stage in stages:
                        stage_completions = VegetableStageCompletion.objects.filter(
                            vegetable_pop=stage,
                            fk_farmer=farmer,
                            fk_farmland=farm,
                            fk_croptype_id=filter_type,
                            fk_crop_id=crop_id,
                            fk_language_id=user_language,
                            stage_number=stage.stage_number
                        )
                        print(f"Stage completions are :{stage_completions}")

                        if stage_completions.exists():
                            stage_completion = stage_completions.first()
                            stage_completion.completion_date = today
                            stage_completion.is_completed = True
                            if stage_completion.start_date:
                                stage_completion.total_days_spent = (today - stage_completion.start_date).days
                            else:
                                stage_completion.start_date = today
                                stage_completion.total_days_spent = 0
                            stage_completion.save()
                        else:
                            stage_completion, created = VegetableStageCompletion.objects.get_or_create(
                                vegetable_pop=stage,
                                fk_farmer=farmer,
                                fk_farmland=farm,
                                fk_croptype_id=filter_type,
                                fk_crop_id=crop_id,
                                fk_language_id=user_language,
                                stage_number=stage.stage_number,
                                defaults={'start_date': today, 'completion_date': today, 'is_completed': True, 'total_days_spent': 0}
                            )
                            print(f"Stage Completion : {stage_completion}")

                        completed_stages_data.append({
                            'stage_id': stage_completion.vegetable_pop.id,
                            'stage_number': stage_completion.stage_number,
                            'days_to_complete': stage_completion.total_days_spent,
                            'user_language':user_language,
                            'preference_number': stage.preference
                        })

                    # Handle preference completion
                    preference_completion_queryset = VegetablePreferenceCompletion.objects.filter(
                        fk_farmer=farmer,
                        fk_farmland=farm,
                        fk_crop_id=crop_id,
                        fk_croptype_id=filter_type,
                        fk_language_id=user_language,
                        preference_number=preference_number
                    )

                    if preference_completion_queryset.exists():
                        preference_completion = preference_completion_queryset.latest('id')
                        preference_completion.completion_date = today
                        preference_completion.is_completed = True
                        if preference_completion.start_date:
                            preference_completion.total_days = (today - preference_completion.start_date).days
                        else:
                            preference_completion.start_date = today
                            preference_completion.total_days = 0
                        preference_completion.progress = 100
                        preference_completion.save()
                    else:
                        preference_completion = VegetablePreferenceCompletion.objects.create(
                            fk_farmer=farmer,
                            fk_farmland=farm,
                            fk_crop_id=crop_id,
                            fk_croptype_id=filter_type,
                            fk_language_id=user_language,
                            preference_number=preference_number,
                            start_date=today,
                            completion_date=today,
                            is_completed=True,
                            total_days=0,
                            progress=100
                        )
                        print(f"Preference Completion :{preference_completion}")

                    # Initialize the next preference
                    next_preference_number = int(preference_number) + 1
                    next_preference_stages = VegetablePop.objects.filter(
                        fk_crop_id=crop_id,
                        preference=next_preference_number,
                        fk_language_id=user_language,
                        fk_croptype_id=filter_type
                    ).order_by('stage_number')
                    print(f"Next Preference Stages are :{next_preference_stages}")

                    if next_preference_stages.exists():
                        VegetablePreferenceCompletion.objects.get_or_create(
                            fk_farmer=farmer,
                            fk_farmland=farm,
                            fk_crop_id=crop_id,
                            fk_language_id=user_language,
                            fk_croptype_id=filter_type,
                            preference_number=next_preference_number,
                            defaults={'start_date': today, 'is_completed': False, 'progress': 0}
                        )

                        for next_stage in next_preference_stages:
                            VegetableStageCompletion.objects.get_or_create(
                                vegetable_pop=next_stage,
                                fk_farmer=farmer,
                                fk_farmland=farm,
                                fk_croptype_id=filter_type,
                                fk_crop_id=crop_id,
                                fk_language_id=user_language,
                                stage_number=next_stage.stage_number,
                                defaults={'start_date': today, 'is_completed': False, 'total_days_spent': 0}
                            )

                    sync_multi_language_data(farmer, farm, crop_id, user_language, filter_type)

                    coins_added = 20 if submit_task else 10
                    farmer.coins += coins_added
                    farmer.save()

                    return Response({
                        'completed_stages': completed_stages_data,
                        'coins_added': coins_added,
                        'total_coins': farmer.coins
                    })

            else:
                return Response({'message': 'User is not a farmer'}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            return Response({
                'message': 'An error occurred',
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#######------------Vegetable Progress
class VegetableProgressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        crops_data = request.data.get('crops')

        if not crops_data or not isinstance(crops_data, list):
            return Response({'message': 'Invalid or missing crops data'}, status=status.HTTP_400_BAD_REQUEST)

        if user.user_type != "farmer":
            return Response({'message': 'User is not a farmer'}, status=status.HTTP_403_FORBIDDEN)

        try:
            farmer = FarmerProfile.objects.get(user=user)
            user_language = farmer.fk_language.id
        except FarmerProfile.DoesNotExist:
            return Response({'message': 'Farmer Not Found'}, status=status.HTTP_404_NOT_FOUND)

        crops_progress = []
        crops_with_no_data = []

        for crop_data in crops_data:
            land_id = crop_data.get('land_id')
            filter_type = crop_data.get('filter_type')

            if not land_id or not filter_type:
                continue

            try:
                farm = FarmerLandAddress.objects.get(id=land_id, fk_farmer=farmer)
                crop_id = farm.fk_crops.id
            except FarmerLandAddress.DoesNotExist:
                crops_with_no_data.append({'land_id': land_id, 'filter_type': filter_type, 'error': 'Invalid farmer land ID'})
                continue

            total_preferences = VegetablePop.objects.filter(
                fk_crop_id=crop_id,
                fk_croptype_id=filter_type,
                fk_language=user_language
            ).values('preference').distinct().count()
            crop_images=CropImages.objects.get(fk_cropmaster=crop_id)
            crop_image=crop_images.crop_image.url
            crop_mapper = crop_images.fk_cropmaster
            if user_language == 1:
                crop_name = crop_mapper.eng_crop.crop_name  
            elif user_language == 2:
                crop_name = crop_mapper.hin_crop.crop_name  

            if total_preferences == 0:
                crops_with_no_data.append({'land_id': land_id, 'filter_type': filter_type, 'error': 'No preferences found'})
                continue

            preference_progress = VegetablePreferenceCompletion.objects.filter(
                fk_farmer=farmer,
                fk_farmland=farm,
                fk_croptype_id=filter_type,
                fk_crop_id=crop_id,
                fk_language=user_language
            ).values('preference_number', 'progress', 'is_completed', 'name')

            completed_preferences = sum(1 for pref in preference_progress if pref['is_completed'])
            overall_progress = (completed_preferences / total_preferences) * 100

            crop_progress = {
                'land_id': land_id,
                'crop_id': crop_id,
                'crop_name': crop_name,
                'crop_image':crop_image,
                'user_language': user_language,
                'filter_type': filter_type,
                'overall_progress': round(overall_progress, 2),
                'total_preferences': total_preferences,
                'completed_preferences': completed_preferences,
                'preference_details': list(preference_progress)
            }

            crops_progress.append(crop_progress)

        response_data = {}
        if crops_progress:
            response_data['crops_progress'] = crops_progress
        if crops_with_no_data:
            response_data['crops_with_no_data'] = crops_with_no_data

        status_code = status.HTTP_200_OK if crops_progress else status.HTTP_404_NOT_FOUND
        if crops_with_no_data:
            status_code = status.HTTP_206_PARTIAL_CONTENT

        return Response(response_data, status=status_code)
#######-----------------Weather Notifcation
class GetVegetablePopNotification(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data 
        crops = data.get('crops', [])  

        if not crops:
            return Response({'message': 'Missing or empty field: crops'}, status=status.HTTP_400_BAD_REQUEST)
        try:

            responses = []
            for crop in crops:
                crop_id = crop.get('crop_id')
                land_id = crop.get('land_id')
                filter_type = crop.get('filter_type')
                weather_conditions = crop.get('weather_conditions', [])

                if not filter_type:
                    return Response({'message': f'Missing or empty field: filter_type, for crop_id {crop_id}'}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    farmer = FarmerProfile.objects.get(user=request.user)
                    user_language=farmer.fk_language.id
                except FarmerProfile.DoesNotExist:
                    return Response({'message': 'Farmer Not Found'}, status=status.HTTP_404_NOT_FOUND)

                farm=None
                if land_id:
                    try:
                        farm = FarmerLandAddress.objects.get(id=land_id, fk_farmer=farmer)
                        crop_id=farm.fk_crops.id
                        print(f"Crops Id is :{crop_id}")
                    except FarmerLandAddress.DoesNotExist:
                        return Response({'error': 'Invalid farmer land ID'}, status=status.HTTP_404_NOT_FOUND)

                preference_completion = VegetablePreferenceCompletion.objects.filter(
                fk_farmer=farmer,
                fk_farmland=farm,
                fk_crop_id=crop_id,
                fk_croptype_id=filter_type,
                is_completed=False
                    ).order_by('preference_number').first()
                print(f"Preferences Found:{preference_completion}")

                if not preference_completion:
                    return Response({'results': []}, status=status.HTTP_200_OK)

                preference_completion_serializer = VegetablePrefrencesSerializer(preference_completion)
                print(f"Prefrences Found:{preference_completion_serializer.data}")
                notification_messages = WeatherPopNotification.objects.filter(
                fk_weather_condition__condition__in=weather_conditions,
                preference_number=preference_completion.preference_number,
                fk_language_id=user_language,
                fk_crops_id=crop_id,
                fk_croptype_id=filter_type
                                 ).distinct()
                print(f"Notification Messages Found:{notification_messages}")

                if notification_messages.exists():
                    notification_serializers = WeatherNotificationSerializer(notification_messages, many=True)
                    responses.append({
                    'crop_id': int(crop_id),
                    'notifications': notification_serializers.data
                    })
                else:
                    responses.append({
                    'message': 'No notification found for the current weather conditions and preference',
                })

            return Response({'results': responses}, status=status.HTTP_200_OK)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
##########################################---------------SPICES POP---------#########################################
class SpicesStagesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        user = request.user
        crop_id = request.data.get('crop_id')
        farm_id=request.data.get('land_id')
        filter_type = request.data.get('filter_type')
        user_language = request.data.get('user_language')

        required_fields = ['crop_id', 'filter_type', 'user_language']
        for field in required_fields:
            if not request.data.get(field):
                return Response({'message': f'Missing or empty field: {field}'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if user.user_type == "farmer":
                try:
                    farmer = FarmerProfile.objects.get(user=user)
                except FarmerProfile.DoesNotExist:
                    return Response({'message': 'Farmer Not Found'}, status=status.HTTP_404_NOT_FOUND)
                farm=None
                if farm_id:
                    try:
                        farm = FarmerLandAddress.objects.get(id=farm_id, fk_farmer=farmer, fk_crops__id=crop_id)
                    except FarmerLandAddress.DoesNotExist:
                        return Response({'error': 'Invalid farmer land ID'}, status=status.HTTP_404_NOT_FOUND)

                veges = SpicesPop.objects.filter(
                    fk_crop_id=crop_id,
                    fk_language_id=user_language,
                    fk_croptype_id=filter_type
                ).order_by("preference", "stage_number")

                today = timezone.now().date()
                stage_data = []
                preference_data = []

                preferences = SpicesPop.objects.filter(
                    fk_crop_id=crop_id,
                    fk_croptype_id=filter_type,
                    fk_language_id=user_language
                ).values('preference', 'stages').distinct().order_by('preference')

                preference_completion_map = {}
                for pref in preferences:
                    preference_completion, created = SpicesPreferenceCompletion.objects.get_or_create(
                        fk_farmer=farmer,
                        fk_farmland=farm,
                        fk_crop_id=crop_id,
                        fk_language_id=user_language,
                        fk_croptype_id=filter_type,
                        preference_number=pref['preference'],
                        name=pref['stages'],
                        defaults={'start_date': None}
                    )
                    preference_completion_map[pref['preference']] = preference_completion

                for vege in veges:
                    stage_completions = SpicestageCompletion.objects.filter(
                        spice_pop=vege,
                        fk_farmer=farmer,
                        fk_farmland=farm,
                        fk_language_id=user_language,
                        fk_croptype_id=filter_type,
                        fk_crop_id=crop_id,
                        stage_number=vege.stage_number
                    )

                    if stage_completions.exists():
                        stage_completion = stage_completions.first()
                    else:
                        stage_completion, created = SpicestageCompletion.objects.get_or_create(
                            spice_pop=vege,
                            fk_farmer=farmer,
                            fk_farmland=farm,
                            fk_language_id=user_language,
                            fk_croptype_id=filter_type,
                            fk_crop_id=crop_id,
                            stage_number=vege.stage_number,
                            defaults={'start_date': None}
                        )

                    preference_completion = preference_completion_map.get(vege.preference)

                    if preference_completion:
                        if vege.preference == 1:
                            if stage_completion.start_date is None:
                                stage_completion.start_date = today
                                stage_completion.save()
                        
                            if preference_completion.start_date is None:
                                preference_completion.start_date = today
                                preference_completion.save()
                        else:
                            previous_preferences = [p for p in preference_completion_map if p < vege.preference]
                            all_previous_completed = all(
                                preference_completion_map[p].is_completed
                                for p in previous_preferences
                                if preference_completion_map.get(p)
                            )

                            if all_previous_completed:
                                if stage_completion.start_date is None:
                                    if previous_preferences:
                                        previous_preference = max(previous_preferences)
                                        previous_preference_completion = preference_completion_map.get(previous_preference)
                                    if previous_preference_completion and previous_preference_completion.completion_date:
                                        stage_completion.start_date = previous_preference_completion.completion_date
                                    else:
                                        stage_completion.start_date = today
                            else:
                                stage_completion.start_date = today
                            stage_completion.save()
                         
                        if preference_completion.start_date is None:
                            preference_completion.start_date = stage_completion.start_date
                            preference_completion.save()

                    # Calculate progress for this preference
                    total_stages = SpicesPop.objects.filter(
                        fk_crop_id=crop_id,
                        preference=vege.preference,
                        fk_croptype_id=filter_type,
                        fk_language_id=user_language
                    ).count()

                    completed_stages = SpicestageCompletion.objects.filter(
                        fk_farmer=farmer,
                        fk_farmland=farm,
                        spice_pop__fk_crop_id=crop_id,
                        fk_croptype_id=filter_type,
                        fk_language_id=user_language,
                        fk_crop_id=crop_id,
                        spice_pop__preference=vege.preference,
                        is_completed=True
                    ).count()

                    progress = int((completed_stages / total_stages) * 100) if total_stages > 0 else 0
                    if preference_completion:
                        preference_completion.progress = progress
                        preference_completion.save()

                        if progress == 100 and not preference_completion.is_completed:
                            preference_completion.is_completed = True
                            preference_completion.completion_date = today
                            preference_completion.total_days = (today - preference_completion.start_date).days if preference_completion.start_date else 0
                            preference_completion.save()
                            
                            next_preference = vege.preference + 1
                            next_preference_stages = SpicesPop.objects.filter(
                                fk_crop_id=crop_id,
                                preference=next_preference,
                                fk_language_id=user_language,
                                fk_croptype_id=filter_type
                            ).order_by('stage_number')
                            
                            if next_preference_stages.exists():
                                next_preference_completion, _ = SpicesPreferenceCompletion.objects.get_or_create(
                                    fk_farmer=farmer,
                                    fk_farmland=farm,
                                    fk_crop_id=crop_id,
                                    fk_language_id=user_language,
                                    fk_croptype_id=filter_type,
                                    preference_number=next_preference,
                                    defaults={'start_date': today, 'is_completed': False, 'progress': 0}
                                )
                                for next_stage in next_preference_stages:
                                    SpicestageCompletion.objects.get_or_create(
                                        spice_pop=next_stage,
                                        fk_farmer=farmer,
                                        fk_farmland=farm,
                                        fk_croptype_id=filter_type,
                                        fk_crop_id=crop_id,
                                        fk_language_id=user_language,
                                        stage_number=next_stage.stage_number,
                                        defaults={'start_date': today, 'is_completed': False, 'total_days_spent': 0}
                                    )

                    products = []
                    for product in vege.fk_product.all():
                        suppliers = product.fk_supplier.all()
                        supplier_ids = [supplier.id for supplier in suppliers]
                        latest_price = ProductPrices.objects.filter(fk_product=product).order_by('-id').first()
                        product_data = {
                            'product_id': product.id,
                            'product_name': product.productName,
                            'product_image': product.product_image.url if product.product_image else None,
                            'product_description': product.productDescription,
                            'Category': product.Category,
                            'supplier_ids': supplier_ids,
                            'price': latest_price.unit_price if latest_price else None
                                    }
                        products.append(product_data)

                    # Add stage data to stage_data list
                    stage_data.append({
                        'stage_id': vege.id,
                        'stages': vege.stages,
                        'stage_name': vege.stage_name,
                        "stage_audio": vege.audio.url if vege.audio else None, 
                        'sow_period': vege.sow_period,
                        'description': vege.description,
                        'stage_number': vege.stage_number,
                        'preference': vege.preference,
                        'is_completed': stage_completion.is_completed,
                        'days_spent': stage_completion.total_days_spent,
                        'start_date': stage_completion.start_date,
                        'products': products
                    })

                for preference_number, preference_completion in preference_completion_map.items():
                    preference_data.append({
                        'preference_id': preference_completion.id,
                        'stages': preference_completion.name,
                        'is_completed': preference_completion.is_completed,
                        'preference_number': preference_completion.preference_number
                    })

                return Response({'stages': stage_data, 'preferences': preference_data})
    
        except Exception as e:
            return Response({
                'error': 'An error occurred.',
                'details': str(e),
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

###-------Mark Stage Complete
class MarkSpiceStageCompleteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        user = request.user
        crop_id = request.data.get('crop_id')
        farm_id=request.data.get('land_id')
        filter_type = request.data.get('filter_type')
        preference_number = request.data.get('preference_number')
        submit_task = request.FILES.get('submit_task')
        user_language = request.data.get('user_language')

        required_fields = ['crop_id', 'filter_type', 'preference_number', 'user_language']
        for field in required_fields:
            if not request.data.get(field):
                return Response({'message': f'Missing or empty field: {field}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if user.user_type == "farmer":
                try:
                    farmer = FarmerProfile.objects.get(user=user)
                except FarmerProfile.DoesNotExist:
                    return Response({'message': 'Farmer Not Found'}, status=status.HTTP_404_NOT_FOUND)
                farm=None
                if farm_id:
                    try:
                        farm = FarmerLandAddress.objects.get(id=farm_id, fk_farmer=farmer, fk_crops__id=crop_id)
                    except FarmerLandAddress.DoesNotExist:
                        return Response({'error': 'Invalid farmer land ID'}, status=status.HTTP_404_NOT_FOUND)

                with transaction.atomic():
                    stages = SpicesPop.objects.filter(
                        fk_crop_id=crop_id,
                        preference=preference_number,
                        fk_croptype_id=filter_type,
                        fk_language_id=user_language
                    )

                    if not stages.exists():
                        return Response({'message': 'No stages found for this preference'}, status=status.HTTP_404_NOT_FOUND)

                    today = timezone.now().date()
                    completed_stages_data = []

                    for stage in stages:
                        stage_completions = SpicestageCompletion.objects.filter(
                            spice_pop=stage,
                            fk_farmer=farmer,
                            fk_farmland=farm,
                            fk_croptype_id=filter_type,
                            fk_crop_id=crop_id,
                            fk_language_id=user_language,
                            stage_number=stage.stage_number
                        )

                        if stage_completions.exists():
                            stage_completion = stage_completions.first()
                            stage_completion.completion_date = today
                            stage_completion.is_completed = True
                            if stage_completion.start_date:
                                stage_completion.total_days_spent = (today - stage_completion.start_date).days
                            else:
                                stage_completion.start_date = today
                                stage_completion.total_days_spent = 0
                            stage_completion.save()
                        else:
                            stage_completion, created = SpicestageCompletion.objects.get_or_create(
                                spice_pop=stage,
                                fk_farmer=farmer,
                                fk_farmland=farm,
                                fk_croptype_id=filter_type,
                                fk_crop_id=crop_id,
                                fk_language_id=user_language,
                                stage_number=stage.stage_number,
                                defaults={'start_date': today, 'completion_date': today, 'is_completed': True, 'total_days_spent': 0}
                            )

                        completed_stages_data.append({
                            'stage_id': stage_completion.spice_pop.id,
                            'stage_number': stage_completion.stage_number,
                            'days_to_complete': stage_completion.total_days_spent,
                            'preference_number': stage.preference
                        })

                    # Handle preference completion
                    preference_completion, created = SpicesPreferenceCompletion.objects.get_or_create(
                        fk_farmer=farmer,
                        fk_farmland=farm,
                        fk_crop_id=crop_id,
                        fk_croptype_id=filter_type,
                        fk_language_id=user_language,
                        preference_number=preference_number,
                        defaults={'start_date': today, 'completion_date': today, 'is_completed': True, 'total_days': 0, 'progress': 100}
                    )

                    if not created:
                        preference_completion.completion_date = today
                        preference_completion.is_completed = True
                        if preference_completion.start_date:
                            preference_completion.total_days = (today - preference_completion.start_date).days
                        else:
                            preference_completion.start_date = today
                            preference_completion.total_days = 0
                        preference_completion.progress = 100
                        preference_completion.save()

                    # Initialize the next preference
                    next_preference_number = int(preference_number) + 1
                    next_preference_stages = SpicesPop.objects.filter(
                        fk_crop_id=crop_id,
                        preference=next_preference_number,
                        fk_language_id=user_language,
                        fk_croptype_id=filter_type
                    ).order_by('stage_number')

                    if next_preference_stages.exists():
                        next_preference_completion, _ = SpicesPreferenceCompletion.objects.get_or_create(
                            fk_farmer=farmer,
                            fk_farmland=farm,
                            fk_crop_id=crop_id,
                            fk_language_id=user_language,
                            fk_croptype_id=filter_type,
                            preference_number=next_preference_number,
                            defaults={'start_date': today, 'is_completed': False, 'progress': 0}
                        )

                        for next_stage in next_preference_stages:
                            SpicestageCompletion.objects.get_or_create(
                                spice_pop=next_stage,
                                fk_farmer=farmer,
                                fk_farmland=farm,
                                fk_croptype_id=filter_type,
                                fk_crop_id=crop_id,
                                fk_language_id=user_language,
                                stage_number=next_stage.stage_number,
                                defaults={'start_date': today, 'is_completed': False, 'total_days_spent': 0}
                            )

                    coins_added = 20 if submit_task else 10
                    farmer.coins += coins_added
                    farmer.save()

                    return Response({
                        'completed_stages': completed_stages_data,
                        'coins_added': coins_added,
                        'total_coins': farmer.coins
                    })
            else:
                return Response({'message': 'User is not a farmer'}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            return Response({
                'message': 'An error occurred',
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#######------------Spices Progress
class SpicesProgressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        crop_id = request.query_params.get('crop_id')
        farm_id=request.query_params.get('land_id')
        filter_type = request.query_params.get('filter_type')

        if not crop_id or not filter_type:
            return Response({'message': 'Missing crop_id or filter_type'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if user.user_type == "farmer":
                try:
                    farmer = FarmerProfile.objects.get(user=user)
                except FarmerProfile.DoesNotExist:
                    return Response({'message': 'Farmer Not Found'}, status=status.HTTP_404_NOT_FOUND)
                farm=None
                if farm_id:
                    try:
                        farm = FarmerLandAddress.objects.get(id=farm_id, fk_farmer=farmer, fk_crops__id=crop_id)
                    except FarmerLandAddress.DoesNotExist:
                        return Response({'error': 'Invalid farmer land ID'}, status=status.HTTP_404_NOT_FOUND)

                total_preferences = SpicesPop.objects.filter(
                    fk_crop_id=crop_id,
                    fk_croptype_id=filter_type
                ).values('preference').distinct().count()

                if total_preferences == 0:
                    return Response({'message': 'No preferences found for this crop'}, status=status.HTTP_404_NOT_FOUND)

                completed_preferences = SpicesPreferenceCompletion.objects.filter(
                    fk_farmer=farmer,
                    fk_farmland=farm,
                    fk_crop_id=crop_id,
                    fk_croptype_id=filter_type,
                    is_completed=True
                ).count()

                overall_progress = (completed_preferences / total_preferences) * 100

                preference_progress = SpicesPreferenceCompletion.objects.filter(
                    fk_farmer=farmer,
                    fk_farmland=farm,
                    fk_croptype_id=filter_type,
                    fk_crop_id=crop_id
                ).values('preference_number', 'progress', 'is_completed', 'name')

                response_data = {
                    'overall_progress': round(overall_progress, 2),
                    'total_preferences': total_preferences,
                    'completed_preferences': completed_preferences,
                    'preference_details': list(preference_progress)
                }

                return Response(response_data)
            else:
                return Response({'message': 'User is not a farmer'}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )   
##--------Spices WQeather Notifications
class GetSpicesPopNotification(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        data = request.query_params  
        user_language = data.get('user_language')
        crop_id = data.get('crop_id')
        farm_id = data.get('land_id')
        filter_type = data.get('filter_type')
        weather_condition = data.get('weather_condition', [])

        required_fields = ['crop_id', 'filter_type', 'user_language']
        for field in required_fields:
            if not data.get(field):
                return Response({'message': f'Missing or empty field: {field}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if user.user_type == "farmer":
                try:
                    farmer = FarmerProfile.objects.get(user=user)
                except FarmerProfile.DoesNotExist:
                    return Response({'message': 'Farmer Not Found'}, status=status.HTTP_404_NOT_FOUND)

                farm = None
                if farm_id:
                    try:
                        farm = FarmerLandAddress.objects.get(id=farm_id, fk_farmer=farmer, fk_crops__id=crop_id)
                    except FarmerLandAddress.DoesNotExist:
                        return Response({'message': 'Land not Found'}, status=status.HTTP_404_NOT_FOUND)
                
                preference_completion = SpicesPreferenceCompletion.objects.filter(
                    fk_farmer=farmer,
                    fk_farmland=farm,
                    fk_crop_id=crop_id,
                    fk_croptype_id=filter_type,
                    is_completed=False
                ).order_by('preference_number').first()

                if not preference_completion:
                    return Response({'message': 'All preferences are completed or not found'}, status=status.HTTP_404_NOT_FOUND)

                preference_completion_serializer = SpicesPrefrencesSerializer(preference_completion)

                notification_message = WeatherPopNotification.objects.filter(
                    fk_weather_condition__condition__in=weather_condition,
                    preference_number=preference_completion.preference_number,
                    fk_language_id=user_language,
                    fk_crops_id=crop_id,
                    fk_croptype_id=filter_type
                ).first()

                if notification_message:
                    notification_serializer = WeatherNotificationSerializer(notification_message)
                    return Response({
                        'notification': notification_serializer.data,
                        'preference': preference_completion_serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'message': 'No notification found for the current weather condition and preference',
                        'preference': preference_completion_serializer.data
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({'message': 'User is not a farmer'}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 
#######################################--------------CEREALS POP---#########################################################
class CerealStagesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        user = request.user
        crop_id = request.data.get('crop_id')
        farm_id=request.data.get('land_id')
        filter_type = request.data.get('filter_type')
        user_language = request.data.get('user_language')

        required_fields = ['crop_id', 'filter_type', 'user_language']
        for field in required_fields:
            if not request.data.get(field):
                return Response({'message': f'Missing or empty field: {field}'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if user.user_type == "farmer":
                try:
                    farmer = FarmerProfile.objects.get(user=user)
                except FarmerProfile.DoesNotExist:
                    return Response({'message': 'Farmer Not Found'}, status=status.HTTP_404_NOT_FOUND)
                farm=None
                if farm_id:
                    try:
                        farm = FarmerLandAddress.objects.get(id=farm_id, fk_farmer=farmer, fk_crops__id=crop_id)
                    except FarmerLandAddress.DoesNotExist:
                        return Response({'error': 'Invalid farmer land ID'}, status=status.HTTP_404_NOT_FOUND)

                veges = CerealsPop.objects.filter(
                    fk_crop_id=crop_id,
                    fk_language_id=user_language,
                    fk_croptype_id=filter_type
                ).order_by("preference", "stage_number")

                today = timezone.now().date()
                stage_data = []
                preference_data = []

                preferences = CerealsPop.objects.filter(
                    fk_crop_id=crop_id,
                    fk_croptype_id=filter_type,
                    fk_language_id=user_language
                ).values('preference', 'stages').distinct().order_by('preference')

                preference_completion_map = {}
                for pref in preferences:
                    preference_completion, created = CerealPreferenceCompletion.objects.get_or_create(
                        fk_farmer=farmer,
                        fk_farmland=farm,
                        fk_crop_id=crop_id,
                        fk_language_id=user_language,
                        fk_croptype_id=filter_type,
                        preference_number=pref['preference'],
                        name=pref['stages'],
                        defaults={'start_date': None}
                    )
                    preference_completion_map[pref['preference']] = preference_completion

                for vege in veges:
                    stage_completions = CerealStageCompletion.objects.filter(
                        cereal_pop=vege,
                        fk_farmer=farmer,
                        fk_farmland=farm,
                        fk_language_id=user_language,
                        fk_croptype_id=filter_type,
                        fk_crop_id=crop_id,
                        stage_number=vege.stage_number
                    )

                    if stage_completions.exists():
                        stage_completion = stage_completions.first()
                    else:
                        stage_completion, created = CerealStageCompletion.objects.get_or_create(
                            cereal_pop=vege,
                            fk_farmer=farmer,
                            fk_farmland=farm,
                            fk_language_id=user_language,
                            fk_croptype_id=filter_type,
                            fk_crop_id=crop_id,
                            stage_number=vege.stage_number,
                            defaults={'start_date': None}
                        )

                    preference_completion = preference_completion_map.get(vege.preference)

                    if preference_completion:
                        if vege.preference == 1:
                            if stage_completion.start_date is None:
                                stage_completion.start_date = today
                                stage_completion.save()
                        
                            if preference_completion.start_date is None:
                                preference_completion.start_date = today
                                preference_completion.save()
                        else:
                            previous_preferences = [p for p in preference_completion_map if p < vege.preference]
                            all_previous_completed = all(
                                preference_completion_map[p].is_completed
                                for p in previous_preferences
                                if preference_completion_map.get(p)
                            )

                            if all_previous_completed:
                                if stage_completion.start_date is None:
                                    if previous_preferences:
                                        previous_preference = max(previous_preferences)
                                        previous_preference_completion = preference_completion_map.get(previous_preference)
                                    if previous_preference_completion and previous_preference_completion.completion_date:
                                        stage_completion.start_date = previous_preference_completion.completion_date
                                    else:
                                        stage_completion.start_date = today
                            else:
                                stage_completion.start_date = today
                            stage_completion.save()
                         
                        if preference_completion.start_date is None:
                            preference_completion.start_date = stage_completion.start_date
                            preference_completion.save()

                    # Calculate progress for this preference
                    total_stages = CerealsPop.objects.filter(
                        fk_crop_id=crop_id,
                        preference=vege.preference,
                        fk_croptype_id=filter_type,
                        fk_language_id=user_language
                    ).count()

                    completed_stages = CerealStageCompletion.objects.filter(
                        fk_farmer=farmer,
                        fk_farmland=farm,
                        cereal_pop__fk_crop_id=crop_id,
                        fk_croptype_id=filter_type,
                        fk_language_id=user_language,
                        fk_crop_id=crop_id,
                        cereal_pop__preference=vege.preference,
                        is_completed=True
                    ).count()

                    progress = int((completed_stages / total_stages) * 100) if total_stages > 0 else 0
                    if preference_completion:
                        preference_completion.progress = progress
                        preference_completion.save()

                        if progress == 100 and not preference_completion.is_completed:
                            preference_completion.is_completed = True
                            preference_completion.completion_date = today
                            preference_completion.total_days = (today - preference_completion.start_date).days if preference_completion.start_date else 0
                            preference_completion.save()
                            
                            next_preference = vege.preference + 1
                            next_preference_stages = CerealsPop.objects.filter(
                                fk_crop_id=crop_id,
                                preference=next_preference,
                                fk_language_id=user_language,
                                fk_croptype_id=filter_type
                            ).order_by('stage_number')
                            
                            if next_preference_stages.exists():
                                next_preference_completion, _ = CerealPreferenceCompletion.objects.get_or_create(
                                    fk_farmer=farmer,
                                    fk_farmland=farm,
                                    fk_crop_id=crop_id,
                                    fk_language_id=user_language,
                                    fk_croptype_id=filter_type,
                                    preference_number=next_preference,
                                    defaults={'start_date': today, 'is_completed': False, 'progress': 0}
                                )
                                for next_stage in next_preference_stages:
                                    CerealStageCompletion.objects.get_or_create(
                                        cereal_pop=next_stage,
                                        fk_farmer=farmer,
                                        fk_farmland=farm,
                                        fk_croptype_id=filter_type,
                                        fk_crop_id=crop_id,
                                        fk_language_id=user_language,
                                        stage_number=next_stage.stage_number,
                                        defaults={'start_date': today, 'is_completed': False, 'total_days_spent': 0}
                                    )

                    products = []
                    for product in vege.fk_product.all():
                        suppliers = product.fk_supplier.all()
                        supplier_ids = [supplier.id for supplier in suppliers]
                        latest_price = ProductPrices.objects.filter(fk_product=product).order_by('-id').first()
                        product_data = {
                            'product_id': product.id,
                            'product_name': product.productName,
                            'product_image': product.product_image.url if product.product_image else None,
                            'product_description': product.productDescription,
                            'Category': product.Category,
                            'supplier_ids': supplier_ids,
                            'price': latest_price.unit_price if latest_price else None
                                    }
                        products.append(product_data)

                    # Add stage data to stage_data list
                    stage_data.append({
                        'stage_id': vege.id,
                        'stages': vege.stages,
                        'stage_name': vege.stage_name,
                        "stage_audio": vege.audio.url if vege.audio else None, 
                        'sow_period': vege.sow_period,
                        'description': vege.description,
                        'stage_number': vege.stage_number,
                        'preference': vege.preference,
                        'is_completed': stage_completion.is_completed,
                        'days_spent': stage_completion.total_days_spent,
                        'start_date': stage_completion.start_date,
                        'products': products
                    })

                for preference_number, preference_completion in preference_completion_map.items():
                    preference_data.append({
                        'preference_id': preference_completion.id,
                        'stages': preference_completion.name,
                        'is_completed': preference_completion.is_completed,
                        'preference_number': preference_completion.preference_number
                    })

                return Response({'stages': stage_data, 'preferences': preference_data})
    
        except Exception as e:
            return Response({
                'error': 'An error occurred.',
                'details': str(e),
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

###-------Mark Stage Complete
class MarkCerealStageCompleteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        user = request.user
        crop_id = request.data.get('crop_id')
        farm_id=request.data.get('land_id')
        filter_type = request.data.get('filter_type')
        preference_number = request.data.get('preference_number')
        submit_task = request.FILES.get('submit_task')
        user_language = request.data.get('user_language')

        required_fields = ['crop_id', 'filter_type', 'preference_number', 'user_language']
        for field in required_fields:
            if not request.data.get(field):
                return Response({'message': f'Missing or empty field: {field}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if user.user_type == "farmer":
                try:
                    farmer = FarmerProfile.objects.get(user=user)
                except FarmerProfile.DoesNotExist:
                    return Response({'message': 'Farmer Not Found'}, status=status.HTTP_404_NOT_FOUND)
                farm=None
                if farm_id:
                    try:
                        farm = FarmerLandAddress.objects.get(id=farm_id, fk_farmer=farmer, fk_crops__id=crop_id)
                    except FarmerLandAddress.DoesNotExist:
                        return Response({'error': 'Invalid farmer land ID'}, status=status.HTTP_404_NOT_FOUND)

                with transaction.atomic():
                    stages = CerealsPop.objects.filter(
                        fk_crop_id=crop_id,
                        preference=preference_number,
                        fk_croptype_id=filter_type,
                        fk_language_id=user_language
                    )

                    if not stages.exists():
                        return Response({'message': 'No stages found for this preference'}, status=status.HTTP_404_NOT_FOUND)

                    today = timezone.now().date()
                    completed_stages_data = []

                    for stage in stages:
                        stage_completions = CerealStageCompletion.objects.filter(
                            cereal_pop=stage,
                            fk_farmer=farmer,
                            fk_farmland=farm,
                            fk_croptype_id=filter_type,
                            fk_crop_id=crop_id,
                            fk_language_id=user_language,
                            stage_number=stage.stage_number
                        )

                        if stage_completions.exists():
                            stage_completion = stage_completions.first()
                            stage_completion.completion_date = today
                            stage_completion.is_completed = True
                            if stage_completion.start_date:
                                stage_completion.total_days_spent = (today - stage_completion.start_date).days
                            else:
                                stage_completion.start_date = today
                                stage_completion.total_days_spent = 0
                            stage_completion.save()
                        else:
                            stage_completion, created = CerealStageCompletion.objects.get_or_create(
                                cereal_pop=stage,
                                fk_farmer=farmer,
                                fk_farmland=farm,
                                fk_croptype_id=filter_type,
                                fk_crop_id=crop_id,
                                fk_language_id=user_language,
                                stage_number=stage.stage_number,
                                defaults={'start_date': today, 'completion_date': today, 'is_completed': True, 'total_days_spent': 0}
                            )

                        completed_stages_data.append({
                            'stage_id': stage_completion.cereal_pop.id,
                            'stage_number': stage_completion.stage_number,
                            'days_to_complete': stage_completion.total_days_spent,
                            'preference_number': stage.preference
                        })

                    # Handle preference completion
                    preference_completion, created = CerealPreferenceCompletion.objects.get_or_create(
                        fk_farmer=farmer,
                        fk_farmland=farm,
                        fk_crop_id=crop_id,
                        fk_croptype_id=filter_type,
                        fk_language_id=user_language,
                        preference_number=preference_number,
                        defaults={'start_date': today, 'completion_date': today, 'is_completed': True, 'total_days': 0, 'progress': 100}
                    )

                    if not created:
                        preference_completion.completion_date = today
                        preference_completion.is_completed = True
                        if preference_completion.start_date:
                            preference_completion.total_days = (today - preference_completion.start_date).days
                        else:
                            preference_completion.start_date = today
                            preference_completion.total_days = 0
                        preference_completion.progress = 100
                        preference_completion.save()

                    # Initialize the next preference
                    next_preference_number = int(preference_number) + 1
                    next_preference_stages = CerealsPop.objects.filter(
                        fk_crop_id=crop_id,
                        preference=next_preference_number,
                        fk_language_id=user_language,
                        fk_croptype_id=filter_type
                    ).order_by('stage_number')

                    if next_preference_stages.exists():
                        next_preference_completion, _ = CerealPreferenceCompletion.objects.get_or_create(
                            fk_farmer=farmer,
                            fk_farmland=farm,
                            fk_crop_id=crop_id,
                            fk_language_id=user_language,
                            fk_croptype_id=filter_type,
                            preference_number=next_preference_number,
                            defaults={'start_date': today, 'is_completed': False, 'progress': 0}
                        )

                        for next_stage in next_preference_stages:
                            CerealStageCompletion.objects.get_or_create(
                                cereal_pop=next_stage,
                                fk_farmer=farmer,
                                fk_farmland=farm,
                                fk_croptype_id=filter_type,
                                fk_crop_id=crop_id,
                                fk_language_id=user_language,
                                stage_number=next_stage.stage_number,
                                defaults={'start_date': today, 'is_completed': False, 'total_days_spent': 0}
                            )

                    coins_added = 20 if submit_task else 10
                    farmer.coins += coins_added
                    farmer.save()

                    return Response({
                        'completed_stages': completed_stages_data,
                        'coins_added': coins_added,
                        'total_coins': farmer.coins
                    })
            else:
                return Response({'message': 'User is not a farmer'}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            return Response({
                'message': 'An error occurred',
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#######------------Spices Progress
class CerealProgressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        crop_id = request.query_params.get('crop_id')
        farm_id=request.query_params.get('land_id')
        filter_type = request.query_params.get('filter_type')

        if not crop_id or not filter_type:
            return Response({'message': 'Missing crop_id or filter_type'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if user.user_type == "farmer":
                try:
                    farmer = FarmerProfile.objects.get(user=user)
                except FarmerProfile.DoesNotExist:
                    return Response({'message': 'Farmer Not Found'}, status=status.HTTP_404_NOT_FOUND)
                farm=None
                if farm_id:
                    try:
                        farm = FarmerLandAddress.objects.get(id=farm_id, fk_farmer=farmer, fk_crops__id=crop_id)
                    except FarmerLandAddress.DoesNotExist:
                        return Response({'error': 'Invalid farmer land ID'}, status=status.HTTP_404_NOT_FOUND)

                total_preferences = CerealsPop.objects.filter(
                    fk_crop_id=crop_id,
                    fk_croptype_id=filter_type
                ).values('preference').distinct().count()

                if total_preferences == 0:
                    return Response({'message': 'No preferences found for this crop'}, status=status.HTTP_404_NOT_FOUND)

                completed_preferences = CerealPreferenceCompletion.objects.filter(
                    fk_farmer=farmer,
                    fk_farmland=farm,
                    fk_crop_id=crop_id,
                    fk_croptype_id=filter_type,
                    is_completed=True
                ).count()

                overall_progress = (completed_preferences / total_preferences) * 100

                preference_progress = CerealPreferenceCompletion.objects.filter(
                    fk_farmer=farmer,
                    fk_farmland=farm,
                    fk_croptype_id=filter_type,
                    fk_crop_id=crop_id
                ).values('preference_number', 'progress', 'is_completed', 'name')

                response_data = {
                    'overall_progress': round(overall_progress, 2),
                    'total_preferences': total_preferences,
                    'completed_preferences': completed_preferences,
                    'preference_details': list(preference_progress)
                }

                return Response(response_data)
            else:
                return Response({'message': 'User is not a farmer'}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )   
##--------Cereals WQeather Notifications
class GetCerealsPopNotification(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        data = request.query_params  
        user_language = data.get('user_language')
        crop_id = data.get('crop_id')
        farm_id = data.get('land_id')
        filter_type = data.get('filter_type')
        weather_condition = data.get('weather_condition', [])

        required_fields = ['crop_id', 'filter_type', 'user_language']
        for field in required_fields:
            if not data.get(field):
                return Response({'message': f'Missing or empty field: {field}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if user.user_type == "farmer":
                try:
                    farmer = FarmerProfile.objects.get(user=user)
                except FarmerProfile.DoesNotExist:
                    return Response({'message': 'Farmer Not Found'}, status=status.HTTP_404_NOT_FOUND)

                farm = None
                if farm_id:
                    try:
                        farm = FarmerLandAddress.objects.get(id=farm_id, fk_farmer=farmer, fk_crops__id=crop_id)
                    except FarmerLandAddress.DoesNotExist:
                        return Response({'message': 'Land not Found'}, status=status.HTTP_404_NOT_FOUND)
                
                preference_completion = CerealPreferenceCompletion.objects.filter(
                    fk_farmer=farmer,
                    fk_farmland=farm,
                    fk_crop_id=crop_id,
                    fk_croptype_id=filter_type,
                    is_completed=False
                ).order_by('preference_number').first()

                if not preference_completion:
                    return Response({'message': 'All preferences are completed or not found'}, status=status.HTTP_404_NOT_FOUND)

                preference_completion_serializer = CerealsPrefrencesSerializer(preference_completion)

                notification_message = WeatherPopNotification.objects.filter(
                    fk_weather_condition__condition__in=weather_condition,
                    preference_number=preference_completion.preference_number,
                    fk_language_id=user_language,
                    fk_crops_id=crop_id,
                    fk_croptype_id=filter_type
                ).first()

                if notification_message:
                    notification_serializer = WeatherNotificationSerializer(notification_message)
                    return Response({
                        'notification': notification_serializer.data,
                        'preference': preference_completion_serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'message': 'No notification found for the current weather condition and preference',
                        'preference': preference_completion_serializer.data
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({'message': 'User is not a farmer'}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )     
########################################--------------FRUITS POP---------------######################################################
import calendar
def month_to_number(month_name):
    return list(calendar.month_name).index(month_name)
class GetFruitsPopAPIView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request,format=None):
        user=request.user
        try:
            data = request.data
            farm_id = data.get('land_id')
            user_language = data.get('user_language')
            crop_id = data.get('crop_id')
            orchidtype = data.get('orchidtype')
            filter_type = data.get('filter_type')
            current_date = timezone.now().date()
            current_month = current_date.month
            if user.user_type == "farmer":
                try:
                    farmer = FarmerProfile.objects.get(user=user)
                except FarmerProfile.DoesNotExist:
                    return Response({'message': 'Farmer Not Found'}, status=status.HTTP_404_NOT_FOUND)
                farm=None
                if farm_id:
                    try:
                        farm = FarmerLandAddress.objects.get(id=farm_id, fk_farmer=farmer, fk_crops__id=crop_id)
                    except FarmerLandAddress.DoesNotExist:
                        return Response({'error': 'Invalid farmer land ID'}, status=status.HTTP_404_NOT_FOUND)

                fruits_pop_data = FruitsPop.objects.filter(
                fk_crops_id=crop_id,
                fk_language_id=user_language,
                fk_croptype_id=filter_type,
                orchidtype=orchidtype,
                start_month__lte=current_month,
                end_month__gte=current_month,
                start_month__isnull=False,
                end_month__isnull=False
                        )

                if fruits_pop_data.exists():
                    response_data = {
                    'land_id': farm_id,
                    'user_id': farmer.id,
                    'crops': []
                    }

                    for fruit_pop in fruits_pop_data:
                        completion, _ = FruitsStageCompletion.objects.get_or_create(
                        fk_fruits=fruit_pop,
                        fk_farmer=farmer,
                        fk_farmland_id=farm_id if farm_id else None,
                        fk_croptype_id=filter_type,
                        fk_crops_id=crop_id,
                        defaults={
                            'is_complete': False,
                            'completion_date': None,
                            'days_completed': 0,
                            'delay_count': 0
                                    }
                                )
                        is_completed = completion.is_complete
                        completion_date = completion.completion_date
                        days_completed = completion.days_completed
                        delay_count = completion.delay_count

                        start_month = month_to_number(fruit_pop.start_period)
                        end_month = month_to_number(fruit_pop.end_period)

                        current_year = current_date.year
                        start_date = date(current_year, start_month, 1)
                        end_date = date(current_year, end_month, calendar.monthrange(current_year, end_month)[1])

                        if end_month < start_month:
                            end_date = date(current_year + 1, end_month, calendar.monthrange(current_year + 1, end_month)[1])

                        total_days = (end_date - start_date).days

                        if is_completed:
                            days_left = 0
                            progress = 100
                        else:
                            days_left = max(0, (end_date - current_date).days)
                            progress = min(100, max(0, int((days_completed / total_days) * 100)))

                        products = [
                        {
                            'product_id': product.id,
                            'product_name': product.productName if product else None,
                            'description': product.productDescription if product else None,
                            'product_image': product.product_image.url if product.product_image and product.product_image.name else None,
                        }
                        for product in fruit_pop.fk_product.all()
                        ]

                        crop_data = {
                        'crop_name': fruit_pop.fk_crops.crop_name,
                        'stages_id': fruit_pop.id,
                        'stages': fruit_pop.stages,
                        'stage_name': fruit_pop.stage_name,
                        'stage_number': fruit_pop.stage_number,
                        'start_month': fruit_pop.start_month,
                        'end_month': fruit_pop.end_month,
                        'orchidtype': fruit_pop.orchidtype,
                        'description': fruit_pop.description,
                        'start': fruit_pop.start_period,
                        'end': fruit_pop.end_period,
                        'days_completed': days_completed,
                        'days_left': days_left,
                        'total_days': total_days,
                        'progress': progress,
                        'is_complete': is_completed,
                        'completion_date': completion_date.isoformat() if completion_date else None,
                        'delay_count': delay_count,
                        'products': products
                        }
                        response_data['crops'].append(crop_data)

                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'No fruits population data found for the given criteria.'}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({'message': 'User is not a farmer'}, status=status.HTTP_403_FORBIDDEN)

        except ValueError as ve:
            return Response({'error': 'Value error occurred', 'message': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )   
##--------Complete Fruits Stages 
class CompleteFruitsStagesAPIView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request,format=None):
        user=request.user
        try:
            data = request.data
            farm_id = data.get('land_id')
            crop_id = data.get('crop_id')
            filter_type = data.get('orchidtype')
            stage_ids = data.get('stage_ids')
            submit_image=data.get('submit_task')
            current_date = timezone.now().date()
            if not crop_id or not stage_ids:
                return Response({'error': 'Crop ID and Stage IDs are required'}, status=status.HTTP_400_BAD_REQUEST)
            if user.user_type == "farmer":
                try:
                    farmer = FarmerProfile.objects.get(user=user)
                except FarmerProfile.DoesNotExist:
                    return Response({'message': 'Farmer Not Found'}, status=status.HTTP_404_NOT_FOUND)
                farm=None
                if farm_id:
                    try:
                        farm = FarmerLandAddress.objects.get(id=farm_id, fk_farmer=farmer, fk_crops__id=crop_id)
                    except FarmerLandAddress.DoesNotExist:
                        return Response({'error': 'Invalid farmer land ID'}, status=status.HTTP_404_NOT_FOUND)
                completed_stages = []

                for stage_id in stage_ids:
                    try:
                        stage = FruitsPop.objects.get(id=stage_id)
                        start_month = month_to_number(stage.start_period)
                        current_year = current_date.year
                        start_date = date(current_year, start_month, 1)
                        days_completed = (current_date - start_date).days
                        completion, created = FruitsStageCompletion.objects.update_or_create(
                            fk_fruits=stage,
                            fk_farmer=farmer,
                            submit_image=submit_image,
                            fk_croptype_id=filter_type,
                            fk_crops_id=crop_id,
                            defaults={
                            'is_complete': True,
                            'completion_date': current_date,
                            'days_completed': days_completed,
                            'delay_count': 0  
                                }
                                )
                        coins_added = 20 if submit_image else 10
                        farmer.coins += coins_added
                        farmer.save()
                        completed_stages.append({
                            'stage_id': stage_id,
                            'stage_name': stage.stage_name,
                            'completion_date': completion.completion_date,
                            'delay': completion.delay_count,
                            'days_completed': completion.days_completed,
                            'coins_received': coins_added
                            })
                    except FruitsPop.DoesNotExist:
                        return Response({'error': f'Stage with ID {stage_id} does not exist.'}, status=404)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )   

class GetFruitsWeatherNotifications(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        user=request.user
        print(f"User is :{user.user_type}")
        try:
            user_language = request.query_params.get('user_language')
            crop_id = request.query_params.get('crop_id')
            farm_id = request.query_params.get('farm_id')
            filter_type = request.query_params.get('filter_type')
            weather_condition = request.query_params.get('weather_condition',[])
            
            required_fields = ['user_id', 'crop_id', 'filter_type', 'user_language']
            for field in required_fields:
                if not locals().get(field):
                    return Response({'message': f'Missing or empty field: {field}'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                farmer = FarmerProfile.objects.get(user=user)
            except FarmerProfile.DoesNotExist:
                return Response({'message': 'Farmer Not Found'}, status=status.HTTP_404_NOT_FOUND)
            farm=None
            if farm_id:
                try:
                    farm = FarmerLandAddress.objects.get(id=farm_id, fk_farmer=farmer, fk_crops__id=crop_id)
                except FarmerLandAddress.DoesNotExist:
                    return Response({'error': 'Invalid farmer land ID'}, status=status.HTTP_404_NOT_FOUND)

            preference_completion = FruitsStageCompletion.objects.filter(
                fk_farmer=farmer,
                fk_farmland=farm,
                fk_crops_id=crop_id,
                fk_croptype_id=filter_type,
                is_complete=False
            ).first()

            if not preference_completion:
                return Response({'message': 'All preferences are completed or not found'}, status=status.HTTP_404_NOT_FOUND)

            notification_message = WeatherPopNotification.objects.filter(
                fk_weather_condition__condition__in=weather_condition,
                fk_language_id=user_language,
                fk_crops_id=crop_id,
                fk_croptype_id=filter_type
            ).first()

            if notification_message:
                return Response({'message': 'success', 'notification': notification_message.notification_text}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'No notification found for the current weather condition and preference'}, status=status.HTTP_404_NOT_FOUND)
                                                                       
        except Exception as e:
            return Response({'message': 'An error occurred', 'error': traceback.format_exc()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#############---------------------------------------DUKAAN---------------######################################
#############---------------------------------------DUKAAN---------------######################################

#################----------------------------SHOP Rating by Farmer-----------------##############
class FarmerCommentonShop(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        user=request.user
        print(f"User is {user.user_type}")
        try:
            if user.user_type == 'farmer':
                try:
                    farmer_profile=FarmerProfile.objects.get(user=user)
                except FarmerProfile.DoesNotExist:
                    return Response({'status':'error','message':'Farmer not Found'})
                shop_id = request.data.get('shop_id', None)
                rating=request.data.get('rating', None)
                if not shop_id or not rating:
                    return Response({'status':'error','message':'Shop ID and Rating are required'})
                if rating < 0 or rating > 5:
                    return Response({'status':'error','message':'Rating should be between 0 and 5'})
                print(f"Shop ID IS :{shop_id} Rating by User is :{rating}")
                data=UserCommentOnShop.objects.create(fk_shop_id=shop_id,fk_user=farmer_profile,
                                                      rating=rating)
                print(f"Shop Ratimg Data Object is :{data}")
                data.save()
                return Response({'status':'success','message':'Rating added successfully'},status=status.HTTP_200_OK)
            else:
                return Response({'status':'error','message':'Invalid User'})
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
#################-------------------------------------------Agricultural Shops--------------------###########
class GetallShops(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user=request.user
        print(f"User is :{user.user_type}")
        filter_type=request.query_params.get("filter_type")
        try:
            if user.user_type=="farmer":
                if filter_type == 'fpo':
                    shops = ShopDetails.objects.filter(fk_fpo__isnull=False, is_deleted=False)
                    print(f"Shops Data:{shops}")
                    if not shops.exists():
                        return Response({"error": "No FPO shops found"}, status=status.HTTP_404_NOT_FOUND)
                elif filter_type == 'supplier':
                    shops = ShopDetails.objects.filter(fk_supplier__isnull=False, is_deleted=False)
                    if not shops.exists():
                        return Response({"error": "No Supplier shops found"}, status=status.HTTP_404_NOT_FOUND)
                else:
                    shops = ShopDetails.objects.filter(is_deleted=False)
                    if not shops.exists():
                        return Response({"error": "No shops found"}, status=status.HTTP_404_NOT_FOUND)
                serializer = ShopDetailSerializer(shops, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK) 
            else:
                return Response({"error": "Only farmers can access this endpoint"}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
##############################----- Get Single Shop Info(with Shop+Product+Shop Ratings)----------------------###############
class GetShopDetails(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        user = request.user
        print(f"User is :{user.user_type}")
        shop_id = request.query_params.get('shop_id')
        filter_type = request.query_params.get('filter_type')
        
        if not shop_id:
            return Response({"error": "shop_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not filter_type:
            return Response({"error": "filter_type is required"}, status=status.HTTP_400_BAD_REQUEST) 
        
        try:
            if user.user_type == "farmer":
                try:
                    farmer_profile=FarmerProfile.objects.get(user=user)
                    print(f"Farmer Record is :{farmer_profile}")
                except FarmerProfile.DoesNotExist:
                    return Response({"error": "Farmer not found"}, status=status.HTTP_404_NOT_FOUND)
                
                shop = ShopDetails.objects.filter(id=shop_id, is_deleted=False)
                if not shop.exists():
                    return Response({"error": "No shop found with this id"}, status=status.HTTP_404_NOT_FOUND)

                shop_instance = shop.first()  
                if filter_type == "fpo":
                    fpo_id = shop_instance.fk_fpo.id
                    print(f"FPO is :{fpo_id}")
                    products = ProductDetails.objects.filter(fk_fpo_id=fpo_id, is_deleted=False)
                    print(f"Products are :{products}")
                    serializer = FPOShopDetailSerializer(shop, many=True,context={'farmer_id':farmer_profile.id})
                    products_data=FPOProductDetailsSerializer(products,many=True,context={'fpo_id': fpo_id})
                    print(f"Product Data are :{products_data.data}")
                    
                elif filter_type == "supplier":
                    print(f"Shop is :{shop}")
                    supplier = shop_instance.fk_supplier.id  
                    print(f"Supplier is :{supplier}")
                    products = ProductDetails.objects.filter(fk_supplier__id=supplier, is_deleted=False)
                    print(f"Products are :{products}")
                    serializer = SupplierShopDetailSerializer(shop, many=True,context={'farmer_id':farmer_profile.id})
                    products_data=SupplierProductFilterDetailsSerializer(products, many=True,context={'supplier_id': supplier})
                
                return Response({'shops_data': serializer.data,'products_data':products_data.data,
                                 }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Only farmers can access this endpoint"}, status=status.HTTP_403_FORBIDDEN)
        
        except ShopDetails.DoesNotExist:
            return Response({"error": "No shop found with this id"}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
#########################-----------------------Get All Products--------------------------################
class GetallProducts(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,format=None):
        user=request.user
        print(f"User is :{user}")
        filter_type=request.query_params.get('filter_type')
        category=request.query_params.get('category')
        if not filter_type and not category:
            return Response({"error": "filter_type or category is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if user.user_type=="farmer":
                if filter_type == 'fpo':
                    products = ProductDetails.objects.filter(fk_fpo__isnull=False, is_deleted=False,Category=category)
                    if not products.exists():
                        return Response({"error": "No FPO products found"}, status=status.HTTP_404_NOT_FOUND)
                    product_instance=products.first()
                    fpo_id=product_instance.fk_fpo.id
                    print(f"FPO Id is :{fpo_id}")
                    print(f"Products are :{products}")
                    products_data=FPOProductDetailsSerializer(products,many=True,context={'fpo_id': fpo_id})
                    print(f"Product Data are :{products_data.data}")
                    
                    
                elif filter_type =='supplier':
                    products = ProductDetails.objects.filter(fk_supplier__isnull=False, is_deleted=False,Category=category)
                    if not products.exists():
                        return Response({"error": "No Supplier products found"}, status=status.HTTP_404_NOT_FOUND)
                    product_instance=products.first()
                    supplier_ids = []
                    for product in products:
                        supplier_ids.extend([supplier.id for supplier in product.fk_supplier.all()])
                    print(f"Supplier Ids are :{supplier_ids}")
                    products_data = SupplierProductFilterDetailsSerializer(products, many=True)
                    print(f"Product Data are :{products_data.data}")
                    
                return Response({'products_data':products_data.data
                                 }, status=status.HTTP_200_OK)
                
            else:
                return Response({"error": "Only farmers can access this endpoint"}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
##############################--------------------GET SINGLE Product Details-----------------------#######################
class GetSingleProductDetails(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        user = request.user
        print(f"User is :{user.user_type}")
        product_id = request.query_params.get('product_id')
        filter_type=request.query_params.get('filter_type')
        
        if not product_id :
            return Response({"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST) 
        if not filter_type:
            return Response({"error": "filter_type is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if user.user_type == "farmer":
                try:
                    farmer_profile=FarmerProfile.objects.get(user=user)
                    print(f"Farmer Record is :{farmer_profile}")
                except FarmerProfile.DoesNotExist:
                    return Response({"error": "Farmer not found"}, status=status.HTTP_404_NOT_FOUND)
                if filter_type=="fpo":
                    products = ProductDetails.objects.filter(id=product_id,fk_fpo__isnull=False, is_deleted=False)
                    if not products.exists():
                        return Response({"error": "No FPO products found"}, status=status.HTTP_404_NOT_FOUND)
                    product_instance=products.first()
                    fpo_id=product_instance.fk_fpo.id
                    print(f"FPO Id is :{fpo_id}")
                    print(f"Products are :{products}")
                    products_data=FPOProductDetailsSerializer(products,many=True,context={'fpo_id': fpo_id})
                    print(f"Product Data are :{products_data.data}")
                   
                elif filter_type=="supplier":
                    products = ProductDetails.objects.filter(id=product_id,fk_supplier__isnull=False, is_deleted=False)
                    if not products.exists():
                        return Response({"error": "No Supplier products found"}, status=status.HTTP_404_NOT_FOUND)
                    product_instance=products.first()
                    supplier_id=product_instance.fk_supplier.id
                    print(f"Supplier Id is :{supplier_id}")
                    print(f"Products are :{products}")
                    products_data= SupplierProductFilterDetailsSerializer(products, many=True, context={'supplier_id': supplier_id})
                    print(f"Product Data are :{products_data.data}")
                return Response({'products_data':products_data.data
                                 }, status=status.HTTP_200_OK)
                    
            else:
                return Response({"error": "Only farmers can access this endpoint"}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
                
#################################################----------------------SOIL TESTING BOOKINGS------------#########################

#####-------SOIL Testing Shops In Branch/Collection----
class SoilTestingShops(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        provider_id = request.query_params.get("provider_id")
        filter_type = request.query_params.get("filter_type")
        if not provider_id or not filter_type:
            return Response({"error": "provider_id and filter_type are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            shops=ShopDetails.objects.filter(have_soil=True,partnerservice__id=provider_id)
        except ShopDetails.DoesNotExist:
            return Response({"error": "No shop found with this provider_id and filter_type"}, status=status.HTTP_404_NOT_FOUND)
        try:
            soil_charges=SoilCharges.objects.filter(plans__iexact=filter_type,fk_providername__id=provider_id)
            print(f"Soil Charges Data:{soil_charges}")
        except SoilCharges.DoesNotExist:
            return Response({"error": "No Soil Charges found for this provider_id and filter_type"}, status=status.HTTP_404_NOT_FOUND)

        shop_ids=soil_charges.values_list("fk_shop_id",flat=True)
        print(f"Shop IDs for Soil Charges:{shop_ids}")

        results=shops.filter(id__in=shop_ids)
        print(f"Filtered Shop Data:{results}")
        serializer=ShopDetailSerializer(results,many=True)
        print(f"Serializer Data:{serializer.data}")
        response_data = []
        for shop in serializer.data:
            response_data.append({
                'shopid':shop['id'],
                'shopName': shop['shopName'],
                'shopContactNo': shop['shopContactNo'],
                'shopLatitude': shop['shopLatitude'],
                'shopLongitude': shop['shopLongitude'],
                'shopaddress': shop['shopaddress']
            })
        return Response({'status':'success','message':'Shop Displayed Successfully','data':response_data
                         })
    
##################-----------------------------Soil Testing Plans Information based on Shop--------------##################
class SoilTestingShopPlans(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            provider_id=request.query_params.get('provider_id')
            shop_id=request.query_params.get('shop_id')
            filter_type=request.query_params.get('filter_type')
            if not provider_id or not shop_id or not filter_type:
                return Response({"error": "provider_id, shop_id and filter_type are required"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                shop_details=ShopDetails.objects.filter(id=shop_id,partnerservice__id=provider_id)
            except ShopDetails.DoesNotExist:
                return Response({"error": "No shop Data found "}, status=status.HTTP_404_NOT_FOUND)
            shops_serializer=ShopDetailSerializer(shop_details,many=True)
            print(f"Shop Details Data :{shops_serializer.data}")
            shop_data = []
            for shop in shops_serializer.data:
                shop_data.append({
                'shopid':shop['id'],
                'shopName': shop['shopName'],
                'shopContactNo': shop['shopContactNo'],
                'shopLatitude': shop['shopLatitude'],
                'shopLongitude': shop['shopLongitude'],
                'shopaddress': shop['shopaddress']
            })

            try:
                soil_charges=SoilCharges.objects.filter(fk_providername__id=provider_id, fk_shop__id=shop_id,plans__iexact=filter_type)
            except SoilCharges.DoesNotExist:
                return Response({"error": "No Soil Charges Data found "}, status=status.HTTP_404_NOT_FOUND)
            soil_charges_serializer=SoilChargesSerializer(soil_charges,many=True)
            print(f"Soil Charges Data :{soil_charges_serializer.data}")
            soilcharges_data = []
            for shop in soil_charges_serializer.data:
                soilcharges_data.append({
                'chargesid':shop['id'],
                'finalprice': shop['price'],
                'pricebefore': shop['price_before'],
                'shop_id': shop['fk_shop'],
                'provider_ids': shop['fk_providername'],
            })

            return Response({'status':'success','shop_data':shop_data,'soil_charges':soilcharges_data})
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
##############-------------------------------POP Based Stage Completion Notfication-----------------############
class PopNotifications(APIView):
    def get(self, request,format=None):
        user=request.user
        print(f"User is :{user.user_type}")
        try:
            if user.user_type=='farmer':
                try:
                    farmer_profile=FarmerProfile.objects.get(user=user)
                    print(f"Farmer is :{farmer_profile}")
                except FarmerProfile.DoesNotExist:
                    return Response({"error": "No Farmer Profile found"}, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )