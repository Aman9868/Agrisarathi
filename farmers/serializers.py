##serialziers.py
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from fponsuppliers.models import *
from .models import *
from rest_framework.pagination import LimitOffsetPagination

######################----------------------------------------Farmer Serialzier--------------------------###########
class FarmerRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['mobile', 'email']

    def __init__(self, *args, **kwargs):
        self.user_type = kwargs.pop('user_type', None)
        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        if self.user_type is None:
            raise ValueError("user_type must be provided")

        user = CustomUser.objects.create_user(
            mobile=validated_data.get('mobile'),
            email=validated_data.get('email'),
            user_type=self.user_type
        )

        if self.user_type == 'farmer':
            FarmerProfile.objects.create(user=user, mobile=user.mobile, email=user.email)
        else:
            raise ValueError("Invalid user type")

        print(f"Created {self.user_type} user: {user}")
        return user
    
#########---------------------------Farmer Profile---------------------###############
class FarmerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmerProfile
        fields = '__all__'
##############################---------------------------Farm land Serializers-----------------########
class FarmerLandAddressSerializer(serializers.ModelSerializer):
    state = serializers.CharField(source='fk_state.state', read_only=True)
    district = serializers.CharField(source='fk_district.district', read_only=True)
    crop = serializers.CharField(source='fk_crops.crop_name', read_only=True)
    crop_images=serializers.SerializerMethodField()
    class Meta:
        model = FarmerLandAddress
        fields = ['id', 'land_area', 'address', 'state', 'district', 'tehsil', 'crop','crop_images']
    def get_crop_images(self, obj):
        crop_images = CropImages.objects.filter(fk_cropmaster=obj.fk_crops)
        return [image.crop_image.url for image in crop_images]
########################----------------------------Crop Type Serializers------------------###########
class POPCropTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = POPTypes
        fields = '__all__'
###############################--------------------------Service Providers Serializer--------------------------------##
class ServiceProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service_Provider
        fields = '__all__'
##############---------------------------------All States Serializer---------------------###########
class StatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = StateMaster
        fields = '__all__'

##############---------------------------------All District Serializer---------------------###########
class DistrictMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DistrictMaster
        fields = '__all__' 
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
    class Meta:
        model = Upload_Disease
        fields = '__all__'

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
    crop_audio = serializers.SerializerMethodField()

    class Meta:
        model = SuggestedCrop
        fields = [
            'fk_crop', 'season', 'description', 'weather_temperature', 'cost_of_cultivation',
            'market_price', 'production', 'fk_language', 'crop_image', 'crop_audio'
        ]

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
    class Meta:
        model = WeatherPopNotification
        fields = '__all__'
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

#####################################-----------------------------SOIL Testing----------------####################
class ShopDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopDetails
        fields = '__all__' 
class SoilChargesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoilCharges
        fields = '__all__'