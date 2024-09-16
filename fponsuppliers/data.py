import  json
import traceback
from django.http import JsonResponse
from .models import *
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


@csrf_exempt
def AddMeasurements(request):
    try:
        if request.method=="POST":
            excel_file = r'/home/Agrisarathi/agrisarthi/staticfiles/measurement.xlsx'
            data_xl = pd.read_excel(excel_file)
            for index, row in data_xl.iterrows():
                ProductMeasurements.objects.create(
                    measurement_code=row['Measurement_Code'],
                    description=row['Measurement Description'],
                )
            return JsonResponse({'success':'Data Uploaded Successfully'})
        else:
           return JsonResponse({'message': 'Method not allowed'}, status=405)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred.', 'details': str(e), 'traceback': traceback.format_exc()}, status=500)
    
class GetMeasurements(APIView):
    def get(self,request,format=None):
        user=request.user
        print(f"User is :{user}")
        try:
            if user.user_type=='fpo':
                try:
                    fpo=FPO.objects.get(user=user)
                    print(f"Fpo Details :{fpo}")
                except FPO.DoesNotExist:
                    return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)
                measurements=ProductMeasurements.objects.filter(is_deleted=False)
                serializers=ProductMeasurementsSerializer(measurements,many=True)
                return Response(serializers.data)
            elif user.user_type=='supplier':
                try:
                    supplier=Supplier.objects.get(user=user)
                    print(f"Supplier Details :{supplier}")
                except Supplier.DoesNotExist:
                    return Response({'error': 'Supplier details not found'}, status=status.HTTP_404_NOT_FOUND)
                measurements=ProductMeasurements.objects.filter(is_deleted=False)
                serializers=ProductMeasurementsSerializer(measurements,many=True)
                return Response(serializers.data)
            else:
                return Response({'error': 'Only FPO and Supplier users can access this endpoint'}, status=status.HTTP_403_FORBIDDEN)
                
                
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
        