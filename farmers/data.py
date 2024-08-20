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
from django.core.mail import send_mail
# from newsapi import NewsApiClient
from django.core.exceptions import ValidationError
# from serpapi import BingSearch
base_url = "64.227.136.113:8090"
import ast
import logging
logger = logging.getLogger('Agreeculture_App')

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
            excel_file = r'/home/AgreecultureUpdate/staticfiles/files/Districtdata.xlsx'
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
            excel_file = r'/home/AgreecultureUpdate/static/potatovariety.xlsx'
            data_xl = pd.read_excel(excel_file,sheet_name='mango')
            for index, row in data_xl.iterrows():
                CropVariety.objects.create(
                    fk_crops_id=crop_id,
                    variety=row['Variety']
                )
            return JsonResponse({'success':'Data Uploaded Successfully'})
        else:
           return JsonResponse({'message': 'Method not allowed'}, status=405)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred.', 'details': str(e), 'traceback': traceback.format_exc()}, status=500)
    
#############################################---------------------------Get Crop Variety Details----------------########
@csrf_exempt
def GetCropVariety(request):
    try:
        if request.method=="POST":
            data = json.loads(request.body.decode('utf-8'))
            crop_id=data.get('crop_id')
            variety=CropVariety.objects.filter(fk_crops_id=crop_id)
            return JsonResponse({"data":list(variety.values())})
        else:
            return JsonResponse({'message': 'Method not allowed'}, status=405)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred.', 'details': str(e), 'traceback': traceback.format_exc()}, status=500)
    
####################---------------------------------------Get All Crops-----------------------###############
@csrf_exempt
def GetCrops(request):
    try:
        if request.method=="POST":
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
            excel_file = r'/home/AgreecultureUpdate/Crop Suggestion (1).xlsx'
            data_xl = pd.read_excel(excel_file)
            for index, row in data_xl.iterrows():
                # Assuming fk_crop is a ForeignKey field to CropMaster
                crop_name = row['Crop Name']
                crop_master = CropMaster.objects.get(crop_name=crop_name)  # Get the CropMaster instance

                SuggestedCrop.objects.create(
                    fk_crop=crop_master,
                    season=row['When to be Suggested'],
                    description=row['Basic Description'],
                    weather_temperature=row['Weather Temperature'],
                    cost_of_cultivation=row['Cost of Cultivation (per acre)'],
                    market_price=row['Average Market Price (per quintal)'],
                    production=row['Average Production (per acre)']
                )
            return JsonResponse({'success': 'Data Uploaded Successfully'})
        else:
            return JsonResponse({'message': 'Method not allowed'}, status=405)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred.', 'details': str(e), 'traceback': traceback.format_exc()}, status=500)
    
####################-----------------------------ADD Spices POP-------------------------##################
@csrf_exempt
def AddSpicesPOP(request):
    try:
        if request.method=="POST":
            user_language=request.POST.get('user_language')
            crop_id=request.POST.get('crop_id')
            filter_id=request.POST.get('filter_id')
            excel_file = r'/home/AgreecultureUpdate/Wheat Pop.xlsx'
            data_xl = pd.read_excel(excel_file,sheet_name='Wheat POP HI')
            for index, row in data_xl.iterrows():
                SpicesPop.objects.create(
                    fk_language_id=user_language,
                    fk_crop_id=crop_id,
                    stages=row['stages'],
                    stage_name=row['stage_name'],
                    stage_number=row['stage_number'],
                    sow_period=row['sow_period'],
                    description=row['description'],
                    preference=row['preference'],
                    fk_croptype_id=filter_id
                )
            return JsonResponse({'success':'Data Uploaded Successfully'})
        else:
           return JsonResponse({'message': 'Method not allowed'}, status=405)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred.', 'details': str(e), 'traceback': traceback.format_exc()}, status=500)
    
