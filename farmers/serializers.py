##serialziers.py
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from fponsuppliers.models import *
from .models import *
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.pagination import PageNumberPagination
from django.db import transaction

######################----------------------------------------Farmer Serialzier--------------------------###########
class FarmerRegistrationSerializer(serializers.ModelSerializer):
    user_language = serializers.IntegerField(write_only=True)
    class Meta:
        model = CustomUser
        fields = ['mobile', 'email','user_language']

    def __init__(self, *args, **kwargs):
        self.user_type = kwargs.pop('user_type', None)
        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        if self.user_type is None:
            raise ValueError("user_type must be provided")
        user_language = validated_data.pop('user_language')

        user = CustomUser.objects.create_user(
            mobile=validated_data.get('mobile'),
            email=validated_data.get('email'),
            user_type=self.user_type
        )

        if self.user_type == 'farmer':
            FarmerProfile.objects.create(user=user, mobile=user.mobile, email=user.email,fk_language_id=user_language)
        else:
            raise ValueError("Invalid user type")

        print(f"Created {self.user_type} user: {user} with language: {user_language}")
        return user
    
#########---------------------------Farmer Profile---------------------###############
class FarmerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmerProfile
        fields = '__all__'
##############################---------------------------Farm land Serializers-----------------########
class FarmerLandAddressSerializer(serializers.ModelSerializer):
    state = serializers.CharField(source='fk_state.state', read_only=True)
    crop_id = serializers.IntegerField(source='fk_crops.id', read_only=True)
    filter_id = serializers.IntegerField(source='fk_croptype.id', read_only=True)
    district = serializers.SerializerMethodField()
    eng_district=serializers.CharField(source='fk_district.eng_district', read_only=True)
    crop = serializers.SerializerMethodField()
    state= serializers.SerializerMethodField()
    crop_images=serializers.SerializerMethodField()
    preference = serializers.SerializerMethodField()
    class Meta:
        model = FarmerLandAddress
        fields = ['id', 'land_area', 'address', 'state', 'district', 'tehsil', 'crop','crop_images','crop_id','filter_id',
                  'eng_district','preference']
    def get_crop_images(self, obj):
        crop_images = CropImages.objects.filter(fk_cropmaster=obj.fk_crops)
        return [image.crop_image.url for image in crop_images]
    
    def get_crop(self, obj):
        farmer_language = obj.fk_farmer.fk_language.id
        print(f"Farmer language ID: {farmer_language}")
        crop_name = None
        if farmer_language == 1:  
            crop_name = obj.fk_crops.eng_crop.crop_name if obj.fk_crops.eng_crop else None
        elif farmer_language == 2: 
            crop_name = obj.fk_crops.hin_crop.crop_name if obj.fk_crops.hin_crop else None
        
        print(f"Returning crop name: {crop_name}")
        return crop_name
    def get_district(self, obj):
        user_language = obj.fk_farmer.fk_language.id
        if obj.fk_district:
            if user_language == 1: 
                return obj.fk_district.eng_district if obj.fk_district.eng_district else None
            elif user_language == 2:  
                return obj.fk_district.hin_district if obj.fk_district.hin_district else None
        return None
    def get_state(self, obj):
        user_language = obj.fk_farmer.fk_language.id
        if obj.fk_state:
            if user_language == 1: 
                return obj.fk_state.eng_state if obj.fk_state.eng_state else None
            elif user_language == 2:  
                return obj.fk_state.hin_state if obj.fk_state.hin_state else None
        return None
    def get_preference(self, obj):
        user = obj.fk_farmer
        crop_id = obj.fk_crops.id
        filter_type = obj.fk_croptype.id
        user_language = obj.fk_farmer.fk_language.id
        print(f"User is :{user}, CropId is :{crop_id}, FilterType is :{filter_type}, UserLanguage is :{user_language},Land is :{obj}")
        return VegetablePreferenceCompletion.objects.filter(
            fk_farmer=user,
            fk_farmland=obj,
            fk_crop_id=crop_id,
            fk_language_id=user_language,
            fk_croptype_id=filter_type
        ).exists()
########################----------------------------Crop Type Serializers------------------###########
class POPCropTypeSerializer(serializers.ModelSerializer):
    pop_id = serializers.SerializerMethodField()
    pop_name = serializers.SerializerMethodField()
    #season = serializers.SerializerMethodField()
    season_id = serializers.IntegerField(source='season_map.id', read_only=True)
    
    class Meta:
        model = POPMapper
        fields = ['pop_id', 'pop_name','season_id']

    def get_pop_id(self, obj):
        return obj.id

    def get_pop_name(self, obj):
        user_language = self.context.get('user_language')
        if user_language == 1:  # Assuming 1 is English
            return obj.eng_pop.name if obj.eng_pop else None
        elif user_language == 2:  # Assuming 2 is Hindi
            return obj.hin_pop.name if obj.hin_pop else None
        return None

    def get_season(self, obj):
        user_language = self.context.get('user_language')
        if obj.season_map:
            if user_language == 1:  # Assuming 1 is English
                return obj.season_map.eng_season if obj.season_map.eng_season else None
            elif user_language == 2:  # Assuming 2 is Hindi
                return obj.season_map.hin_season if obj.season_map.hin_season else None
        return None
        
##############################--------------------------CROP VARIRTY--------------------###############
class CropVarietySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    class Meta:
        model = CropVariety
        fields = ['id', 'name']

    def get_name(self, obj):
        user_language = self.context.get('user_language')
        if user_language == 1:  
            return obj.eng_name
        elif user_language == 2: 
            return obj.hin_name
        else:
            return None
###############################--------------------------Service Providers Serializer--------------------------------##
class ServiceProviderSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Service_Provider
        fields = ['id','name', 'service_provider_pic', 'paid_or_free']

    def get_name(self, obj):
        user_language = self.context.get('user_language')
        if user_language == 1:  
            return obj.eng_name
        elif user_language == 2:  
            return obj.hin_name
        return None
##############---------------------------------All States Serializer---------------------###########
class StatesSerializer(serializers.ModelSerializer):
    state_name = serializers.SerializerMethodField()
    class Meta:
        model = StateMaster
        fields = ['id', 'state_name']
    def get_state_name(self, obj):
        user_language = self.context.get('user_language')
        if user_language == 1:  
            return obj.eng_state
        elif user_language == 2: 
            return obj.hin_state
        else:
            return None

##############---------------------------------All District Serializer---------------------###########
class DistrictMasterSerializer(serializers.ModelSerializer):
    district_name = serializers.SerializerMethodField()
    class Meta:
        model = DistrictMaster
        fields = ['id','district_name'] 

    def get_district_name(self, obj):
        user_language = self.context.get('user_language')
        if user_language == 1:  
            return obj.eng_district
        elif user_language == 2: 
            return obj.hin_district
        else:
            return None
######################----------------------------------------Initial Screen Crops--------------------------###########
class CropImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CropImages
        fields = ['crop_image']

class CropMasterSerializer(serializers.ModelSerializer):
    crop_images = serializers.SerializerMethodField()
    season_name = serializers.SerializerMethodField()
    season_id = serializers.SerializerMethodField()
    croptype_id=serializers.SerializerMethodField()

    class Meta:
        model = CropMaster
        fields = ['id', 'crop_name', 'crop_status', 'season_name', 'season_id', 'crop_images','croptype_id']

    def get_crop_images(self, obj):
        images = CropImages.objects.filter(fk_cropmaster=obj).values_list('crop_image', flat=True)
        return [f"media/{image}" for image in images]

    def get_season_name(self, obj):
        return obj.fk_crop_type.fk_season.season if obj.fk_crop_type and obj.fk_crop_type.fk_season else None

    def get_season_id(self, obj):
        return obj.fk_crop_type.fk_season.id if obj.fk_crop_type and obj.fk_crop_type.fk_season else None
    def get_croptype_id(self, obj):
        return obj.fk_crop_type.id if obj.fk_crop_type else None
    
#####################--------------------------------Shop Serializer------------------------#############
class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopDetails
        fields = '__all__'

#####################-----------------------------------Disease Detection------------------------#############
class UploadDiseaseSerializer(serializers.ModelSerializer):
    disease_name=serializers.CharField(source='fk_disease.name', read_only=True)
    serviceprovider=serializers.SerializerMethodField()
    crop_id=serializers.IntegerField(source='fk_crop.id', read_only=True)
    class Meta:
        model = Upload_Disease
        fields = ['id','disease_name','uploaded_image','crop_id','serviceprovider','created_at']
        
    def get_serviceprovider(self, obj):
        user_language = self.context.get('user_language')
        if user_language == 1:  
            return obj.fk_provider.eng_name if obj.fk_provider else None
        elif user_language == 2:  
            return obj.fk_provider.hin_name if obj.fk_provider else None
        return None
    
class UploadDiseaseSerializerMore(serializers.ModelSerializer):
    disease_name=serializers.CharField(source='fk_disease.name', read_only=True)
    symtomps=serializers.CharField(source='fk_disease.symptom', read_only=True)
    treatment_before=serializers.CharField(source='fk_disease.treatmentbefore', read_only=True)
    teratment_field=serializers.CharField(source='fk_disease.treatmentfield', read_only=True)
    crop_id=serializers.IntegerField(source='fk_crop.id', read_only=True)
    treatment=serializers.CharField(source='fk_disease.treatment',read_only=True)
    class Meta:
        model = Upload_Disease
        fields = ['id','disease_name','uploaded_image','crop_id','treatment_before','teratment_field','symtomps',
                  'treatment']

class DiseaseProductInfoSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()

    class Meta:
        model = DiseaseProductInfo
        fields = ['products']

    def get_products(self, obj):
        products = obj.fk_product.all()
        result = []
        for product in products:
            # Retrieve the list of supplier IDs for the product
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
            
            result.append(product_data)
        return result

class DiseaseMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiseaseMaster
        fields = '__all__'

class DiseaseTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiseaseTranslation
        fields = '__all__'

class DiseaseImagesMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disease_Images_Master
        fields = ['disease_file']

class DiseaseVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model=DiseaseVideo
        fields='__all__'
#######################---------------------Govt Schemes Seralizer---------------------################
class GovtSchemesSerializer(serializers.ModelSerializer):
    state = serializers.CharField(source='fk_state.state', default=None)
    class Meta:
        model = GovtSchemes
        fields = ['id', 'scheme_name', 'details', 'benefits', 'elgibility', 'application_process', 'document_require', 
                  'scheme_by', 'ministry_name', 'state', 'applicationform_link', 'reference', 'scheme_image']
        
#################-------------------------News Seializer--------------------##################
class CurrentNewsSerializer(serializers.ModelSerializer):
    language=serializers.CharField(source='fk_language.language', default=None)
    class Meta:
        model = CurrentNews
        fields = ['id', 'title', 'content', 'created_at', 'image', 'related_post', 'source', 'link', 'language']

class CurrentNewsPagination(LimitOffsetPagination):
    default_limit = 20 
    max_limit = 100  


########-----------------------------------------CROP SUGGESTion-----------------------#################
class SuggestedCropSerializer(serializers.ModelSerializer):
    crop_image = serializers.SerializerMethodField()
    crop_name=serializers.SerializerMethodField()
    crop_audio = serializers.SerializerMethodField()

    class Meta:
        model = SuggestedCrop
        fields = [
            'fk_crop', 'season', 'description', 'weather_temperature', 'cost_of_cultivation',
            'market_price', 'production', 'fk_language', 'crop_image', 'crop_audio','crop_name',
        ]
    def get_crop_name(self, obj):
        user_language = self.context.get('user_language')
        print(f"Farmer language ID: {user_language}")
        crop_name = None
        if user_language == 1:  
            crop_name = obj.fk_crop.eng_crop.crop_name if obj.fk_crop.eng_crop else None
        elif user_language == 2: 
            crop_name = obj.fk_crop.hin_crop.crop_name if obj.fk_crop.hin_crop else None
        print(f"Returning crop name: {crop_name}")
        return crop_name

    def get_crop_image(self, obj):
        crop_images = CropImages.objects.filter(fk_cropmaster=obj.fk_crop)
        if crop_images.exists():
            return crop_images.first().crop_image.url
        return None

    def get_crop_audio(self, obj):
        if obj.audio:
            return obj.audio.url
        return None
#############################-------------------------Vegetabel Notifciations---------------------################
class WeatherNotificationSerializer(serializers.ModelSerializer):
    weather_id=serializers.IntegerField(source='id',read_only=True)
    crop_id=serializers.IntegerField(source='fk_crops.id', read_only=True,default=None)
    class Meta:
        model = WeatherPopNotification
        fields = ['weather_id', 'crop_id','stages','gif','preference_number','notification_text']
class VegetablePrefrencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = VegetablePreferenceCompletion
        fields = '__all__'

class SpicesPrefrencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpicesPreferenceCompletion
        fields = '__all__'

class CerealsPrefrencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CerealPreferenceCompletion
        fields = '__all__'
class CropMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CropMaster
        fields = '__all__'
#####################################-----------------------------SOIL Testing----------------####################
class ShopDetailSerializer(serializers.ModelSerializer):
    shop_id=serializers.IntegerField(source='id')
    class Meta:
        model = ShopDetails
        fields = ['shop_id','shopName','shopContactNo','shopaddress','shop_opentime','shop_closetime','shopimage']
class SoilChargesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoilCharges
        fields = '__all__'
        
        
###############################---------------------------Dukan all Shops----------------------#############
class GetallShopPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size'
    max_page_size = 100 