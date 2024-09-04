from django.contrib import admin
from .models import *
from django.utils.html import format_html
#########################---------------------Languages-----------------------##########
@admin.register(LanguageSelection)
class LangaugeSelectionAdmin(admin.ModelAdmin):
    list_display=('id','language','created_at')

#########################-------------------------State Master--------------------------##################
@admin.register(StateMaster)
class StateMasterAdmin(admin.ModelAdmin):
    list_display = ('id','eng_state', 'hin_state')
#########################----------------------------Distict Master-------------------------#############
@admin.register(DistrictMaster)
class DistrictMasterAdmin(admin.ModelAdmin):
    list_display=('id','getstate','eng_district','hin_district','created_at')
    def getstate(self, obj):
        eng_crop_name = obj.fk_state.eng_state if obj.fk_state and obj.fk_state.eng_state else ""
        hin_crop_name = obj.fk_state.hin_state if obj.fk_state and obj.fk_state.hin_state else ""
        return f"{eng_crop_name} / {hin_crop_name}".strip(" / ")

#########################----------------------Farmers------------------------###################
@admin.register(FarmerProfile)
class FarmerofileAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'mobile', 'getlanguage','display_badgecolor','coins','fpo_name','created_at','updated_at')
    def display_badgecolor(self, obj):
        if obj.badgecolor:
            return format_html('<a href="{}" target="_blank"><img src="{}" width="100px" /></a>',  obj.badgecolor.url,obj.badgecolor.url)
        else:
            return '-'
    display_badgecolor.short_description = 'Badge Color'

    def getlanguage(self,obj):
        return obj.fk_language.language if obj.fk_language else None
    getlanguage.short_description='Language'


    def save_model(self, request, obj, form, change):
        if 'coins' in form.changed_data:
            obj.add_coins(form.cleaned_data['coins'])
        super().save_model(request, obj, form, change)
@admin.register(FarmerLandAddress)
class FarmerLandAddressAdmin(admin.ModelAdmin):
    list_display = ('id','fk_farmer', 'land_area', 'address','get_combined_crop_name','pincode',  'village', 'lat1', 'lat2',
                    'tehsil')
    def get_combined_crop_name(self, obj):
        eng_crop_name = obj.fk_crops.eng_crop.crop_name if obj.fk_crops and obj.fk_crops.eng_crop else ""
        hin_crop_name = obj.fk_crops.hin_crop.crop_name if obj.fk_crops and obj.fk_crops.hin_crop else ""
        return f"{eng_crop_name} / {hin_crop_name}".strip(" / ")
    
    get_combined_crop_name.short_description = 'Crop Name'
#############------------------------------------------Fertilizers Admin---------------------------####################
@admin.register(Fertilizer)
class FertilizerAdmin(admin.ModelAdmin):
    list_display = ('fk_language', 'nitrogen', 'phosphorus', 'potassium', 'zincsulphate', 'measurement_type')
    list_filter = ('measurement_type',)
    def get_state(self,obj):
        return obj.fk_state.state if obj.fk_state else None
    get_state.short_description='State'
################---------------------------------------Service Providers----------------------------###################################
@admin.register(Service_Provider)
class Service_ProviderAdmin(admin.ModelAdmin):
    list_display = ('id','eng_name','hin_name', 'display_service', 'paid_or_free')
    def display_service(self, obj):

        if obj.service_provider_pic:
            return format_html('<a href="{}" target="_blank"><img src="{}" width="100px" /></a>', obj.service_provider_pic.url, obj.service_provider_pic.url)
        else:
            return '-'
    display_service.short_description = 'Service Provider'
    def getlanguage(self,obj):
        return obj.fk_language.language if obj.fk_language else None
    getlanguage.short_description='Language'
#########################----------------------------------Disease Section Admin-----------------------------------##################
@admin.register(DiseaseMaster)
class DiseaseMasterAdmin(admin.ModelAdmin):
    list_display = ('id','name','symptom','treatmentbefore','treatmentfield','getlanguage','get_combined_crop_name')
    list_filter=('fk_crops','fk_language')
    def getlanguage(self,obj):
        return obj.fk_language.language if obj.fk_language else None
    getlanguage.short_description='Language'

    def get_combined_crop_name(self, obj):
        eng_crop_name = obj.fk_crops.eng_crop.crop_name if obj.fk_crops and obj.fk_crops.eng_crop else ""
        hin_crop_name = obj.fk_crops.hin_crop.crop_name if obj.fk_crops and obj.fk_crops.hin_crop else ""
        return f"{eng_crop_name} / {hin_crop_name}".strip(" / ")

@admin.register(Disease_Images_Master)
class Disease_Images_MasterAdmin(admin.ModelAdmin):
    list_display = ('id','get_fk_disease', 'disease_file')
    
    def get_fk_disease(self, obj):
        return ", ".join([disease.name for disease in obj.fk_disease.all()])
    get_fk_disease.short_description = 'Diseases'

@admin.register(DiseaseTranslation)
class DiseaseTranslationAdmin(admin.ModelAdmin):
    list_display=('id','getdisease_name','getlanguage','translation','get_combined_crop_name')
    def getlanguage(self,obj):
        return obj.fk_language.language if obj.fk_language else None
    getlanguage.short_description='Language'

    def getdisease_name(self,obj):
        return obj.fk_disease.name if obj.fk_disease else None
    def get_combined_crop_name(self, obj):
        eng_crop_name = obj.fk_crops.eng_crop.crop_name if obj.fk_crops and obj.fk_crops.eng_crop else ""
        hin_crop_name = obj.fk_crops.hin_crop.crop_name if obj.fk_crops and obj.fk_crops.hin_crop else ""
        return f"{eng_crop_name} / {hin_crop_name}".strip(" / ")
    
################-----------------------------------------------Disease Video------------------------#############
@admin.register(DiseaseVideo)
class DiseaseVideoAdmin(admin.ModelAdmin):
    list_display=('fk_language','video')
    
################-----------------------------------------Govt Schemes-------------------######################
@admin.register(GovtSchemes)
class GovtSchemesAdmin(admin.ModelAdmin):
    list_display = ('scheme_name','scheme_by','getlanguage','display_links','display_image')
    def getlanguage(self,obj):
        return obj.fk_language.language if obj.fk_language else None
    getlanguage.short_description='Language'

    def getstate(self,obj):
        return obj.fk_state.state if obj.fk_state else None
    getstate.short_description='State'

    def display_links(self, obj):
        if obj.reference:
            links = obj.reference.split('\n')
            return '\n'.join(links)
        return ""
    def display_image(self, obj):
        if obj.scheme_image:
            return format_html('<a href="{}" target="_blank"><img src="{}" width="100px" /></a>', obj.scheme_image.url, obj.scheme_image.url)
        else:
            return '-'
    display_image.short_description = 'Image'

#####################################----------------------------CROP & Seasons---------------#####################
@admin.register(SeasonMaster)
class SeasonMasterAdmin(admin.ModelAdmin):
    list_display = ('id','season','getlanguage')
    def getlanguage(self,obj):
        return obj.fk_language.language if obj.fk_language else None
    getlanguage.short_description='Language'

@admin.register(POPTypes)
class CropTypeMasterAdmin(admin.ModelAdmin):
    list_display = ('id','get_season', 'name','getlanguage')
    def get_season(self, obj):
        return obj.fk_season.season if obj.fk_season else None
    get_season.short_description = 'Season'
    get_season.admin_order_field = 'fk_season__season'
    def getlanguage(self,obj):
        return obj.fk_language.language if obj.fk_language else None
    getlanguage.short_description='Language'

@admin.register(CropMaster)
class CropMasterAdmin(admin.ModelAdmin):
    list_display = ('id','get_crop_type', 'crop_name','getlanguage')
    list_filter=('fk_language',)

    def get_crop_type(self, obj):
        return obj.fk_crop_type.name if obj.fk_crop_type else None
    get_crop_type.short_description = 'Crop Type'
    get_crop_type.admin_order_field = 'fk_crop_type__type'

    def getlanguage(self,obj):
        return obj.fk_language.language if obj.fk_language else None
    getlanguage.short_description='Language'


@admin.register(CropImages)
class CropImagesAdmin(admin.ModelAdmin):
    list_display=('id','get_combined_crop_name','crop_image')
    def get_combined_crop_name(self, obj):
        eng_crop_name = obj.fk_cropmaster.eng_crop.crop_name if obj.fk_cropmaster and obj.fk_cropmaster.eng_crop else ""
        hin_crop_name = obj.fk_cropmaster.hin_crop.crop_name if obj.fk_cropmaster and obj.fk_cropmaster.hin_crop else ""
        return f"{eng_crop_name} / {hin_crop_name}".strip(" / ")
    
    get_combined_crop_name.short_description = 'Crop Name'

###########################################----------------------Crop Variety---------------------------------------#################
@admin.register(CropVariety)
class CropVarietyAdmin(admin.ModelAdmin):
    list_display=('id','get_combined_crop_name','eng_name','hin_name')
    def get_combined_crop_name(self, obj):
        eng_crop_name = obj.fk_crops.eng_crop.crop_name if obj.fk_crops and obj.fk_crops.eng_crop else ""
        hin_crop_name = obj.fk_crops.hin_crop.crop_name if obj.fk_crops and obj.fk_crops.hin_crop else ""
        return f"{eng_crop_name} / {hin_crop_name}".strip(" / ")
#############--------------------------------------------Community Section---------------------##################### 
@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ('get_user_name','display_fponame', 'description', 'created_at')

    def get_user_name(self, obj):
        return obj.fk_user.name if obj.fk_user else None
    get_user_name.short_description = 'Posted by Farmer'
    get_user_name.admin_order_field = 'fk_user__name'
    def display_fponame(self,obj):
        return obj.fk_fpo.fpo_name if obj.fk_fpo else None
    display_fponame.short_description ="Posted By FPO"
    def get_crop_name(self, obj):
        return obj.fk_crop.crop_name if obj.fk_crop else None
    get_crop_name.short_description = 'Crop Name'
    get_crop_name.admin_order_field = 'fk_crop__crop_name'

@admin.register(PostsMedia)
class PostsMediaAdmin(admin.ModelAdmin):
    list_display = ('fk_post', 'video_file', 'image_file')

@admin.register(PostComments)
class PostCommentsAdmin(admin.ModelAdmin):
    list_display = ('fk_post', 'get_user_name','display_fponame','text', 'created_at')
    def get_user_name(self, obj):
        return obj.fk_user.name if obj.fk_user else None
    get_user_name.short_description = 'Commented by Farmer'
    get_user_name.admin_order_field = 'fk_user__name'
    def display_fponame(self,obj):
        return obj.fk_fpo.fpo_name if obj.fk_fpo else None
    display_fponame.short_description ="Commented By FPO"

@admin.register(CommentReply)
class CommentReplyAdmin(admin.ModelAdmin):
    list_display = ('display_postcomment', 'displayfarmer_name','display_fponame','text', 'created_at')

    def display_postcomment(self,obj):
        return obj.fk_postcomment.text if obj.fk_postcomment else None
    display_postcomment.short_description = "Comment"

    def displayfarmer_name(self,obj):
        return obj.fk_user.name if obj.fk_user else None
    displayfarmer_name.short_description = "Reply by Farmer"

    def display_fponame(self,obj):
        return obj.fk_fpo.fpo_name if obj.fk_fpo else None
    display_fponame.short_description ="Reply By FPO"
    

@admin.register(PostsLike)
class PostsLikeAdmin(admin.ModelAdmin):
    list_display = ('fk_post', 'fk_user','fk_fpo','like_count', 'created_at')
    def display_post(self,obj):
        return obj.fk_post.description if obj.fk_post else None
    
#######################--------------------------------------Upload Diseasees--------------------------#################
@admin.register(Upload_Disease)
class Uploaded_DiseaseAdmin(admin.ModelAdmin):
    list_display = ('id','get_service_provider','get_disease_name','get_user','fk_language','get_combined_crop_name'
                    )

    def get_user(self, obj):
        return obj.fk_user.id if obj.fk_user else None
    get_user.short_description = 'User'

    def get_service_provider(self, obj):
        eng_name = obj.fk_provider.eng_name if obj.fk_provider and obj.fk_provider.eng_name else ""
        hin_name = obj.fk_provider.hin_name if obj.fk_provider and obj.fk_provider.hin_name else ""
        return f"{eng_name} / {hin_name}".strip(" / ")



    def get_combined_crop_name(self, obj):
        eng_crop_name = obj.fk_crop.eng_crop.crop_name if obj.fk_crop and obj.fk_crop.eng_crop else ""
        hin_crop_name = obj.fk_crop.hin_crop.crop_name if obj.fk_crop and obj.fk_crop.hin_crop else ""
        return f"{eng_crop_name} / {hin_crop_name}".strip(" / ")

    def get_disease_name(self, obj):

        return obj.fk_disease.name if obj.fk_disease else None
    get_disease_name.short_description = 'Disease Name'
    get_disease_name.admin_order_field = 'fk_disease__name'
######################----------------------------------Soil Tseting------------------############################
@admin.register(SoilCharges)
class SoilAdminCharges(admin.ModelAdmin):
    list_display = ('id', 'price', 'plans','fk_shop')
    def get_service_provider(self, obj):
        return obj.fk_providername.name if obj.fk_providername else None
    get_service_provider.short_description = 'Service Provider'
    get_service_provider.admin_order_field = 'fk_provider__name'



##################################----------------------Spices POP------------------------##################
@admin.register(SpicesPop)
class SpicesPopAdmin(admin.ModelAdmin):
    list_display = ('stages','description','stage_number','getcrop_type', 'get_crop_name','getlanguage','preference')
    list_filter = ('stages','fk_language')
    search_fields = ('stages', 'description')
    def get_crop_name(self, obj):
        return obj.fk_crop.crop_name if obj.fk_crop else None
    get_crop_name.short_description = 'Crop Name'

    def getlanguage(self,obj):
        return obj.fk_language.language if obj.fk_language else None
    getlanguage.short_description='Language'

    def getcrop_type(self,obj):
        return obj.fk_croptype.name if obj.fk_croptype else None

##################-----------------------

@admin.register(SpicestageCompletion)
class SpicestageCompletionAdmin(admin.ModelAdmin):
    list_display = ('spice_pop', 'stage_number', 'fk_farmer', 'completion_date', 'total_days_spent', 'delay_days')
#################################-------------------------Prefrence Completion------------------###################
@admin.register(SpicesPreferenceCompletion)
class SpicesPreferenceCompletionAdmin(admin.ModelAdmin):
    list_display = ('fk_farmer', 'fk_crop', 'preference_number', 'start_date', 'completion_date', 'total_days', 'is_completed')

#################################------------------------------Fruits POP-----------------------------####################
@admin.register(FruitsPop)
class FruitsPopAdmin(admin.ModelAdmin):
    list_display = ['id','stages','stage_name', 'stage_number', 'start_period', 'end_period', 'orchidtype',
                    'getlanguage','getcrop_name']
    def getcrop_name(self,obj):
        return obj.fk_crops.crop_name if obj.fk_crops else None
    getcrop_name.short_description = 'Crop Name'

    def getlanguage(self,obj):
        return obj.fk_language.language if obj.fk_language else None
    getlanguage.short_description='Language'


@admin.register(FruitsStageCompletion)
class FruitsStageComplete(admin.ModelAdmin):
    list_display=('fk_fruits','fk_farmer','fk_farmland','start_date','completion_date','days_completed','delay_count')


##################----------------------------------Vegetable POP-----------------------############
@admin.register(VegetablePop)
class VegetablePopAdmin(admin.ModelAdmin):
    list_display = ('stages','description','stage_number', 'get_combined_crop_name','fk_croptype','audio','preference','video')
    list_filter = ('stages','fk_language','fk_crop')
    search_fields = ('stages', 'description')
    def get_combined_crop_name(self, obj):
        eng_crop_name = obj.fk_crop.eng_crop.crop_name if obj.fk_crop and obj.fk_crop.eng_crop else ""
        hin_crop_name = obj.fk_crop.hin_crop.crop_name if obj.fk_crop and obj.fk_crop.hin_crop else ""
        return f"{eng_crop_name} / {hin_crop_name}".strip(" / ")

    def getlanguage(self,obj):
        return obj.fk_language.language if obj.fk_language else None
    getlanguage.short_description='Language'

@admin.register(VegetableStageCompletion)
class VegtableStageCompletionAdmin(admin.ModelAdmin):
    list_display = ('id','vegetable_pop', 'stage_number', 'fk_farmer', 'completion_date', 'total_days_spent','getlanguage')
    def getlanguage(self,obj):
        return obj.fk_language.language if obj.fk_language else None
    getlanguage.short_description='Language'
@admin.register(VegetablePreferenceCompletion)
class VegetablePreferenceCompletionAdmin(admin.ModelAdmin):
    list_display = ('id','fk_farmer', 'get_combined_crop_name', 'preference_number', 'start_date', 'completion_date', 'total_days', 'is_completed','getlanguage')
    def getlanguage(self,obj):
        return obj.fk_language.language if obj.fk_language else None
    getlanguage.short_description='Language'

    def get_combined_crop_name(self, obj):
        eng_crop_name = obj.fk_crop.eng_crop.crop_name if obj.fk_crop and obj.fk_crop.eng_crop else ""
        hin_crop_name = obj.fk_crop.hin_crop.crop_name if obj.fk_crop and obj.fk_crop.hin_crop else ""
        return f"{eng_crop_name} / {hin_crop_name}".strip(" / ")

##################----------------------------------CEREAL POP-----------------------############
@admin.register(CerealsPop)
class CerealsPopAdmin(admin.ModelAdmin):
    list_display = ('stages','description','stage_number', 'get_crop_name','audio','preference','video')
    list_filter = ('stages','fk_language','fk_crop')
    search_fields = ('stages', 'description')
    def get_crop_name(self, obj):
        return obj.fk_crop.crop_name if obj.fk_crop else None
    get_crop_name.short_description = 'Crop Name'

    def getlanguage(self,obj):
        return obj.fk_language.language if obj.fk_language else None
    getlanguage.short_description='Language'

@admin.register(CerealStageCompletion)
class CerealStageCompletionAdmin(admin.ModelAdmin):
    list_display = ('cereal_pop', 'stage_number', 'fk_farmer', 'completion_date', 'total_days_spent', 'delay_days')

@admin.register(CerealPreferenceCompletion)
class CerealPreferenceCompletionAdmin(admin.ModelAdmin):
    list_display = ('fk_farmer', 'fk_crop', 'preference_number', 'start_date', 'completion_date', 'total_days', 'is_completed')

################################-----------------------------POP Notifcation---------------------------#############
@admin.register(PopWeatherCondition)
class PopWeatherConditionAdmin(admin.ModelAdmin):
    list_display=('id','condition')

@admin.register(WeatherPopNotification)
class WeatherPopNotificationAdmin(admin.ModelAdmin):
    list_display=('stages','get_combined_crop_name','notification_text','getlanguage','gif')
    list_filter=('fk_crops',)
    def get_combined_crop_name(self, obj):
        eng_crop_name = obj.fk_crops.eng_crop.crop_name if obj.fk_crops and obj.fk_crops.eng_crop else ""
        hin_crop_name = obj.fk_crops.hin_crop.crop_name if obj.fk_crops and obj.fk_crops.hin_crop else ""
        return f"{eng_crop_name} / {hin_crop_name}".strip(" / ")

    def getlanguage(self,obj):
        return obj.fk_language.language if obj.fk_language else None
    getlanguage.short_description='Language'

################################------------------------------Crop Suggestion----------------#####################
@admin.register(SuggestedCrop)
class SuggestedCropAdmin(admin.ModelAdmin):
    list_display = ('season', 'start_month', 'end_month', 'weather_temperature', 'cost_of_cultivation', 'market_price', 'production', 'get_combined_crop_name', 'fk_language')
    def get_combined_crop_name(self, obj):
        eng_crop_name = obj.fk_crop.eng_crop.crop_name if obj.fk_crop and obj.fk_crop.eng_crop else ""
        hin_crop_name = obj.fk_crop.hin_crop.crop_name if obj.fk_crop and obj.fk_crop.hin_crop else ""
        return f"{eng_crop_name} / {hin_crop_name}".strip(" / ")

######################------------------------------OTP Verification-------------- #####################
@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'mobile', 'otp', 'created_at')

###############################--------------------------------------Disease Section-------------######################
@admin.register(DiseaseProductInfo)
class DiseaseProductInfoAdmin(admin.ModelAdmin):
    list_display = ('id','getdis_name','get_combined_crop_name')
    search_fields = ('fk_disease__name', 'fk_product__productName') 
    #list_filter = ('fk_crop', 'fk_disease', 'fk_product')
    def get_combined_crop_name(self, obj):
        eng_crop_name = obj.fk_crop.eng_crop.crop_name if obj.fk_crop and obj.fk_crop.eng_crop else ""
        hin_crop_name = obj.fk_crop.hin_crop.crop_name if obj.fk_crop and obj.fk_crop.hin_crop else ""
        return f"{eng_crop_name} / {hin_crop_name}".strip(" / ")

    def getdis_name(self,obj):
        return obj.fk_disease.name if obj.fk_disease else None
    getdis_name.short_description = 'Disease Name'

    def getproduct_name(self,obj):
        return obj.fk_product.productName if obj.fk_product else None
    getproduct_name.short_description = 'Product Name'

##############################-------------------------NEWS-----------------------------#############
@admin.register(CurrentNews)
class CurrentNewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'getlanguage')
    list_filter = ('fk_language', 'created_at','source')
    def getlanguage(self,obj):
        return obj.fk_language.language if obj.fk_language else None
    getlanguage.short_description='Language'

########################----------------------------Crop Mapper---------------------------#################
@admin.register(CropMapper)
class CropMapperAdmin(admin.ModelAdmin):
    list_display = ('id', 'geteng_crop_name','gethin_crop_name')

    def geteng_crop_name(self,obj):
        return obj.eng_crop.crop_name if obj.eng_crop else None
    geteng_crop_name.short_description = 'English Crop'


    def gethin_crop_name(self,obj):
        return obj.hin_crop.crop_name if obj.hin_crop else None
    gethin_crop_name.short_description = 'Hindi Crop'

    def gethin_pop_name(self,obj):
        return obj.hin_pop.name if obj.hin_pop else None
    gethin_pop_name.short_description = 'Hindi Pop'

#######################################---------- Season Mapper-----------------------###################
@admin.register(SeasonMapper)
class SeasonMapperAdmin(admin.ModelAdmin):
    list_display = ('id', 'geteng_season_name', 'gethin_season_name', 'created_at', 'updated_at', 'is_deleted')

    def geteng_season_name(self,obj):
        return obj.eng_season.season if obj.eng_season else None
    geteng_season_name.short_description = 'English Season'

    def gethin_season_name(self,obj):
        return obj.hin_season.season if obj.hin_season else None
    gethin_season_name.short_description = 'Hindi Season'

##############################-----------------POP Mapper-----------------------------#################
@admin.register(POPMapper)
class PopMapperAdmin(admin.ModelAdmin):
    list_display = ('id', 'geteng_pop_name','gethin_pop_name','get_combined_season_name')

    def geteng_pop_name(self,obj):
        return obj.eng_pop.name if obj.eng_pop else None
    geteng_pop_name.short_description = 'English Pop'

    def gethin_pop_name(self,obj):
        return obj.hin_pop.name if obj.hin_pop else None
    gethin_pop_name.short_description = 'Hindi Pop'

    def get_combined_season_name(self, obj):
        if obj.season_map:
            eng_season_name = obj.season_map.eng_season.season if obj.season_map.eng_season else None
            hin_season_name = obj.season_map.hin_season.season if obj.season_map.hin_season else None
            return f"{eng_season_name} / {hin_season_name}"
        return None
    get_combined_season_name.short_description = 'Combined Season Name'


    