import  json
import traceback
from django.http import JsonResponse
from .models import *
from .scraper import *
from django.shortcuts import get_object_or_404
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
import random
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.sessions.models import Session
from django.http import HttpResponse
from django.db.models import Q
import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
import xlrd
import requests
import string
import os
from urllib.parse import urlparse
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from transformers import pipeline
from PIL import Image
# from newsapi import NewsApiClient
from django.core.exceptions import ValidationError
from .serializers import *
from rest_framework import status
from datetime import timedelta
# from serpapi import BingSearch
base_url = "64.227.136.113:8090"
import ast
from django.core.mail import send_mail
import logging
logger = logging.getLogger('Agreeculture_App')

#############################----------------------------Farmer Functionbs------------------------##################

#####-------------------------For Creating Refresh and Acces Token
def create_farmer_token(user, user_type):
    refresh = RefreshToken.for_user(user)
    refresh['user_type'] = user_type
    print(f"Created token for user type: {user_type}")
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

##############----------------------For Sending email
def send_otp_via_email(email, otp):
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}. It is valid for 10 minutes.'
    from_email = 'your-email@gmail.com'
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)

#################---------------------For Sending Otps
#################---------------------For Sending Otps
def send_otpmobile(request,mobile):
    try:
        url = "https://control.msg91.com/api/v5/otp"
        otp = random.randint(0,9999)
        params = {
        "template_id": "66b0844cd6fc0578d732ba62",  
        "mobile": mobile,                  
        "authkey": "427492AbnBhrYUWsn66b0810eP1",
        "realTimeResponse": "1"
        }
        payload = {
        "OTP": otp  
        }
        headers = {
        'Content-Type': "application/json"
        }
        response = requests.post(url, params=params, headers=headers, data=json.dumps(payload))
        print(otp)
        return Response(response.json())
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

###############--------------------------Update user infro with mobile and email---------------#############
def update_farmer_info(user, user_type, ip_address, mobile=None, is_new=False):
    if user_type == 'farmer':
        farmer, created = FarmerProfile.objects.get_or_create(user=user)
        farmer.ip_address = ip_address
        if mobile:
            farmer.mobile = mobile  
        if is_new or created:
            farmer.created_by = user
            farmer.created_at = timezone.now()
            farmer.is_new_user = True
        else:
            farmer.is_new_user = False
        farmer.last_updated_by = user
        farmer.last_updated_at = timezone.now()
        farmer.save()
#############-----------------For Creating & Reigstering new users--------------############
def register_new_user(request, **kwargs):
    mobile = kwargs.get('mobile')
    user_type = kwargs.get('user_type')
    otp = kwargs.get('otp')
    try:
        serializer = FarmerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            related_user = serializer.create(serializer.validated_data, user_type)
            store_otp(related_user, otp)
            update_farmer_info(related_user, user_type, kwargs['ip_address'], is_new=True, mobile=mobile)
            return Response({
                'message': f'User created and OTP sent successfully to {related_user.mobile}',
                'is_existing_user': False,
                'otp':otp
            }, status=status.HTTP_201_CREATED)
        print(f"Registration failed with errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
###########--------------------To store sende otp in backend
def store_otp(identifier, otp):
    expires_at = timezone.now() + timedelta(minutes=5)
    otp_record, created = OTPVerification.objects.update_or_create(
        mobile=identifier,
        defaults={
            'otp': otp,
            'expires_at': expires_at
        }
    )
    return otp_record


######################----------------------Addd State------------------------------------########################
@csrf_exempt
def AddState(request):
    try:
        if request.method=="POST":
            user_language=request.POST.get('user_language')
            excel_file = r'/home/AgreecultureUpdate/static/All States.xlsx'
            data_xl = pd.read_excel(excel_file)
            for index, row in data_xl.iterrows():
                StateMaster.objects.create(
                    state=row['State'],
                    fk_language_id=user_language
                )
            return JsonResponse({'success':'Data Uploaded Successfully'})
        else:
           return JsonResponse({'message': 'Method not allowed'}, status=405)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred.', 'details': str(e), 'traceback': traceback.format_exc()}, status=500)
#################################################---------------Add District---------------------###############
@csrf_exempt
def AddDistrict(request):
    try:
        if request.method=="POST":
            user_language=request.POST.get('user_language')
            state_id=request.POST.get('state_id')
            excel_file = r'/home/Agrisarathi/agrisarthi/staticfiles/updistrict.xlsx'
            data_xl = pd.read_excel(excel_file,sheet_name='hi')
            for index, row in data_xl.iterrows():
                DistrictMaster.objects.create(
                    fk_state_id=state_id,
                    fk_language_id=user_language,
                    district=row['District Name']
                )
            return JsonResponse({'success':'Data Uploaded Successfully'})
        else:
           return JsonResponse({'message': 'Method not allowed'}, status=405)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred.', 'details': str(e), 'traceback': traceback.format_exc()}, status=500)
    
#################################################---------------Add Crop Variety---------------------###############
@csrf_exempt
def AddCropVariety(request):
    try:
        if request.method=="POST":
            data = json.loads(request.body.decode('utf-8'))
            crop_id=data.get('crop_id')
            user_language=data.get('user_language')
            excel_file = r'/home/aman/backend/AgrisarthiProject/agrisarthi/PotaoVariety.xlsx'
            data_xl = pd.read_excel(excel_file,sheet_name='eng')
            for index, row in data_xl.iterrows():
                CropVariety.objects.create(
                    fk_crops_id=crop_id,
                    eng_name=row['eng_name'],
                    hin_name=row['hin_name']
                )
            return JsonResponse({'success':'Data Uploaded Successfully'})
        else:
           return JsonResponse({'message': 'Method not allowed'}, status=405)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred.', 'details': str(e), 'traceback': traceback.format_exc()}, status=500)
    

####################---------------------------------------Get All Crops-----------------------#############################
@csrf_exempt
def GetCrops(request):
    try:
        if request.method=="":
            data = json.loads(request.body.decode('utf-8'))
            user_language=data.get('user_language')
            crops=CropMaster.objects.filter(fk_language_id=user_language)
            return JsonResponse({"data":list(crops.values())})
        else:
            return JsonResponse({'message': 'Method not allowed'}, status=405)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred.', 'details': str(e), 'traceback': traceback.format_exc()}, status=500)



##############--------------------------------------------Crop Suggested-------------------------##############
@csrf_exempt
def AddSuggcropcsv(request):
    try:
        if request.method == "POST":
            excel_file = r'/home/aman/backend/AgrisarthiProject/Agrisarthi/Crop Suggestion (1).xlsx'
            data = json.loads(request.body.decode('utf-8'))
            user_language=data.get('user_language')
            data_xl = pd.read_excel(excel_file,sheet_name="hin")
            for index, row in data_xl.iterrows():
                # Assuming fk_crop is a ForeignKey field to CropMaster
                crop_name = row['Crop Name']
                try:
                    crop_master = CropMaster.objects.get(crop_name=crop_name)
                except CropMaster.DoesNotExist:
                    continue

                SuggestedCrop.objects.create(
                    fk_crop=crop_master,
                    fk_language_id=user_language,
                    season=row['When to be Suggested'],
                    description=row['Basic Description'],
                    weather_temperature=row['Weather Temperature'],
                    cost_of_cultivation=row['Cost of Cultivation (per acre)'],
                    market_price=row['Average Market Price (per quintal)'],
                    start_month=row['start_month'],
                    end_month=row['start_month'],
                    production=row['Average Production (per acre)']
                )
            return JsonResponse({'success': 'Data Uploaded Successfully'})
        else:
            return JsonResponse({'message': 'Method not allowed'}, status=405)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred.', 'details': str(e), 'traceback': traceback.format_exc()}, status=500)
    
####################-----------------------------ADD Spices POP-------------------------##################
@csrf_exempt
def AddPOP(request):
    try:
        if request.method=="POST":
            data = json.loads(request.body.decode('utf-8'))
            user_language=data.get('user_language')
            crop_id=data.get('crop_id')
            filter_id=data.get('filter_id')
            excel_file = r'/home/aman/backend/AgrisarthiProject/Agrisarthi/turmericpop.xlsx'
            data_xl = pd.read_excel(excel_file,sheet_name='hin')
            for index, row in data_xl.iterrows():
                SpicesPop.objects.create(
                    fk_language_id=user_language,
                    fk_crop_id=crop_id,
                    stages=row['stages'],
                    stage_name=row['stage_name'],
                    stage_number=row['stage_number'],
                    description=row['description'],
                    preference=row['preference'],
                    sow_period=row['sow_period'],
                    fk_croptype_id=filter_id
                )
            return JsonResponse({'success':'Data Uploaded Successfully'})
        else:
           return JsonResponse({'message': 'Method not allowed'}, status=405)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred.', 'details': str(e), 'traceback': traceback.format_exc()}, status=500)
    
