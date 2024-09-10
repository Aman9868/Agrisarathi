from django.http import HttpResponse
from django.shortcuts import render,redirect
from .models import *
from farmers.models import *
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
from .backends import *
import traceback
import pandas as pd
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import *
from django.db import transaction
################################--------------------JWT Token Creation------------------#######################################
def create_user_token(user, user_type):
    refresh = RefreshToken.for_user(user)
    refresh['user_type'] = user_type
    print(f"Created token for user type: {user_type}")
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
####################-------------------------------------REST API's Login----------------###############
class UserLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        user_type = request.data.get('user_type')
        mobile = request.data.get('mobile')
        password = request.data.get('password')
        ip_address = request.META.get('REMOTE_ADDR')
        print(f"Login attempt with mobile: {mobile}, user_type: {user_type}, password: {password}, IP address: {ip_address}")

        try:
            user = CustomUser.objects.filter(mobile=mobile, user_type=user_type).first()
            if user:
                if check_password(password, user.password):
                    tokens = create_user_token(user, user_type)
                    self.update_user_info(user, user_type, ip_address)
                    return Response({
                        'message': "User logged in successfully",
                        'tokens': tokens
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                # New user registration and login
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

    def update_user_info(self, user, user_type, ip_address, is_new=False):
        if user_type == 'fpo':
            fpo = FPO.objects.get(user=user)
            print(f"FPO is :{fpo}")
            fpo.ip_address = ip_address
            if is_new:
                fpo.created_by = user
                fpo.created_at = timezone.now()
            fpo.last_updated_by = user
            fpo.last_updated_at = timezone.now()
            fpo.save()
        elif user_type == 'supplier':
            supplier =Supplier.objects.get(user=user)
            print(f"Supplier is :{supplier}")
            supplier.ip_address = ip_address
            if is_new:
                supplier.created_by = user
                supplier.created_at = timezone.now()
            supplier.last_updated_by = user
            supplier.last_updated_at = timezone.now()
            supplier.save()   
#############----------------------Logout---------------------##################
class UserLogout(APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            print(f"Logout attempt with refresh token: {refresh_token}")
            print(f"Token payload: {token.payload}")
            user_type = token.payload.get('user_type')

            if user_type not in ['fpo', 'supplier']:
                return Response({"error": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST)

            token.blacklist()
            return Response({"message": "Successfully logged out"}, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            print("Token error encountered during logout")
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
#############-----------------------------------------------Get Profilen FPO/Supplier----------------------------------##########    
class UserProfileView(APIView):
  permission_classes = [IsAuthenticated]
  def get(self, request, format=None):
        user = request.user
        print(f"User is {user.user_type}")
        if user.user_type == 'fpo':
            try:
                fpoid = get_object_or_404(FPO, user=user)
                print(f"FPO Details:{fpoid}")
                serializer = FPODetailsSerializer(fpoid)
                return Response({'message':'suceess',"data":serializer.data,
                                 },status=status.HTTP_200_OK)
            except FPO.DoesNotExist:
                return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)
        elif user.user_type =='supplier':
            try:
                supplier = get_object_or_404(Supplier, user=user)
                print(f"Supplier Details:{supplier}")
                serializer = SupplierDetailsSerializer(supplier)
                return Response({'message':'suceess',"data":serializer.data,
                                 },status=status.HTTP_200_OK)
            except Supplier.DoesNotExist:
                return Response({'error': 'Supplier details not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'Invalid User'}, status=status.HTTP_403_FORBIDDEN)
        
######################------------------------------------Profile Update Supplier or FPO-----------------------################
class UpdateProfile(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request, format=None):
        user = request.user
        data = request.data
        try:
            if user.user_type == 'fpo':
                try:
                    fpo_profile = FPO.objects.get(user=user)
                except FPO.DoesNotExist:
                    return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)
                fpo_bank_business, _ = BankBusinessDetails.objects.get_or_create(fk_fpo=fpo_profile)
                fpo_shop,_ = ShopDetails.objects.get_or_create(fk_fpo=fpo_profile)

                fpo_fields = [
                'mobile', 'fpo_name', 'address','state',
                'district', 'village'
                ]
                bank_business_fields = [
                'accountholder_name', 'account_number', 'bank_name', 'ifsc_code',
                'business_establishdate', 'pan_no', 'registration_id', 'gst_number'
                ]
                shop_details = [
                'shopName', 'shopContactNo', 'shopaddress', 'shop_opentime', 'shop_closetime',
                'shop_opendays', 'shop_closedon', 'shopLatitude', 'shopLongitude'
                ]

                for field in fpo_fields:
                    if field in data:
                        setattr(fpo_profile, field, data[field])
                for field in bank_business_fields:
                    if field in data:
                        setattr(fpo_bank_business, field, data[field])
                for field in shop_details:
                    if field in data:
                        setattr(fpo_shop, field, data[field])

                fpo_profile.save()
                fpo_bank_business.save()
                fpo_shop.save() 
                return Response({'message': 'FPO profile updated successfully'}, status=status.HTTP_200_OK)
            elif user.user_type =='supplier':
                try:
                    supplier_profile = Supplier.objects.get(user=user)
                except Supplier.DoesNotExist:
                    return Response({'error': 'Supplier details not found'}, status=status.HTTP_404_NOT_FOUND)
                supplier_bank_business, _ = BankBusinessDetails.objects.get_or_create(fk_supplier=supplier_profile)
                supplier_shop,_ = ShopDetails.objects.get_or_create(fk_supplier=supplier_profile)

                supplier_fields = [
                'mobile','supplier_name', 'address','state',
                'district', 'village']
                bank_business_fields = [
                'accountholder_name', 'account_number', 'bank_name', 'ifsc_code',
                'business_establishdate', 'pan_no', 'registration_id', 'gst_number'
                ]
                shop_details = [
                'shopName', 'shopContactNo', 'shopaddress', 'shop_opentime', 'shop_closetime',
                'shop_opendays', 'shop_closedon', 'shopLatitude', 'shopLongitude'
                ]
                for field in supplier_fields:
                    if field in data:
                        setattr(supplier_profile, field, data[field])
                for field in bank_business_fields:
                    if field in data:
                        setattr(supplier_bank_business, field, data[field])
                for field in shop_details:
                    if field in data:
                        setattr(supplier_shop, field, data[field])
                
                supplier_profile.save() 
                supplier_bank_business.save()
                supplier_shop.save()
                return Response({'message': 'Supplier profile updated successfully'}, status=status.HTTP_200_OK)

            return Response({'error': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)
           

        except Exception as e:
            trace = traceback.format_exc()
            return Response({
                'message': 'An error occurred',
                'error': str(e),
                'traceback': trace
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
############################---------------------------Profile Picture Update----------------##############
class UpdateProfilePicture(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request, format=None):
        user = request.user
        try:
            profile_picture = request.FILES.get('profile')
            print(f"Profile Picture: {profile_picture}")
            if profile_picture:
                if user.user_type == 'fpo':
                    try:
                        fpo_profile = FPO.objects.get(user=user)
                    except FPO.DoesNotExist:
                        return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)

                    fpo_profile.profile = profile_picture
                    fpo_profile.save()
                    return Response({'message': 'FPO profile picture updated successfully'}, status=status.HTTP_200_OK)

                elif user.user_type == 'supplier':
                    try:
                        supplier_profile = Supplier.objects.get(user=user)
                    except Supplier.DoesNotExist:
                        return Response({'error': 'Supplier details not found'}, status=status.HTTP_404_NOT_FOUND)

                    supplier_profile.profile = profile_picture
                    supplier_profile.save()
                    return Response({'message': 'Supplier profile picture updated successfully'}, status=status.HTTP_200_OK)

                else:
                    return Response({'error': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'No profile picture uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            trace = traceback.format_exc()
            return Response({
                'message': 'An error occurred',
                'error': str(e),
                'traceback': trace
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
###################------------------------------------Reset Password-----------------###############
class ResetPasssword(APIView):
    permission_classes = [AllowAny]
    def put(self, request, format=None):
        #user = request.user
        #print(f"User is {user.user_type}")
        try:
            mobile = request.data.get('mobile')
            new_password = request.data.get('new_password')
            
            if not mobile or not new_password:
                return Response({'error': 'Please provide mobile and new_password'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                user=CustomUser.objects.get(mobile=mobile,user_type="FPO")
                print(f"User is :{user}")
                print(f"USer type is :{user.user_type}")
                fpo = FPO.objects.get(mobile=user.mobile)
                print(f"Fpo is:{fpo}")
                if fpo:
                        fpo.password = make_password(new_password)
                        fpo.save()
                        user.set_password(new_password)
                        user.save()
                        return Response({'message': 'FPO Password reset successfully'}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'FPO not found with given mobile number'}, status=status.HTTP_404_NOT_FOUND)
            except FPO.DoesNotExist:
                return Response({'error': 'FPO not found with given mobile number'}, status=status.HTTP_404_NOT_FOUND)
            
        
            
        except Exception as e:
            trace = traceback.format_exc()
            return Response({
                'message': 'An error occurred',
                'error': str(e),
                'traceback': trace
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#################-----------------------------Add Farmers By FPO Profile------------------------- #################
class FarmerByFPO(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request,format=None):
        user = request.user
        print(f"User is {user.user_type}")
        try:
            data = request.data
            farmer_name = data.get('farmer_name')
            farmer_mobile = data.get('farmer_mobile')
            farmer_village = data.get('farmer_village')
            farmer_block = data.get('farmer_block')
            farmer_district = data.get('farmer_district')
            if user.user_type=='fpo':
                fpo=FPO.objects.get(user=user)
                user=CustomUser.objects.create(mobile=farmer_mobile,user_type='farmer')
                if FarmerProfile.objects.filter(mobile=farmer_mobile).exists():
                    return Response({'message': 'Mobile number already exists'}, status=status.HTTP_400_BAD_REQUEST)
                farmer = FarmerProfile.objects.create(
                user=user,
                fpo_name=fpo,
                name=farmer_name,
                mobile=farmer_mobile,
                village=farmer_village,
                block=farmer_block,
                district=farmer_district,
            )

            return Response({'message': 'Farmer added successfully', 'farmer_id': farmer.id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'message': 'An error occurred', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def delete(self, request,format=None):
        user = request.user
        print(f"User is {user.user_type}")
        try:
            farmer_ids=request.data.get('farmer_id',[])
            if not farmer_ids:
                return Response({'status': 'error', 'msg': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
            if user.user_type == 'fpo':
                    try:
                        fpo_profile = FPO.objects.get(user=user)
                    except FPO.DoesNotExist:
                        return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)
            farmer_profile= FarmerProfile.objects.filter(id__in=farmer_ids, fpo_name=fpo_profile)
            count_deleted = farmer_profile.count()
            farmer_profile.update(is_deleted=True)
            if count_deleted > 0:
                return Response({'status': 'success', 'msg': f'{count_deleted} farmers deleted successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'status': 'error', 'msg': 'No farmers found to delete'}, status=status.HTTP_404_NOT_FOUND)
        
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
    def put(self, request):
        user=request.user
        try:
            data = request.data
            farmer_id = data.get('farmer_id')
            if not farmer_id :
                return Response({'status': 'error', 'msg': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
            if user.user_type=="fpo":
                try:
                    fpo = FPO.objects.get(user=user)
                except FPO.DoesNotExist:
                    return Response({'status': 'error', 'msg': 'Fpo does not exist'}, status=status.HTTP_404_NOT_FOUND)
                try:
                    farmer=FarmerProfile.objects.get(id=farmer_id,fpo_name=fpo)
                except FarmerProfile.DoesNotExist:
                    return Response({'status': 'error', 'msg': 'Farmer does not exist'}, status=status.HTTP_404_NOT_FOUND)
                if 'farmer_name' in data:
                    farmer.name = data.get('farmer_name')

                if 'farmer_mobile' in data:
                    farmer_mobile = data.get('farmer_mobile')
                    farmer.mobile = farmer_mobile
                    user.mobile = farmer_mobile  
                    user.save()
                if 'farmer_village' in data:
                    farmer.village = data.get('farmer_village')

                if 'farmer_block' in data:
                    farmer.block = data.get('farmer_block')

                if 'farmer_district' in data:
                    farmer.district = data.get('farmer_district')
			

                farmer.save()

                return Response({'message': 'Farmer updated successfully', 'farmer_id': farmer.id}, status=status.HTTP_200_OK)
            else:
                return Response({'status': 'error', 'msg': 'Only FPO can update farmer profile'}, status=status.HTTP_403_FORBIDDEN)

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
        
############################----------------------Addd Farmers CSV------------------------##############
class AddFarmerCsv(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    def post(self, request):
        user = request.user
        print(f"User is {user.user_type}")
        try:
            csv_file = request.FILES.get('csv_file')
            user_type=user.user_type
            if not csv_file:
                return Response({'message': 'CSV file is required'}, status=status.HTTP_400_BAD_REQUEST)

            if user.user_type == 'fpo':
                try:
                    fpo_profile = FPO.objects.get(user=user)
                except FPO.DoesNotExist:
                    return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)

                df = pd.read_excel(csv_file)
                successful_records = []
                errors = []

                for index, row in df.iterrows():
                    try:
                        mobile = str(row['mobile_number']).strip()
                        if len(mobile) != 10 or not mobile.isdigit():
                            errors.append(f'Row {index + 1}: Invalid mobile number: {mobile}')
                            continue

                        name = str(row['name']).strip() if not pd.isna(row['name']) else ''
                        if len(name) > 100:
                            errors.append(f'Row {index + 1}: Name too long: {name}')
                            continue

                        village = str(row['village']).strip() if not pd.isna(row['village']) else ''
                        if len(village) > 100:
                            errors.append(f'Row {index + 1}: Village name too long: {village}')
                            continue

                        block = str(row['block']).strip() if not pd.isna(row['block']) else ''
                        if len(block) > 100:
                            errors.append(f'Row {index + 1}: Block name too long: {block}')
                            continue

                        district = str(row['district']).strip() if not pd.isna(row['district']) else ''
                        if len(district) > 100:
                            errors.append(f'Row {index + 1}: District name too long: {district}')
                            continue

                        if not FarmerProfile.objects.filter(mobile=mobile, fpo_name=fpo_profile).exists():
                            CustomUser.objects.create(mobile=mobile,user_type=user_type)
                            FarmerProfile.objects.create(
                                user=user,
                                fpo_name=fpo_profile,
                                name=name,
                                mobile=mobile,
                                village=village,
                                block=block,
                                district=district
                            )
                            successful_records.append(f'Row {index + 1}: Farmer added successfully')
                        else:
                            errors.append(f'Row {index + 1}: Farmer with mobile number {mobile} already exists')

                    except Exception as e:
                        errors.append(f'Row {index + 1}: {str(e)}')

                return Response({
                    'message': 'Farmers added via Excel',
                    'successful_records_count': len(successful_records),
                    'errors_count': len(errors),
                    'successful_records': successful_records,
                    'errors': errors
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
######----------------------Get Single Farmer Details by  FPO------------------------#########################
class GetSingleFarmerDetailsbyFPO(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,format=None):
            user = request.user
            farmer_id=request.query_params.get("farmer_id")
            print(f"User is {user.user_type}")
            try:
                if user.user_type == 'fpo':
                    try:
                        fpo_profile = FPO.objects.get(user=user)
                    except FPO.DoesNotExist:
                        return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)

                fpo_farmers = FarmerProfile.objects.filter(fpo_name_id=fpo_profile,id=farmer_id)
                farmers_data = []
                for farmer in fpo_farmers:
                    farmers_data.append({
                    'farmer_id': farmer.id,
                    'farmer_name': farmer.name,
                    'farmer_mobile': farmer.mobile,
                    'farmer_district': farmer.district,
                    'farmer_village':farmer.village,
                    'farmer_block':farmer.block,
                    'created_at':farmer.created_at
                })

                return Response({'status': 'success', 'data': farmers_data},status=status.HTTP_200_OK)
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
#################------------------------------------Get all Farmer by FPO-------------------------####################
class GetAllFarmerbyFPO(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,format=None):
        user = request.user
        print(f"User is {user.user_type}")
        try:
            if user.user_type == 'fpo':
                try:
                    fpo_profile = FPO.objects.get(user=user)
                except FPO.DoesNotExist:
                    return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)

                fpo_farmers = FarmerProfile.objects.filter(fpo_name=fpo_profile,is_deleted=False)
                paginator=FarmersAllPagination()
                result_page=paginator.paginate_queryset(fpo_farmers, request)
                serializer = FarmerProfileSerializer(result_page, many=True)
                return paginator.get_paginated_response(serializer.data)
            else:
                return Response({'error': 'Only FPO users can access this endpoint'}, status=status.HTTP_403_FORBIDDEN)
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
##############----------------------------------------Product Details FPO and Supplier------------------------##############
class ProductDetailsAddGetDelUpdate(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request,format=None):
        user=request.user
        print(f"User is {user.user_type}")
        try:
            producttype=request.data.get('producttype')
            productname=request.data.get('productName')
            if not producttype or not productname:
                return Response({'error':'Product Name and Product Type are required'},status=status.HTTP_400_BAD_REQUEST)
            if user.user_type == 'fpo':
                try:
                    fpo_profile = FPO.objects.get(user=user)
                    print(f"Fpo Profile : {fpo_profile}")
                except FPO.DoesNotExist:
                    return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)
                product_data = {
                'productName': productname,
                'productDescription': request.data.get('productDescription',' '),
                'composition': request.data.get('composition',' '),
                'measurement_type': request.data.get('measurement_type'),
                'measurement_unit':request.data.get('measurement_unit'),
                'selling_status': request.data.get('selling_status'),
                'Category':request.data.get('Category'),
                'quantity':request.data.get('quantity'),
                'fk_productype_id': producttype,
                'fk_fpo': fpo_profile,
                'expiry_date': request.data.get('expiry_date')
                                }
                if producttype in [1,3]:
                    product_data['manufacturerName'] = request.data.get('manufacturerName',' ')
                elif producttype==2:
                    product_data['fk_crops_id'] =request.data.get('crop_id')
                    product_data['fk_variety_id'] = request.data.get('variety')
                ###FPO Supplier Information
                supplier=FPOSuppliers.objects.create(
                fk_fpo=fpo_profile,
                fk_productype_id=producttype,
                quantity=request.data.get('quantity'),
                total_amount=request.data.get('purchase_price'),
                party_name=request.data.get('party_name'),
                party_mobileno=request.data.get('mobileno'),
                party_company=request.data.get('company_name'),
                unit_price=request.data.get('unit_price'),
                party_gst=request.data.get('party_gst',' ')
                    )
                product = ProductDetails.objects.create(**product_data)
                product.fk_fposupplier=supplier
                product.save()
                ##FPO Prices
                ProductPrices.objects.create(
                fk_product=product,
                purchase_price=request.data.get('purchase_price'),
                unit_price=request.data.get('unit_price'),
                #discount=data.get('discount',0),
                final_price_unit=request.data.get('final_price'),
                fk_fpo=fpo_profile,
                fk_fposupplier=supplier  
                                )
                InventoryDetails.objects.create(
                fk_product=product,
                fk_fpo=fpo_profile,
                stock=request.data.get('quantity', 0),
                fk_fposupplier=supplier,
                fk_productype_id=producttype
                )
                return Response({'message': 'FPO Product created & Added successfully!'})
            elif user.user_type=='supplier':
                try:
                    supplier_info = Supplier.objects.get(user=user)
                except Supplier.DoesNotExist:
                    return Response({'error': 'Supplier details not found'}, status=status.HTTP_404_NOT_FOUND)
                product_data = {
                'productName': productname,
                'productDescription': request.data.get('productDescription',' '),
                'composition': request.data.get('composition',' '),
                'measurement_type': request.data.get('measurement_type'),
                'measurement_unit':request.data.get('measurement_unit'),
                'selling_status': request.data.get('selling_status'),
                'Category':request.data.get('Category'),
                'quantity':request.data.get('quantity'),
                'fk_productype_id': producttype,
                'expiry_date': request.data.get('expiry_date',None),
                'manufacturerName': request.data.get('manufacturerName',' '),
                            }
                product = ProductDetails.objects.create(**product_data)
                product.fk_supplier.set([supplier_info])
                supplier = InputSuppliers.objects.create(
                    fk_supplier=supplier_info,
                    fk_productype_id=producttype,
                    quantity=request.data.get('quantity'),
                    total_amount=request.data.get('purchase_price'),
                    party_name=request.data.get('party_name'),
                    party_mobileno=request.data.get('mobileno'),
                    party_company=request.data.get('company_name'),
                    unit_price=request.data.get('unit_price'),
                    party_gst=request.data.get('party_gst')
                        )
                product.fk_inputsupplier = supplier
                product.save()
                ProductPrices.objects.create(
                fk_product=product,
                fk_supplier=supplier_info,
                purchase_price=request.data.get('purchase_price'),
                unit_price=request.data.get('unit_price'),
                discount=request.data.get('discount',0),
                final_price_unit=request.data.get('final_price'),
                fk_inputsupplier=supplier
                )

                InventoryDetails.objects.create(
                fk_product=product,
                stock=request.data.get('quantity', 0),
                fk_inputsupplier=supplier,
                fk_supplier=supplier_info,
                fk_productype_id=producttype
                 )
                return Response({'message': 'Product created & Added successfully by Supplier!'})
            else:
                return Response({'message': 'Invalid user type'}, status=403)
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
    def put(self,request,format=None):
        user=request.user
        print(F"User: {user}")
        try:
            if user.user_type == 'fpo':
                product_ids = request.data.get('product_id', [])
                if not product_ids:
                    return Response({'message': 'Product id must be required'}, status=404)
                try:
                    fpo_profile = FPO.objects.get(user=user)
                    print(f"Fpo Profile : {fpo_profile}")
                except FPO.DoesNotExist:
                    return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)
                products = ProductDetails.objects.filter(id__in=product_ids, fk_fpo=fpo_profile)
                if not products.exists():
                    return Response({'message': 'No products found'}, status=404)
                ########----Ierate through Products
                for product in products:
                    product.quantity = request.data.get('quantity', product.quantity)
                    product.expiry_date = request.data.get('expiry_date', product.expiry_date)
                    product.productName = request.data.get('productName', product.productName)
                    product.productDescription = request.data.get('productDescription', product.productDescription)
                    product.composition = request.data.get('composition', product.composition)
                    product.measurement_type = request.data.get('measurement_type', product.measurement_type)
                    product.measurement_unit = request.data.get('measurement_unit', product.measurement_unit)
                    product.selling_status = request.data.get('selling_status', product.selling_status)
                    product.Category = request.data.get('Category', product.Category)
                    filter_type = request.data.get('filter_type')
                    if filter_type in ["Agricultural Inputs", "Finish Goods"]:
                        product.manufacturerName = request.data.get('manufacturerName', product.manufacturerName)
                    elif filter_type == "Crops":
                        product.fk_crops_id = request.data.get('crop_id', product.fk_crops_id)
                        product.fk_variety_id = request.data.get('variety_id', product.fk_variety_id)
            
                    product.save()

                    # Update the product prices
                    try:
                        product_prices = ProductPrices.objects.get(fk_product=product, fk_fpo=fpo_profile)
                        product_prices.purchase_price = request.data.get('purchase_price', product_prices.purchase_price)
                        product_prices.unit_price = request.data.get('unit_price', product_prices.unit_price)
                        product_prices.discount = request.data.get('discount', product_prices.discount)
                        product_prices.final_price_unit = request.data.get('final_price', product_prices.final_price_unit)
                        product_prices.save()
                    except ProductPrices.DoesNotExist:
                        return Response({'message': f'Product prices for product ID {product.id} not found'}, status=404)
            
                    # Update the inventory
                    try:
                        inventory = InventoryDetails.objects.get(fk_product=product,fk_fpo=fpo_profile)
                        inventory.stock = product.quantity
                        inventory.save()
                    except InventoryDetails.DoesNotExist:
                        return Response({'message': f'Inventory details for product ID {product.id} not found'}, status=404)
                return Response({'status':'success','message': 'Products updated successfully'},status=status.HTTP_200_OK)
            elif user.user_type=="supplier":
                product_ids = request.data.get('product_id', [])
                if not product_ids:
                    return Response({'message': 'Product id must be required'}, status=404)
                try:
                    supplier_info = Supplier.objects.get(user=user)
                    print(f"Supplier Profile : {supplier_info}")
                except Supplier.DoesNotExist:
                    return Response({'error': 'Supplier details not found'}, status=status.HTTP_404_NOT_FOUND)
                products = ProductDetails.objects.filter(id__in=product_ids, fk_supplier=supplier_info)
                if not products.exists():
                    return Response({'message': 'No products found'}, status=404)
                ########----Ierate through Products
                for product in products:
                    product.quantity = request.data.get('quantity', product.quantity)
                    product.expiry_date = request.data.get('expiry_date', product.expiry_date)
                    product.productName = request.data.get('productName', product.productName)
                    product.productDescription = request.data.get('productDescription', product.productDescription)
                    product.composition = request.data.get('composition', product.composition)
                    product.measurement_type = request.data.get('measurement_type', product.measurement_type)
                    product.measurement_unit = request.data.get('measurement_unit', product.measurement_unit)
                    product.selling_status = request.data.get('selling_status', product.selling_status)
                    product.Category = request.data.get('Category', product.Category)
                    product.save()
                    # Update the product prices
                    try:
                        product_prices = ProductPrices.objects.get(fk_product=product, fk_supplier=supplier_info)
                        product_prices.purchase_price = request.data.get('purchase_price', product_prices.purchase_price)
                        product_prices.unit_price = request.data.get('unit_price', product_prices.unit_price)
                        product_prices.discount = request.data.get('discount', product_prices.discount)
                        product_prices.final_price_unit = request.data.get('final_price', product_prices.final_price_unit)
                        product_prices.save()
                    except ProductPrices.DoesNotExist:
                        return Response({'message': f'Product prices for product ID {product.id} not found'}, status=404)
            
                    # Update the inventory
                    try:
                        inventory = InventoryDetails.objects.get(fk_product=product,fk_supplier=supplier_info)
                        inventory.stock = product.quantity
                        inventory.save()
                    except InventoryDetails.DoesNotExist:
                        return Response({'message': f'Inventory details for product ID {product.id} not found'}, status=404)
                return Response({'status':'success','message': 'Products updated successfully'},status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Invalid user type'}, status=403)
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
    def delete(self, request, formats=None):
        user=request.user
        print(F"User: {user}")
        try:
            product_ids = request.data.get('product_id', [])
            if not product_ids:
                    return Response({'message': 'Product id must be required'}, status=404)
            if user.user_type == 'fpo':
                try:
                    fpo_profile = FPO.objects.get(user=user)
                    print(f"Fpo Profile : {fpo_profile}")
                except FPO.DoesNotExist:
                    return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)
                products = ProductDetails.objects.filter(id__in=product_ids, fk_fpo=fpo_profile)
                if not products.exists():
                    return Response({'message': 'No products found'}, status=404)
                productdel_count = products.count()
                products.update(is_deleted=True)
                ProductPrices.objects.filter(fk_product__in=products).update(is_deleted=True)
                InventoryDetails.objects.filter(fk_product__in=products).update(is_deleted=True)
                if productdel_count>0:
                    return Response({'message': f'{productdel_count} products deleted successfully'},status=status.HTTP_200_OK)
                else:
                    return Response({'message': 'No products found to delete'}, status=404)
            elif user.user_type =='supplier':
                try:
                    supplier_info = Supplier.objects.get(user=user)
                    print(f"Supplier Profile : {supplier_info}")
                except Supplier.DoesNotExist:
                    return Response({'error': 'Supplier details not found'}, status=status.HTTP_404_NOT_FOUND)
                products = ProductDetails.objects.filter(id__in=product_ids, fk_supplier=supplier_info)
                if not products.exists():
                    return Response({'message': 'No products found'}, status=404)
                productdel_count = products.count()
                products.update(is_deleted=True)
                ProductPrices.objects.filter(fk_product__in=products).update(is_deleted=True)
                InventoryDetails.objects.filter(fk_product__in=products).update(is_deleted=True)
                if productdel_count>0:
                    return Response({'message': f'{productdel_count} products deleted successfully'},status=status.HTTP_200_OK)
                else:
                    return Response({'message': 'No products found to delete'}, status=404)
                
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
        user=request.user
        print(f"User: {user}")
        try:
            if user.user_type == 'fpo':
                product_id = request.query_params.get('product_id')

                try:
                    fpo_profile = FPO.objects.get(user=user)
                    print(f"Farmer Profile : {fpo_profile}")
                except FPO.DoesNotExist:
                    return Response({'error': 'Farmer details not found'}, status=status.HTTP_404_NOT_FOUND)
                products = ProductDetails.objects.filter(fk_fpo=fpo_profile, is_deleted=False)
                if product_id:
                    products = products.filter(id=product_id)

                serializer = FPOProductDetailFilterSerializer(products, many=True, context={'fpo_id': fpo_profile.id})
                return Response({'data':serializer.data}, status=status.HTTP_200_OK)
            elif user.user_type =='supplier':
                try:
                    supplier_profile = Supplier.objects.get(user=user)
                    print(f"Supplier Profile :{supplier_profile}")
                except Supplier.DoesNotExist:
                    return Response({'error': 'Supplier details not found'}, status=status.HTTP_404_NOT_FOUND)
                products = ProductDetails.objects.filter(fk_supplier=supplier_profile, is_deleted=False)
                if product_id:
                    products = products.filter(id=product_id)

                serializer = SupplierProductFilterDetailsSerializer(products, many=True, context={'supplier_id': supplier_profile.id})
                return Response(serializer.data, status=status.HTTP_200_OK)
                          
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
#####################--------------------GET Product DetaILS bY FPO/Supplier-------------#####
class GetProductDetailsByFPOSupplier(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        user = request.user
        print(f"User is {user.user_type}")
        try:
            productype_id=request.query_params.get('producttype')
            if not productype_id:
                return Response({'error': 'Product Type ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            if user.user_type == 'fpo':
                try:
                    fpo_profile=FPO.objects.get(user=user)
                except FPO.DoesNotExist:
                    return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)
                products = ProductDetails.objects.filter(fk_productype_id=productype_id,fk_fpo=fpo_profile,is_deleted=False)
                print(f"Product ARE :{products}")
                paginator=GetallProductPagination()
                result_page = paginator.paginate_queryset(products, request)
                serializer=FPOProductDetailFilterSerializer(result_page, many=True, context={'fpo_id': fpo_profile.id})
                print(f"Products Data : {serializer.data}")
                return paginator.get_paginated_response({
                        'status': 'success',
                        'data': serializer.data,
                    })
            elif user.user_type =='supplier':
                try:
                    supplier_profile=Supplier.objects.get(user=user)
                except Supplier.DoesNotExist:
                    return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)
                products = ProductDetails.objects.filter(fk_productype_id=productype_id,fk_supplier=supplier_profile)
                print(f"Product ARE :{products}")
                paginator=GetallProductPagination()
                result_page = paginator.paginate_queryset(products, request)
                serializer = SupplierProductFilterDetailsSerializer(result_page, many=True, context={'supplier_id': supplier_profile.id})
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid User Type'}, status=status.HTTP_403_FORBIDDEN)

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
#####################-----------------------ADD PRODUCT CSV------------------------------##############
class ADDProductDetailsCSV(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        user = request.user
        print(f"User is {user.user_type}")

        try:
            file = request.FILES.get('file')
            producttype = request.data.get('producttype')
            print(f"Product Type is :{producttype}")

            if not file:
                return Response({'error': 'Excel file is required'}, status=status.HTTP_400_BAD_REQUEST)
            if not producttype:
                return Response({'error': 'Product type is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Read the Excel file using pandas
            df = pd.read_excel(file)

            for _, row in df.iterrows():
                productname = row.get('ProductName')
                if not productname:
                    continue  # Skip rows with missing essential data

                if user.user_type == 'fpo':
                    try:
                        fpo_profile = FPO.objects.get(user=user)
                        print(f"Fpo Profile : {fpo_profile}")
                    except FPO.DoesNotExist:
                        return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)

                    product_data = {
                        'productName': productname,
                        'productDescription': row.get('ProductDescription', ' '),
                        'composition': row.get('composition', ' '),
                        'measurement_type': row.get('Measurement'),
                        'measurement_unit': row.get('MeasurementIn'),
                        'selling_status': row.get('Selling Status'),
                        'Category': row.get('Category'),
                        'quantity': row.get('Quantity'),
                        'fk_productype_id': producttype,
                        'fk_fpo': fpo_profile,
                        'expiry_date': row.get('Expiry Date')
                    }

                    if producttype in ["1", "3"]:
                        product_data['manufacturerName'] = row.get('Manufacturer', ' ')
                    elif producttype == "2":
                        product_data['fk_crops_id'] = row.get('crop_id')
                        product_data['fk_variety_id'] = row.get('variety')

                    # FPO Supplier Information
                    supplier = FPOSuppliers.objects.create(
                        fk_fpo=fpo_profile,
                        fk_productype_id=producttype,
                        quantity=row.get('Quantity'),
                        total_amount=row.get('Purchase Price'),
                        party_name=row.get('Party Name'),
                        party_mobileno=row.get('Mobile No'),
                        party_company=row.get('company_name'),
                        unit_price=row.get('Unit Price'),
                        party_gst=row.get('Party GST', ' ')
                    )
                    print(f"FPO Supplier Object:{supplier}")

                    product = ProductDetails.objects.create(**product_data)
                    print(f"Product Objects:{product}")
                    product.fk_fposupplier = supplier
                    product.save()

                    # FPO Prices
                    ProductPrices.objects.create(
                        fk_product=product,
                        purchase_price=row.get('Purchase Price'),
                        unit_price=row.get('Unit Price'),
                        final_price_unit=row.get('Selling Price'),
                        fk_fpo=fpo_profile,
                        fk_fposupplier=supplier
                    )

                    InventoryDetails.objects.create(
                        fk_product=product,
                        fk_fpo=fpo_profile,
                        stock=row.get('Quantity', 0),
                        fk_fposupplier=supplier
                    )

                elif user.user_type == 'supplier':
                    try:
                        supplier_info = Supplier.objects.get(user=user)
                        print(f"Supplier Info :{supplier_info}")
                    except Supplier.DoesNotExist:
                        return Response({'error': 'Supplier details not found'}, status=status.HTTP_404_NOT_FOUND)

                    product_data = {
                        'productName': productname,
                        'productDescription': row.get('ProductDescription', ' '),
                        'composition': row.get('composition', ' '),
                        'measurement_type': row.get('Measurement'),
                        'measurement_unit': row.get('MeasurementIn'),
                        'selling_status': row.get('Selling Status'),
                        'Category': row.get('Category'),
                        'quantity': row.get('Quantity'),
                        'fk_productype_id': producttype,
                        'expiry_date': row.get('Expiry Date', ' '),
                        'manufacturerName': row.get('Manufacturer', ' '),
                    }

                    product = ProductDetails.objects.create(**product_data)
                    print(f"Product Objects:{product}")
                    product.fk_supplier.set([supplier_info])

                    supplier = InputSuppliers.objects.create(
                        fk_supplier=supplier_info,
                        fk_productype_id=producttype,
                        quantity=row.get('Quantity'),
                        total_amount=row.get('Purchase Price'),
                        party_name=row.get('Party Name'),
                        party_mobileno=row.get('Mobile No'),
                        party_company=row.get('company_name'),
                        unit_price=row.get('Unit Price'),
                        party_gst=row.get('Party GST', ' ')
                    )
                    print(f"Supplier Inputs Supplier Info :{supplier}")

                    product.fk_inputsupplier = supplier
                    product.save()

                    ProductPrices.objects.create(
                        fk_product=product,
                        fk_supplier=supplier_info,
                        purchase_price=row.get('Purchase Price'),
                        unit_price=row.get('Unit Price'),
                        final_price_unit=row.get('Selling Price'),
                        discount=row.get('discount', 0),
                        fk_inputsupplier=supplier
                    )

                    InventoryDetails.objects.create(
                        fk_product=product,
                        stock=row.get('Quantity', 0),
                        fk_inputsupplier=supplier,
                        fk_supplier=supplier_info,
                        fk_productype__id=producttype
                    )


            return Response({'message': 'Products created & added successfully!'})
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
#####################----------------------GEt all Productby FPO and Suppliers------------------###############
class GetAllProductsFponSupplier(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,format=None):
        try:
            user = request.user
            print(f"User is :{user.user_type}")
            if user.user_type == 'fpo':
                try:
                    fpo_profile = FPO.objects.get(user=user)
                    print(f"Fpo Profile : {fpo_profile}")
                except FPO.DoesNotExist:
                        return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)
                products = InventoryDetails.objects.filter(fk_fpo=fpo_profile)
                print(f"Product Are:{products}")
                if not products.exists():
                    return Response({'message': 'No products found for the specified filter type'}, status=status.HTTP_404_NOT_FOUND)
                data=FPOProductDetailSerializer(products,many=True)
                return Response({'status': 'success', 'products': data.data}, status=status.HTTP_200_OK)
            elif user.user_type == 'supplier':
                try:
                    supplier_info = Supplier.objects.get(user=user)
                    print(f"Supplier Info :{supplier_info}")
                except Supplier.DoesNotExist:
                    return Response({'error': 'Supplier details not found'}, status=status.HTTP_404_NOT_FOUND)
                products = InventoryDetails.objects.filter(fk_supplier=supplier_info)
                if not products.exists():
                    return Response({'message': 'No products found for the specified filter type'}, status=status.HTTP_404_NOT_FOUND)
                data=SupplierProductDetailSerializer(products,many=True)
                return Response({'status': 'success', 'products': data.data}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'User type not recognized'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'message': 'An error occurred', 'error': traceback.format_exc()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#########################-------------------GET ALL Purchases Info by FPO/Suppliers---------------------#################
class PurchaseInfo(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,format=None):
        user=request.user
        print(f"User: {user}")
        try:
            if user.user_type == 'fpo':
                try:
                    fpo_profile = FPO.objects.get(user=user)
                    print(f"Fpo Profile : {fpo_profile}")
                except FPO.DoesNotExist:
                    return Response({'error': 'Fpo details not found'}, status=status.HTTP_404_NOT_FOUND)
                suppliers=FPOSuppliers.objects.filter(fk_fpo=fpo_profile)
                if not suppliers.exists():
                    return Response({'message': 'No suppliers found'}, status=status.HTTP_200_OK)
                paginator=GetallPurchasePagination()
                result_page = paginator.paginate_queryset(suppliers, request)
                serializer = FPOSuppliersSerializer(result_page, many=True, context={'fpo_id': fpo_profile.id})
                return paginator.get_paginated_response({
                        'status': 'success',
                        'data': serializer.data,
                    })
            elif user.user_type =='supplier':
                try:
                    supplier_profile = Supplier.objects.get(user=user)
                    print(f"Supplier Profile :{supplier_profile}")
                except Supplier.DoesNotExist:
                    return Response({'error': 'Supplier details not found'}, status=status.HTTP_404_NOT_FOUND)
                suppliers=InputSuppliers.objects.filter(fk_supplier=supplier_profile)
                if not suppliers.exists():
                    return Response({'message': 'No suppliers found'}, status=status.HTTP_404_NOT_FOUND)
                serializer = ThirdPartySuppliersSerializer(suppliers, many=True, context={'fk_supplier_id': supplier_profile.id})
                return Response({"message": "success", 'supplier_details': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Invalid user type'}, status=403)
        except Exception as e:
                error_message = str(e)
                trace = traceback.format_exc()
                return Response({"status": "error","message": "An unexpected error occurred",
                                 "error_message": error_message,"traceback": trace},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
###########################--------------------GE ALL Products FPO/Suppliers----------------##############
class GetallProductsInfo(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            if user.user_type == 'fpo':
                try:
                    fpo_profile = FPO.objects.get(user=user)
                except FPO.DoesNotExist:
                    return Response({'error': 'Fpo details not found'}, status=status.HTTP_404_NOT_FOUND)

                products = InventoryDetails.objects.filter(fk_fpo=fpo_profile, is_deleted=False)

                paginator = GetallProductPagination()
                result_page = paginator.paginate_queryset(products, request)
                if result_page is not None:
                    product_serializer = FPOProductDetailSerializer(result_page, many=True)
                    prices = ProductPrices.objects.filter(fk_product__in=[p.fk_product for p in products])
                    prices_serializer = ProductPricesSerializer(prices, many=True)
                    return paginator.get_paginated_response({
                        'status': 'success',
                        'products': product_serializer.data,
                        'prices': prices_serializer.data
                    })

            elif user.user_type == 'supplier':
                try:
                    supplier_profile = Supplier.objects.get(user=user)
                except Supplier.DoesNotExist:
                    return Response({'error': 'Supplier details not found'}, status=status.HTTP_404_NOT_FOUND)

                products = InventoryDetails.objects.filter(fk_supplier=supplier_profile, is_deleted=False)

                paginator = GetallProductPagination()
                result_page = paginator.paginate_queryset(products, request)
                if result_page is not None:
                    product_serializer = SupplierProductDetailSerializer(result_page, many=True)
                    prices = ProductPrices.objects.filter(fk_product__in=[p.fk_product for p in products])
                    prices_serializer = ProductPricesSerializer(prices, many=True)
                    return paginator.get_paginated_response({
                        'status': 'success',
                        'products': product_serializer.data,
                        'prices': prices_serializer.data
                    })

            return Response({'message': 'Invalid user type'}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response({
                "status": "error",
                "message": "An unexpected error occurred",
                "error_message": error_message,
                "traceback": trace
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#################----------------------------Inventory Section FPO/Suppliers------------------------#################
class InventorySection(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        user=request.user
        print(f"User: {user}")
        try:
            filter_type=request.query_params.get('filter_type')
            if not filter_type:
                return Response({'error': 'Filter type is required'}, status=400)
            if user.user_type == 'fpo':
                try:
                    fpo_profile = FPO.objects.get(user=user)
                    print(f"Fpo Profile : {fpo_profile}")
                except FPO.DoesNotExist:
                    return Response({'error': 'Fpo details not found'}, status=status.HTTP_404_NOT_FOUND)
                products = ProductDetails.objects.filter(fk_fpo=fpo_profile,is_deleted=False,fk_productype_id=filter_type)
                print(f"Product Data: {products}")
                inventory = InventoryDetails.objects.filter(fk_product__in=[p for p in products],fk_fpo=fpo_profile)
                print(f"Inventory Data: {inventory}")
                paginator=GetallInventoryPagination()
                result_page = paginator.paginate_queryset(inventory, request)
                print(f"Result page: {result_page}")
                inventory_serializer=FPOProductDetailSerializer(result_page,many=True)
                print(f"Inventory's: {inventory_serializer.data}")
                return paginator.get_paginated_response({
                        'status': 'success',
                        'inventory': inventory_serializer.data,
                    })
            elif user.user_type =='supplier':
                try:
                    supplier_profile = Supplier.objects.get(user=user)
                    print(f"Supplier Profile :{supplier_profile}")
                except Supplier.DoesNotExist:
                    return Response({'error': 'Supplier details not found'}, status=status.HTTP_404_NOT_FOUND)
                products = ProductDetails.objects.filter(fk_supplier=supplier_profile,is_deleted=False,fk_productype_id=filter_type)
                inventory = InventoryDetails.objects.filter(fk_product__in=[p for p in products],fk_supplier=supplier_profile)
                print(f"Inventory Data: {inventory}")
                paginator=GetallInventoryPagination()
                result_page = paginator.paginate_queryset(inventory, request)
                inventory_serializer=SupplierProductDetailSerializer(result_page,many=True)
                print(f"Inventory's: {inventory_serializer.data}")
                return paginator.get_paginated_response({
                        'status': 'success',
                        'inventory': inventory_serializer.data,
                    })
            else:
                return Response({'message': 'Invalid user type'}, status=403)
        except Exception as e:
                error_message = str(e)
                trace = traceback.format_exc()
                return Response({"status": "error","message": "An unexpected error occurred",
                                 "error_message": error_message,"traceback": trace},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    def put(self,request,format=None):
        user=request.user
        print(f"User: {user}")
        try:
            inventory_id=request.data.get('inventory_id')
            new_stock=request.data.get('new_stock')
            if not inventory_id or not new_stock:
                    return Response({'error': 'Product id and quantity are required'}, status=400)
            if user.user_type == 'fpo':
                try:
                    fpo_profile = FPO.objects.get(user=user)
                    print(f"Fpo Profile : {fpo_profile}")
                except FPO.DoesNotExist:
                    return Response({'error': 'Fpo details not found'}, status=status.HTTP_404_NOT_FOUND)

                inventory = InventoryDetails.objects.filter(id=inventory_id,fk_fpo=fpo_profile,is_deleted=False).first()
                print(f"Inventory Data: {inventory}")
                if inventory:
                     product = ProductDetails.objects.filter(id=inventory.fk_product.id).first()
                     if not product:
                        return Response({'error': 'Associated product not found.'}, status=400)
                if new_stock > product.quantity:
                    return Response({
                    'error': 'Stock update failed. New stock value exceeds the product\'s original quantity.',
                    'max_allowed': product.quantity
                }, status=400)
                inventory.stock = new_stock
                inventory.save()
                return Response({'status':'success','message':'Inventory Updated Successfully'},status=status.HTTP_200_OK)
            elif user.user_type=="supplier":
                try:
                    supplier_profile = Supplier.objects.get(user=user)
                    print(f"Supplier Profile :{supplier_profile}")
                except Supplier.DoesNotExist:
                    return Response({'error': 'Supplier details not found'}, status=status.HTTP_404_NOT_FOUND)
                inventory = InventoryDetails.objects.filter(id=inventory_id,fk_supplier=supplier_profile,is_deleted=False).first()
                print(f"Inventory Data: {inventory}")
                if inventory:
                     product = ProductDetails.objects.filter(id=inventory.fk_product.id).first()
                     if not product:
                        return Response({'error': 'Associated product not found.'}, status=400)
                if new_stock > product.quantity:
                    return Response({
                    'error': 'Stock update failed. New stock value exceeds the product\'s original quantity.',
                    'max_allowed': product.quantity
                }, status=400)
                inventory.stock = new_stock
                inventory.save()
                return Response({'status':'success','message':'Inventory Updated Successfully'},status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Invalid user type'}, status=403)
        except Exception as e:
                error_message = str(e)
                trace = traceback.format_exc()
                return Response({"status": "error","message": "An unexpected error occurred",
                                 "error_message": error_message,"traceback": trace},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
########################------------------------------------Sales Section FPO/Supplier---------------###################
class AddGetSales(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        try:
            buyer_name = request.data.get('buyer_name')
            mobile_no = request.data.get('mobile_no')
            address = request.data.get('address')
            sale_date = request.data.get('sale_date')
            products = request.data.get('products')
            payment = request.data.get('payment')

            if not all([sale_date, payment, products, mobile_no]):
                return Response({'error': 'Required fields are missing'}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                if user.user_type == 'fpo':
                    customer, profile = self.handle_fpo_user(user, buyer_name, mobile_no, address)
                elif user.user_type == 'supplier':
                    customer, profile = self.handle_supplier_user(user, buyer_name, mobile_no, address)
                else:
                    return Response({'error': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)

                sale_responses, total_price = self.process_products(products, customer, sale_date, payment, profile, user.user_type)

            return Response({
                "message": "Sales processed successfully", 
                "sales": sale_responses,
                "total_price": total_price
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def handle_fpo_user(self, user, buyer_name, mobile_no, address):
        fpo_profile = get_object_or_404(FPO, user=user)
        is_farmer = FarmerProfile.objects.filter(mobile=mobile_no, fpo_name=fpo_profile).exists()
        discount = self.request.data.get('discount', 0) if is_farmer else 0
        
        customer_data = {
            'buyer_name': buyer_name,
            'mobile_no': mobile_no,
            'address': address,
            'fk_fpo': fpo_profile.id
        }
        customer_serializer = FPOCustomerDetailsSerializer(data=customer_data)
        customer_serializer.is_valid(raise_exception=True)
        customer = customer_serializer.save()
        
        return customer, fpo_profile

    def handle_supplier_user(self, user, buyer_name, mobile_no, address):
        supplier_profile = get_object_or_404(Supplier, user=user)
        
        customer_data = {
            'buyer_name': buyer_name,
            'mobile_no': mobile_no,
            'address': address,
            'fk_supplier': supplier_profile.id
        }
        customer_serializer = SupplierCustomerDetailsSerializer(data=customer_data)
        customer_serializer.is_valid(raise_exception=True)
        customer = customer_serializer.save()
        
        return customer, supplier_profile

    def process_products(self, products, customer, sale_date, payment, profile, user_type):
        sale_responses = []
        total_price = 0

        for product_data in products:
            quantity = product_data.get('Quantity')
            inventory_id = product_data.get('inventory_id')
            
            inventory = get_object_or_404(InventoryDetails, id=inventory_id)
            if inventory.stock < quantity:
                raise ValueError(f'Insufficient stock for product id: {inventory_id}')

            product = inventory.fk_product
            productprice = get_object_or_404(ProductPrices, fk_product=product)

            price = productprice.final_price_unit
            amount = price * quantity * (1 - self.request.data.get('discount', 0) / 100) if user_type == 'fpo' else price * quantity

            inventory.stock -= quantity
            inventory.save()
            product.quantity -= quantity
            product.save()

            sale_data = {
                'fk_invent': inventory.id,
                'amount': amount,
                'sales_date': sale_date,
                'final_price': price,
                'payment_method': payment,
                'fk_custom': customer.id
            }
            sale_serializer = ProductSaleSerializer(data=sale_data)
            sale_serializer.is_valid(raise_exception=True)
            sale = sale_serializer.save()
            sale_responses.append(sale_serializer.data)

            total_price += amount

            self.create_sales_record(user_type, customer.buyer_name, quantity, amount, profile, sale_date, product, inventory)

        return sale_responses, total_price

    def create_sales_record(self, user_type, buyer_name, quantity, amount, profile, sale_date, product, inventory):
        common_data = {
            'name': buyer_name,
            'quantity': quantity,
            'total_amount': amount,
            'sales_date': sale_date,
            'product_name': product.productName,
            'category': inventory.fk_product.fk_productype.product_type,
        }

        if user_type == 'fpo':
            sales_record_data = {
                **common_data,
                'fk_fpo': profile.id,
                'fk_productype': inventory.fk_productype.id,
                'fk_fposupplier': inventory.fk_fposupplier.id
            }
            sales_record_serializer = FPOSalesRecordItemSerializer(data=sales_record_data)
            #print(f"Sales Record Serializer :{sales_record_serializer.data}")
        else:
            sales_record_data = {
                **common_data,
                'fk_supplier': profile.id,
                'fk_inputsupplier_id': inventory.fk_inputsupplier.id
            }
            sales_record_serializer = SupplierSalesRecordItemSerializer(data=sales_record_data)

        sales_record_serializer.is_valid(raise_exception=True)
        sales_record_serializer.save()
    
    def get(self, request,format=None):
        user=request.user
        print(f"Users is : {user}")
        try:
            if user.user_type=='fpo':
                try:
                    fpo_profile = FPO.objects.get(user=user)
                    print(f"FPO Profile: {fpo_profile}")
                except FPO.DoesNotExist:
                    return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)
                sales=SalesRecordItem.objects.filter(fk_fpo=fpo_profile).order_by('sales_date')
                print(f"SaLES Data: {sales}")
                paginator=GetallInventoryPagination()
                result_page = paginator.paginate_queryset(sales, request)
                sales_serializer=FPOSalesRecordItemSerializer(result_page,many=True)
                return paginator.get_paginated_response({
                        'status': 'success',
                        'inventory': sales_serializer.data,
                    })
            elif user.user_type=='supplier':
                try:
                    supplier_profile = Supplier.objects.get(user=user)
                    print(f"Supplier Profile: {supplier_profile}")
                except Supplier.DoesNotExist:
                    return Response({'error': 'Supplier details not found'}, status=status.HTTP_404_NOT_FOUND)
                sales=SalesRecordItem.objects.filter(fk_supplier=supplier_profile).order_by('sales_date')
                paginator=GetallInventoryPagination()
                result_page = paginator.paginate_queryset(sales, request)
                sales_serializer=SupplierSalesRecordItemSerializer(result_page,many=True)
                return paginator.get_paginated_response({
                        'status': 'success',
                        'inventory': sales_serializer.data,
                    })
            else:
                return Response({'error': 'User type not recognized'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
                error_message = str(e)
                trace = traceback.format_exc()
                return Response({"status": "error","message": "An unexpected error occurred",
                                 "error_message": error_message,"traceback": trace},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
##################------------------------------Inventory In Stock FPO/Supplier---------------#####################
class InventoryInoutStock(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,format=None):
        user=request.user
        print(f"Users is :{user}")
        try:
            if user.user_type=='fpo':
                filter_type=request.query_params.get('filter_type')
                status=request.query_params.get('status')
                if not filter_type and not status:
                    return Response({'error': 'Filter type and status must be provided'}, status=400)
                try:
                    fpo_profile = FPO.objects.get(user=user)
                    print(f"FPO Profile: {fpo_profile}")
                except FPO.DoesNotExist:
                    return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)
                if status=="instock":
                    in_stock_filter = InventoryDetails.objects.filter(stock__gte=10, fk_fpo=fpo_profile, fk_product__selling_status=filter_type)
                    print(f"Instock Data: {in_stock_filter}")
                    instockls = format_inventory_details(in_stock_filter)
                    totalintsock = in_stock_filter.count()
                    return Response({"message": "Inventory In Stock fetched successfully", "inventory": instockls, "total_inventory": totalintsock}, status=200)
                elif status=="outstock":
                    out_stock_filter = InventoryDetails.objects.filter(stock=0, fk_fpo=fpo_profile)
                    outtockls = format_inventory_details(out_stock_filter)
                    totaloutsock = out_stock_filter.count()
                    return Response({"message": "Inventory Out Stock fetched successfully", "inventory": outtockls, "total_inventory": totaloutsock}, status=200)
                else:
                    return Response({'error': 'Invalid status provided'}, status=400)
            elif user.user_type=='supplier':
                filter_type=request.query_params.get('filter_type')
                status=request.query_params.get('status')
                if not filter_type and not status:
                    return Response({'error': 'Filter type and status must be provided'}, status=400)
                try:
                    supplier_profile = Supplier.objects.get(user=user)
                    print(f"Supplier Profile: {supplier_profile}")
                except Supplier.DoesNotExist:
                    return Response({'error': 'Supplier details not found'}, status=status.HTTP_404_NOT_FOUND)
                if status=="instock":
                    in_stock_filter = InventoryDetails.objects.filter(stock__gte=10, fk_supplier=supplier_profile, fk_product__selling_status=filter_type)
                    instockls = format_inventory_details(in_stock_filter)
                    totalintsock = in_stock_filter.count()
                    return Response({"message": "Inventory In Stock fetched successfully", "inventory": instockls, "total_inventory": totalintsock},
                                     status=status.HTTP_200_OK)
                elif status=="outstock":
                    out_stock_filter = InventoryDetails.objects.filter(stock=0, fk_supplier=supplier_profile)
                    outtockls = format_inventory_details(out_stock_filter)
                    totaloutsock = out_stock_filter.count()
                    return Response({"message": "Inventory Out Stock fetched successfully", "inventory": outtockls, "total_inventory": totaloutsock},
                                     status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Invalid status provided'}, status=400)
            else:
                return Response({'error': 'User type not recognized'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
                error_message = str(e)
                trace = traceback.format_exc()
                return Response({"status": "error","message": "An unexpected error occurred",
                                 "error_message": error_message,"traceback": trace},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#####################--------------------------Monthly Sales------------------------########################
class MonthlySales(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        user=request.user
        print(f"Users is :{user}")
        try:
            filter_type =request.query_params.get('filter_type')
            if not filter_type:
                return Response({'error': 'Filter type must be provided'}, status=400)
            if user.user_type == 'fpo':
                try:
                    fpo_profile=FPO.objects.get(user=user)
                    print(f"FPO Profile: {fpo_profile}")
                except FPO.DoesNotExist:
                    return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)
                sales = SalesRecordItem.objects.filter(fk_fpo=fpo_profile,fk_productype_id=filter_type)
                sales_serializer=MonthlySalesSerializer(sales,many=True)
                return Response(sales_serializer.data, status=status.HTTP_200_OK)
            elif user.user_type =='supplier':
                try:
                    supplier_profile=Supplier.objects.get(user=user)
                    print(f"Supplier Profile: {supplier_profile}")
                except Supplier.DoesNotExist:
                    return Response({'error': 'Supplier details not found'}, status=status.HTTP_404_NOT_FOUND)
                sales = SalesRecordItem.objects.filter(fk_supplier=supplier_profile,fk_productype_id=filter_type)
                sales_serializer=MonthlySalesSerializer(sales,many=True)
                return Response(sales_serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'User type not recognized'}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
                error_message = str(e)
                trace = traceback.format_exc()
                return Response({"status": "error","message": "An unexpected error occurred",
                                 "error_message": error_message,"traceback": trace},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
###################---------------------------Total Sales FPO n Suppliers---------------------###############################
class TotalSales(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,format=None):
        user=request.user
        print(f"User is:{user}")
        try:
            filter_type =request.query_params.get('filter_type')
            sales_status=request.query_params.get('sales_status')
            if user.user_type=='fpo':
                try:
                    fpo_profile=FPO.objects.get(user=user)
                except FPO.DoesNotExist:
                    return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)
                sales = SalesRecordItem.objects.filter(fk_fpo=fpo_profile,fk_productype_id=filter_type)
                print(f"Sales: {sales}")
                sales_count = sales.count()
                print(f"Sales: {sales_count}")
                total_sales_amount = sales.aggregate(total=models.Sum('total_amount'))['total'] or 0
                total_profit = 0
                for sale in sales:
                    try:
                        product_price = ProductPrices.objects.filter(
                        fk_fpo=fpo_profile,
                        fk_product__fk_productype_id=filter_type,
                        fk_product__selling_status=sales_status
                    )
                        print(f"Product price:{product_price}")
                        for i in product_price:
                            print(f"Final Price Unit:{i.final_price_unit}")
                            print(f"Unit Price Unit:{i.unit_price}")
                            profit_per_unit = i.final_price_unit - i.unit_price
                            total_profit += profit_per_unit * sale.quantity
                    except ProductPrices.DoesNotExist:
                        continue
                return Response({'sales_count': sales_count,
                'total_sales_amount': round(total_sales_amount),
                'total_profit': round(total_profit)},status=status.HTTP_200_OK)
            elif user.user_type=='supplier':
                try:
                    supplier_profile=Supplier.objects.get(user=user)
                except Supplier.DoesNotExist:
                    return Response({'error': 'Supplier details not found'}, status=status.HTTP_404_NOT_FOUND)
                sales = SalesRecordItem.objects.filter(fk_supplier=supplier_profile, category=filter_type)
                print(f"Sales: {sales}")
                sales_count = sales.count()
                print(f"Sales: {sales_count}")
                total_sales_amount = sales.aggregate(total=models.Sum('total_amount'))['total'] or 0
                total_profit = 0
                for sale in sales:
                    try:
                        product_price = ProductPrices.objects.filter(
                        fk_supplier=supplier_profile,
                        fk_product__fk_productype__product_type=filter_type,
                        fk_product__selling_status=sales_status)
                    except ProductPrices.DoesNotExist:
                        continue
                return Response({'sales_count': sales_count,
                'total_sales_amount': round(total_sales_amount),
                'total_profit': round(total_profit)},status=status.HTTP_200_OK)
            else:
                return Response({'error': 'User type not recognized'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
                error_message = str(e)
                trace = traceback.format_exc()
                return Response({"status": "error","message": "An unexpected error occurred",
                                 "error_message": error_message,"traceback": trace},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
####################---------------------------Check Cutsomer is Farmer or not-------------------################
class CheckCustomerisFarmerornot(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,format=None):
        user=request.user
        print(f"User is {user}")
        try:
            mobile_no=request.query_params.get('mobile_no')
            if user.user_type=='fpo':
                try:
                    fpo_profile = FPO.objects.get(user=user)
                    print(f"FPO Profile: {fpo_profile}")
                except FPO.DoesNotExist:
                    return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)
                try:
                    farmer_status=FarmerProfile.objects.get(mobile=mobile_no,fpo_name=fpo_profile).exists()
                    return Response({'message': 'Farmer mobile number is associated with the FPO', 'associated': True},
                                status=status.HTTP_200_OK)
                except FarmerProfile.DoesNotExist:
                    return Response({'message': 'Farmer mobile number is not associated with the FPO', 'associated': False},
                                     status=status.HTTP_200_OK)
            else:
                return Response({'error': 'User type not recognized'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
                error_message = str(e)
                trace = traceback.format_exc()
                return Response({"status": "error","message": "An unexpected error occurred",
                                 "error_message": error_message,"traceback": trace},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
###################-------------------------Homepage--Check Buyer is Farmer or Not when Sales is Done-----------############
class CheckBuyerisFarmerorNot(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,format=None):
        user=request.user
        print(f"User is {user}")
        try:
            filter_type=request.query_params.get('filter_type')
            if not filter_type:
                return Response({'error': 'Filter type must be provided'}, status=400)
            if user.user_type=='fpo':
                try:
                    fpo_profile = FPO.objects.get(user=user)
                    print(f"FPO Profile: {fpo_profile}")
                except FPO.DoesNotExist:
                    return Response({'error': 'FPO details not found'}, status=status.HTTP_404_NOT_FOUND)
                unique_customers = {}

                if filter_type == "active":
                    farmers = FarmerProfile.objects.filter(fpo_name=fpo_profile)
                    print(f"Farmer Object:{farmers}")
                    mobile_numbers = farmers.values_list('mobile', flat=True)
                    print(f"Farmer Mobile No:{mobile_numbers}")
                    customers = CustomerDetails.objects.filter(fk_fpo=fpo_profile, mobile_no__in=mobile_numbers).distinct()
                    print(f"Customers Details:{customers}")
                    unique_customers = {(customer['buyer_name'], customer['mobile_no']): customer for customer in customers.values('buyer_name', 'mobile_no')}

                elif filter_type == "all":
                    farmers = FarmerProfile.objects.filter(fpo_name=fpo_profile).distinct()
                    print(f"Farmer Object:{farmers}")
                    unique_customers = {(farmer['name'], farmer['mobile']): {'buyer_name': farmer['name'], 'mobile_no': farmer['mobile']} for farmer in farmers.values('name', 'mobile')}

                elif filter_type == "inactive":
                    farmers = FarmerProfile.objects.filter(fpo_name=fpo_profile)
                    print(f"Farmer Object:{farmers}")
                    mobile_numbers = farmers.values_list('mobile', flat=True)
                    print(f"Farmer Mobile No:{mobile_numbers}")
                    customers = CustomerDetails.objects.filter(fk_fpo=fpo_profile).exclude(mobile_no__in=mobile_numbers).distinct()
                    print(f"Customers Details:{customers}")
                    unique_customers = {(customer['buyer_name'], customer['mobile_no']): customer for customer in customers.values('buyer_name', 'mobile_no')}

                else:
                    return Response({'message': 'Invalid filter_type'}, status=400)

                return Response({'suceess':'ok','farmers': list(unique_customers.values()), 'count': len(unique_customers)}, status=200)

            else:
                return Response({'error': 'User type not recognized'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
                error_message = str(e)
                trace = traceback.format_exc()
                return Response({"status": "error","message": "An unexpected error occurred",
                                 "error_message": error_message,"traceback": trace},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
###############-------------------------------Get ALL CROPS----------------############
class GetallFPOCrops(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        user=request.user
        print(f"User is {user.user_type}")
        try:
            if user.user_type=="fpo":

                try:
                    data = CropMapper.objects.filter(eng_crop__isnull=False, is_deleted=False).select_related('eng_crop')
                except CropMapper.DoesNotExist:
                    return Response({'status': 'error', 'msg': 'No such Data Found'}, status=status.HTTP_404_NOT_FOUND)
                states_serializer=CropMapperSerializer(data,many=True)
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
class GetFPOCropVariety(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        user=request.user
        print(f"User is '{user.user_type}")
        try:
            if user.user_type=="fpo":
                crop_id=request.query_params.get('crop_id')
                variety=CropVariety.objects.filter(fk_crops_id=crop_id,eng_name__isnull=False)
                print(f"Variety is '{variety}")
                vareiety_data=CropVarietySerializer(variety,many=True)
                return Response({'success': 'ok','data': vareiety_data.data}, status=status.HTTP_200_OK)
            else:
                return Response({'message':'Only Farmer can access this data'}, status=403)
        except Exception as e:
            return Response({'error': 'An error occurred.', 'details': str(e), 'traceback': traceback.format_exc()}, status=500)
        
#################################-----------------------GOvt Schemes-----------------##########
class GetallFPOGovtSchemes(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        user=request.user
        print(f"User is {user.user_type}")
        try:
            filter_type = request.query_params.get('filter_type', 'all')
            user_language = request.query_params.get('language','1')
            if not filter_type:
                return Response({'status': 'error','message': 'Filter type is required'}, status=status.HTTP_400_BAD_REQUEST)
            if user.user_type=="fpo":
                try:
                    farmer_profile=FPO.objects.get(user=user)
                    print(f"FPO :{farmer_profile}")
                except FarmerProfile.DoesNotExist:
                    return Response({'status': 'error','message': 'FPO not found for this user'}, status=status.HTTP_404_NOT_FOUND)
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
                return Response({'status': 'error','message': 'Only fPO can view government schemes'}, status=status.HTTP_403_FORBIDDEN)
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
class FPOGovtSchemesbyID(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        user=request.user
        print(f"User is {user.user_type}")
        try:
            govt_id =request.query_params.get ('govt_id')
            user_language = request.query_params.get('language','1')
            
            if not govt_id:
                return Response({'message': 'govt_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            if user.user_type=="fpo":
                try:
                    farmer_profile=FPO.objects.get(user=user)
                    print(f"Farmer profile :{farmer_profile}")
                except FPO.DoesNotExist:
                    return Response({'status': 'error','message': 'Fpo not found for this user'}, status=status.HTTP_404_NOT_FOUND)
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