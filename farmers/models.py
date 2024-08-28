##farmermodes.py
from django.db import models
import os
from django.utils import timezone
from fponsuppliers.models import *
#############################-------------------------------------Language Selection--------------------###############
# Create your models here.
class LanguageSelection(models.Model):
    langchoice=[
        ("EN", "EN"),
        ("HI", "HI"),
        ("TE", "TE"),  
        ("TA", "TA"),
        ("MR","MR"),
        ("ML","ML"),
        ("BHO","BHO"),
        ("GU","GU"),
        ("PA","PA"),
        ("BN","BN"),
        ("OR","OR")  ,
        ("AS","AS"),
        ("KN","KN")
        
    ]
    language=models.CharField(max_length=200, choices=langchoice, default='EN')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

###############--------------------------------Service Providers-----------------------------######################    
class Service_Provider(models.Model):
    name =  models.CharField(null=True,blank=True,max_length=100)
    service_provider_pic = models.FileField(upload_to="service_provider/", blank=True, null=True)
    paid_or_free = models.BooleanField(default=False, blank=True, null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)

#####################------------------------------------States--------------------#################
class StateMaster(models.Model):
    state = models.CharField(null=True, blank=True, max_length=100)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
##################################--------------------District---------------------#############
class DistrictMaster(models.Model):
    fk_state = models.ForeignKey(StateMaster, on_delete=models.CASCADE, null=True, blank=True)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    district=models.CharField(null=True, blank=True, max_length=100)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
########################------------------------------------Current News----------------------###################
class CurrentNews(models.Model):
    title=models.CharField(max_length=5000,null=True,blank=True)
    content=models.TextField(null=True,blank=True)
    created_at = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to='article_images/', blank=True, null=True)
    related_post=models.CharField(max_length=100,null=True,blank=True)
    source=models.CharField(max_length=100,null=True,blank=True)
    link = models.CharField(null=True,blank=True,max_length=5000)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)

#####################------------------------------POP Types--------------------------################
class SeasonMaster(models.Model):
    season = models.CharField(null=True , blank=True,max_length=100)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class POPTypes(models.Model):
    name=models.CharField(max_length=100,null=True,blank=True)
    fk_season =models.ForeignKey(SeasonMaster,on_delete=models.CASCADE,null=True,blank=True)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
##############--------------------------CROP Details-----
class CropMaster(models.Model):
    fk_crop_type =models.ForeignKey(POPTypes,on_delete=models.CASCADE,null=True,blank=True)
    crop_name = models.CharField(null=True, blank=True, max_length=100)
    crop_status=models.BooleanField(null=True,blank=True,default="")
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CropImages(models.Model):
    fk_cropmaster = models.ManyToManyField(CropMaster,blank=True)
    crop_image = models.FileField(upload_to="crops/", blank=True, null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

###############-------------------------------Disease Models------------------------##############################
class DiseaseMaster(models.Model):
    name = models.CharField(null=True,blank=True,max_length=100)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    symptom = models.TextField(null=True,blank=True)
    symptom_audio=models.FileField(upload_to="symptom_audio/",blank=True, null=True)
    treatmentbefore = models.TextField(null=True,blank=True)
    treatment_befaudio=models.FileField(upload_to="treatment_bef_audio",blank=True, null=True)
    treatmentfield=models.TextField(null=True,blank=True)
    suggestiveproduct=models.TextField(null=True,blank=True)
    treatment=models.TextField(null=True,blank=True)
    message=models.TextField(null=True,blank=True)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    fk_crops=models.ManyToManyField(CropMaster,blank=True)

class DiseaseTranslation(models.Model):
    fk_disease = models.ForeignKey(DiseaseMaster, on_delete=models.CASCADE,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fk_language = models.ForeignKey(LanguageSelection, on_delete=models.CASCADE,null=True,blank=True)
    fk_crops=models.ForeignKey(CropMaster,on_delete=models.CASCADE,null=True,blank=True)
    translation = models.CharField(max_length=255,null=True,blank=True)

class Disease_Images_Master(models.Model):
    fk_disease = models.ManyToManyField(DiseaseMaster,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    disease_file = models.FileField(upload_to="disease/", blank=True, null=True)

#######################-----------------------------------Disease Video---------------------############
class DiseaseVideo(models.Model):
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    video=models.FileField(upload_to="disease_video/", blank=True, null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

####################################################---------------Crop Variety---------------------#################
class CropVariety(models.Model):
    fk_crops=models.ForeignKey(CropMaster,blank=True,null=True,on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fk_language = models.ForeignKey(LanguageSelection, on_delete=models.CASCADE, null=True, blank=True)
    variety=models.CharField(max_length=100,null=True,blank=True)


##########################----------------------------FARMER Profile-------------------------------###########################
def validate_mobile_no(value):
    if not re.match(r'^\d{10}$', value):
        raise ValidationError("Mobile number must be exactly 10 digits.")
class FarmerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='farmers')
    email = models.EmailField(max_length=255, null=True, blank=True)
    email_verified = models.BooleanField(null=True, blank=True, default=False)
    fk_crops = models.ManyToManyField(CropMaster, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(null=True, blank=True, max_length=100)
    mobile = models.CharField(null=True, blank=True, max_length=10, validators=[validate_mobile_no], unique=True)
    fk_language = models.ForeignKey(LanguageSelection, on_delete=models.CASCADE, null=True, blank=True)
    fpo_name = models.ForeignKey(FPO,on_delete=models.CASCADE, related_name='farmers', null=True, blank=True)
    profile = models.FileField(upload_to="Profile/", blank=True, null=True)
    village = models.CharField(null=True, blank=True, max_length=100)
    district = models.CharField(null=True, blank=True, max_length=100)
    block=models.CharField(null=True, blank=True, max_length=100)
    coins = models.IntegerField(null=True, blank=True, default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    badgecolor = models.ImageField(upload_to="farmer_badges/", null=True, blank=True)
    BADGE_CHOICES = {
        'white': 'badge-white.png',
        'yellow': 'badge-yellow.png',
        'red': 'badge-red.jpg',
        'blue': 'badge-blue.jpg',
        'green': 'badge-green.jpg'
    }

    def updateBadgeColor(self, coinCount):
        if coinCount == 0:
            return None
        badges = {'white': 100, 'yellow': 500, "red": 1000, "blue": 1500, "green": 200000000000}
        for color, threshold in badges.items():
            if coinCount < threshold:
                return os.path.join('badges/', self.BADGE_CHOICES[color])
        return os.path.join('badges/', self.BADGE_CHOICES['green'])  

    def add_coins(self, amount):
        self.coins += amount
        self.badgecolor = self.updateBadgeColor(self.coins)
        self.save()
class OTPVerification(models.Model):
    mobile = models.CharField(null=True, blank=True, max_length=10, validators=[validate_mobile_no], unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return timezone.now() < self.expires_at
#############################################################-------------------Farmer Land Records-----------------------###################
class FarmerLandAddress(models.Model):
    fk_farmer=models.ForeignKey(FarmerProfile,on_delete=models.CASCADE,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    land_area=models.FloatField(max_length=20,blank=True,null=True)
    address = models.CharField(null=True, blank=True, max_length=200)
    pincode = models.CharField(null=True, blank=True, max_length=10)
    fk_state = models.ForeignKey(StateMaster,on_delete=models.CASCADE,null=True,blank=True)
    fk_variety=models.ForeignKey(CropVariety,on_delete=models.CASCADE,null=True,blank=True)
    fk_district = models.ForeignKey(DistrictMaster,on_delete=models.CASCADE,null=True,blank=True)
    village = models.CharField(null=True, blank=True, max_length=100)
    lat1 = models.FloatField(null=True, blank=True, max_length=100)
    lat2 = models.FloatField(null=True, blank=True, max_length=100)
    tehsil=models.CharField(null=True, blank=True, max_length=100)
    fk_crops=models.ForeignKey(CropMaster,on_delete=models.CASCADE,null=True,blank=True)
    sowing_date = models.DateField(null=True,blank=True)
    fk_croptype=models.ForeignKey(POPTypes,on_delete=models.CASCADE,null=True,blank=True)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    his_land=models.BooleanField(null=True, blank=True,default=True)
    is_deleted = models.BooleanField(default=False)

#######################-------------------------------Upload Disease---------------------------#################
class Upload_Disease(models.Model):
    created_dt = models.DateTimeField(auto_now_add=False)
    fk_provider=models.ForeignKey(Service_Provider,on_delete=models.CASCADE,null=True,blank=True)
    fk_user=models.ForeignKey(FarmerProfile,on_delete=models.CASCADE,null=True,blank=True)
    fk_crop=models.ForeignKey(CropMaster,on_delete=models.CASCADE,null=True,blank=True)
    fk_disease=models.ForeignKey(DiseaseMaster,on_delete=models.CASCADE,blank=True,null=True)  
    uploaded_image = models.FileField(upload_to="uploaded/", blank=True, null=True)
    filter_type =  models.CharField(null=True,blank=True,max_length=100)
    fk_farmer_land=models.ForeignKey(FarmerLandAddress,on_delete=models.CASCADE,null=True,blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    is_deleted = models.BooleanField(default=False)

###############################----------------------------Disease Product------------------------------#############
class DiseaseProductInfo(models.Model):
    fk_crop=models.ManyToManyField(CropMaster,blank=True)
    fk_disease=models.ForeignKey(DiseaseMaster,on_delete=models.CASCADE,null=True,blank=True)
    fk_product=models.ManyToManyField(ProductDetails,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)

######------------------------------------------Community Section------------------------------############################

# community purpose
class CommunityPost(models.Model):
    fk_user = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE,null=True,blank=True)
    fk_fpo=models.ForeignKey(FPO,on_delete=models.CASCADE,null=True,blank=True)
    description=models.TextField(null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
   

class PostsMedia(models.Model):
    fk_post=models.ForeignKey(CommunityPost,on_delete=models.CASCADE,null=True,blank=True)
    video_file=models.FileField(upload_to='post/videos', null=True, blank=True)
    image_file = models.FileField(upload_to='post/image', null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)


class PostComments(models.Model):
    fk_post=models.ForeignKey(CommunityPost,on_delete=models.CASCADE,null=True,blank=True)
    fk_user=models.ForeignKey(FarmerProfile,on_delete=models.CASCADE,null=True,blank=True)
    fk_fpo=models.ForeignKey(FPO,on_delete=models.CASCADE,null=True,blank=True)
    text=models.TextField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
 

class CommentReply(models.Model):
    fk_postcomment = models.ForeignKey(PostComments,on_delete=models.CASCADE,null=True,blank=True)
    fk_user=models.ForeignKey(FarmerProfile,on_delete=models.CASCADE,null=True,blank=True)
    fk_fpo=models.ForeignKey(FPO,on_delete=models.CASCADE,null=True,blank=True)
    text=models.TextField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
   

class PostsLike(models.Model):
    fk_post=models.ForeignKey(CommunityPost,on_delete=models.CASCADE,null=True,blank=True)    
    fk_user=models.ForeignKey(FarmerProfile,on_delete=models.CASCADE,null=True,blank=True)
    fk_fpo=models.ForeignKey(FPO,on_delete=models.CASCADE,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    like_count = models.IntegerField(default=0, blank=True, null=True)
   
##########################------------------------Shop Comment-------------------------####################
class UserCommentOnShop(models.Model):
    fk_shop = models.ForeignKey(ShopDetails, on_delete=models.CASCADE,blank=True,null=True)
    fk_user = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE,blank=True,null=True)
    comment = models.TextField(null=True, blank=True)
    rating = models.IntegerField(default=0, blank=True, null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

#############################-------------------------------Suggested CrOPS--------------------#############
class SuggestedCrop(models.Model):
    season = models.CharField(max_length=500,null=True,blank=True)
    start_month = models.IntegerField(null=True, blank=True)
    end_month = models.IntegerField(null=True, blank=True)
    description = models.TextField(max_length=1000,null=True,blank=True)
    weather_temperature = models.CharField(max_length=500,null=True,blank=True)
    cost_of_cultivation = models.CharField(max_length=500,null=True,blank=True)
    market_price = models.CharField(max_length=500,null=True,blank=True)
    production = models.CharField(max_length=1000,null=True,blank=True)
    fk_crop=models.ForeignKey(CropMaster,on_delete=models.CASCADE,null=True,blank=True)
    audio=models.FileField(upload_to="cropsuggest_audio/",blank=True, null=True)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

###################################------------------------Govt Schemes-----------------------------################
class GovtSchemes(models.Model):
    scheme_name=models.TextField(max_length=300,null=True,blank=True)
    details=models.TextField(max_length=5000,null=True,blank=True)
    benefits=models.TextField(max_length=5000,null=True,blank=True)
    elgibility=models.TextField(max_length=5000,null=True,blank=True)
    application_process=models.TextField(max_length=5000,null=True,blank=True)
    document_require=models.TextField(max_length=5000,null=True,blank=True)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    scheme_choice=(
        ("Central Schemes","Central Schemes"),
        ("State Schemes","State Schemes"),
        ("केन्द्र सरकार की योजनाएं","केन्द्र सरकार की योजनाएं"),
        ("राज्य सरकार की योजनाएं","राज्य सरकार की योजनाएं")
    )
    scheme_by=models.CharField(null=True,blank=True,choices=scheme_choice,max_length=50,default="")
    ministry_name=models.CharField(null=True,blank=True,max_length=100)
    fk_state=models.ForeignKey(StateMaster,on_delete=models.CASCADE,null=True,blank=True,default="")
    applicationform_link=models.URLField(null=True,blank=True,default="")
    reference=models.TextField(null=True, blank=True, default="")
    scheme_image = models.FileField(upload_to='scheme', null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

##############################-----------------Fertilizer--------------------------------############
class Fertilizer(models.Model):
    fk_state=models.ForeignKey(StateMaster,on_delete=models.CASCADE,null=True,blank=True)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    nitrogen=models.IntegerField(null=True,blank=True)
    phosphorus=models.IntegerField(null=True,blank=True)
    potassium=models.IntegerField(null=True,blank=True)
    zincsulphate=models.IntegerField(null=True,blank=True)
    units_cho=[
    ('KG','KG'),
    ('GM','GM'),
    ('L','L'),
    ('ML','ML'),
    ('DOZEN','DOZEN'),
    ]
    measurement_type=models.CharField(max_length=100,null=True,blank=True,choices=units_cho,default="")
    fk_crop=models.ForeignKey(CropMaster,on_delete=models.CASCADE,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    
##############################----------------------Fruits POP--------------------#########
class FruitsPop(models.Model):
    fk_state=models.ForeignKey(StateMaster,on_delete=models.CASCADE,null=True,blank=True)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    fk_crops=models.ForeignKey(CropMaster,on_delete=models.CASCADE,null=True,blank=True)
    stages=models.CharField(max_length=100,null=True,blank=True)
    stage_name=models.CharField(max_length=100,null=True,blank=True)
    stage_number=models.IntegerField(null=True,blank=True)
    start_periodch=(
    ("January", "January"),
    ("February", "February"),
    ("March", "March"),
    ("April", "April"),
    ("May", "May"),
    ("June", "June"),
    ("July", "July"),
    ("August", "August"),
    ("September", "September"),
    ("October", "October"),
    ("November", "November"),
    ("December", "December")
    )
    start_period=models.CharField(max_length=20,null=True,blank=True,default="",choices=start_periodch)
    end_periodch=(
    ("January", "January"),
    ("February", "February"),
    ("March", "March"),
    ("April", "April"),
    ("May", "May"),
    ("June", "June"),
    ("July", "July"),
    ("August", "August"),
    ("September", "September"),
    ("October", "October"),
    ("November", "November"),
    ("December", "December")
    )
    end_period=models.CharField(max_length=20,null=True,blank=True,default="",choices=end_periodch)
    start_month = models.IntegerField(null=True,blank=True)
    end_month = models.IntegerField(null=True,blank=True)
    prefrence_type=models.IntegerField(null=True,blank=True)
    orchidtype=models.CharField(max_length=20,null=True,blank=True,default="")
    fk_croptype=models.ForeignKey(POPTypes,on_delete=models.CASCADE,null=True,blank=True)
    video=models.FileField(upload_to="fruits_video/", blank=True, null=True)
    audio=models.FileField(upload_to="fruits_audio/", blank=True, null=True)
    fk_product=models.ManyToManyField('fponsuppliers.ProductDetails',blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description=models.TextField(null=True,blank=True)
    is_deleted = models.BooleanField(default=False)

class FruitsStageCompletion(models.Model):
    fk_fruits = models.ForeignKey(FruitsPop, on_delete=models.CASCADE,null=True,blank=True)
    fk_croptype=models.ForeignKey(POPTypes,on_delete=models.CASCADE,null=True,blank=True)
    fk_crops=models.ForeignKey(CropMaster,on_delete=models.CASCADE,null=True,blank=True)
    fk_farmer=models.ForeignKey(FarmerProfile,on_delete=models.CASCADE,null=True)
    fk_farmland=models.ForeignKey(FarmerLandAddress,on_delete=models.CASCADE,null=True)
    start_date = models.DateField(auto_now_add=True)
    completion_date = models.DateField(null=True, blank=True)
    submit_image=models.FileField(upload_to="fruit_submit/", blank=True, null=True)
    days_completed = models.IntegerField(default=0)
    delay_count = models.IntegerField(default=0)
    is_complete = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

###########################----------------SPices POP--------------------------------######################
class SpicesPop(models.Model):  
    stages=models.CharField(max_length=100,null=True,blank=True)
    sow_period=models.CharField(max_length=1000,null=True,blank=True)
    stage_name=models.CharField(max_length=100,null=True,blank=True)
    stage_number=models.IntegerField(null=True,blank=True)
    description=models.TextField(null=True,blank=True)
    fk_crop=models.ForeignKey(CropMaster,on_delete=models.CASCADE,null=True,blank=True)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    preference=models.IntegerField(null=True,blank=True)
    video=models.FileField(upload_to="spicespop/", blank=True, null=True)
    audio=models.FileField(upload_to="spices_audio/", blank=True, null=True)
    fk_croptype=models.ForeignKey(POPTypes,on_delete=models.CASCADE,null=True,blank=True)
    fk_product=models.ManyToManyField('fponsuppliers.ProductDetails',blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

################-------------------------------------Stage Completion of Spices-----------------###############
class SpicestageCompletion(models.Model):
    spice_pop = models.ForeignKey(SpicesPop,on_delete=models.CASCADE,null=True,blank=True)
    stage_number = models.IntegerField(null=True,blank=True)
    fk_farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE,null=True,blank=True)
    fk_farmland=models.ForeignKey(FarmerLandAddress,on_delete=models.CASCADE,null=True)
    fk_croptype=models.ForeignKey(POPTypes,on_delete=models.CASCADE,null=True,blank=True)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    fk_crop = models.ForeignKey(CropMaster, on_delete=models.CASCADE,null=True,blank=True)
    start_date=models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    submit_task=models.FileField(upload_to="task_submit/", blank=True, null=True)
    total_days_spent = models.IntegerField(default=0)
    delay_days = models.IntegerField(default=0)
    early_days = models.IntegerField(default=0)
    progress=models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)


##################------------------------------------Spices Prefrence Record (Land prepation,sowing etc)----------##########
class SpicesPreferenceCompletion(models.Model):
    fk_farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE)
    fk_farmland=models.ForeignKey(FarmerLandAddress,on_delete=models.CASCADE,null=True)
    fk_crop = models.ForeignKey(CropMaster, on_delete=models.CASCADE)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    fk_spicestage=models.ForeignKey(SpicesPop,on_delete=models.CASCADE,null=True,blank=True)
    fk_croptype=models.ForeignKey(POPTypes,on_delete=models.CASCADE,null=True,blank=True)
    preference_number = models.IntegerField()
    name=models.CharField(max_length=1000,null=True,blank=True)
    start_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    total_days = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    progress=models.IntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
#################################################---VEGETABLE POP--########################################################
class VegetablePop(models.Model):  
    stages=models.CharField(max_length=100,null=True,blank=True)
    sow_period=models.CharField(max_length=100,null=True,blank=True)
    stage_name=models.CharField(max_length=100,null=True,blank=True)
    stage_number=models.IntegerField(null=True,blank=True)
    description=models.TextField(null=True,blank=True)
    fk_crop=models.ForeignKey(CropMaster,on_delete=models.CASCADE,null=True,blank=True)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    preference=models.IntegerField(null=True,blank=True)
    video=models.FileField(upload_to="vegetable_pop/", blank=True, null=True)
    audio=models.FileField(upload_to="vegetable_audio/",blank=True, null=True)
    fk_croptype=models.ForeignKey(POPTypes,on_delete=models.CASCADE,null=True,blank=True)
    fk_product=models.ManyToManyField(ProductDetails,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

class VegetableStageCompletion(models.Model):
    vegetable_pop = models.ForeignKey(VegetablePop, on_delete=models.CASCADE,null=True,blank=True)
    stage_number = models.IntegerField(null=True,blank=True)
    fk_farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE,null=True,blank=True)
    fk_farmland=models.ForeignKey(FarmerLandAddress,on_delete=models.CASCADE,null=True)
    fk_croptype=models.ForeignKey(POPTypes,on_delete=models.CASCADE,null=True,blank=True)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    fk_crop = models.ForeignKey(CropMaster, on_delete=models.CASCADE,null=True,blank=True)
    start_date=models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    submit_task=models.FileField(upload_to="task_submit/", blank=True, null=True)
    total_days_spent = models.IntegerField(default=0)
    delay_days = models.IntegerField(default=0)
    early_days = models.IntegerField(default=0)
    progress=models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

class VegetablePreferenceCompletion(models.Model):
    fk_farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE)
    fk_farmland=models.ForeignKey(FarmerLandAddress,on_delete=models.CASCADE,null=True)
    fk_crop = models.ForeignKey(CropMaster, on_delete=models.CASCADE)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    fk_vegetablestage = models.ForeignKey(VegetablePop,on_delete=models.CASCADE,null=True,blank=True)
    fk_croptype=models.ForeignKey(POPTypes,on_delete=models.CASCADE,null=True,blank=True)
    preference_number = models.IntegerField()
    name=models.CharField(max_length=1000,null=True,blank=True)
    start_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    total_days = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    progress=models.IntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)


##########################################--------------------CEREALS POP------------################################
class CerealsPop(models.Model):  
    stages=models.CharField(max_length=100,null=True,blank=True)
    sow_perd=[
        ("0-7","0-7"),
        ("7-14","7-14"),
        ("14-21","14-21"),
        ("21-28","21-28"),
        ("28-35","28-35"),
        ("35-42","35-42"),
        ("42-49","42-49"),
        ("49-56","49-56"),
        ("56-63","56-63"),
        ("63-70","63-70"),
        ("70-77","70-77"),
        ("77-84","77-84"),
    ]
    sow_period=models.CharField(max_length=100,null=True,blank=True,choices=sow_perd,default="")
    stage_name=models.CharField(max_length=100,null=True,blank=True)
    stage_number=models.IntegerField(null=True,blank=True)
    description=models.TextField(null=True,blank=True)
    fk_crop=models.ForeignKey(CropMaster,on_delete=models.CASCADE,null=True,blank=True)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    preference=models.IntegerField(null=True,blank=True)
    video=models.FileField(upload_to="vegetable_pop/", blank=True, null=True)
    audio=models.FileField(upload_to="vegetable_audio/",blank=True, null=True)
    fk_croptype=models.ForeignKey(POPTypes,on_delete=models.CASCADE,null=True,blank=True)
    fk_product=models.ManyToManyField(ProductDetails,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

class CerealStageCompletion(models.Model):
    cereal_pop = models.ForeignKey(CerealsPop, on_delete=models.CASCADE,null=True,blank=True)
    stage_number = models.IntegerField(null=True,blank=True)
    fk_farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE,null=True,blank=True)
    fk_farmland=models.ForeignKey(FarmerLandAddress,on_delete=models.CASCADE,null=True)
    fk_croptype=models.ForeignKey(POPTypes,on_delete=models.CASCADE,null=True,blank=True)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    fk_crop = models.ForeignKey(CropMaster, on_delete=models.CASCADE,null=True,blank=True)
    start_date=models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    submit_task=models.FileField(upload_to="task_submit/", blank=True, null=True)
    total_days_spent = models.IntegerField(default=0)
    delay_days = models.IntegerField(default=0)
    early_days = models.IntegerField(default=0)
    progress=models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

class CerealPreferenceCompletion(models.Model):
    fk_farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE)
    fk_farmland=models.ForeignKey(FarmerLandAddress,on_delete=models.CASCADE,null=True)
    fk_crop = models.ForeignKey(CropMaster, on_delete=models.CASCADE)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    fk_cerealstage = models.ForeignKey(CerealsPop,on_delete=models.CASCADE,null=True,blank=True)
    fk_croptype=models.ForeignKey(POPTypes,on_delete=models.CASCADE,null=True,blank=True)
    preference_number = models.IntegerField()
    name=models.CharField(max_length=1000,null=True,blank=True)
    start_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    total_days = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    progress=models.IntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
#######################-------------------------Notifications------------------####################
class PopWeatherCondition(models.Model):
    condition = models.CharField(max_length=255)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    def __str__(self):
        return self.condition

class WeatherPopNotification(models.Model):
    fk_weather_condition = models.ManyToManyField(PopWeatherCondition,blank=True)
    fk_croptype=models.ForeignKey(POPTypes,on_delete=models.CASCADE,null=True,blank=True)
    preference_number = models.IntegerField(null=True,blank=True)
    fk_crops=models.ForeignKey(CropMaster, on_delete=models.CASCADE,null=True,blank=True)
    notification_text = models.TextField(max_length=1000,null=True, blank=True)
    stages=models.CharField(max_length=1000,null=True, blank=True)
    gif=models.FileField(upload_to="pop_gif/", blank=True, null=True)
    fk_language=models.ForeignKey(LanguageSelection,on_delete=models.CASCADE,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.fk_weather_condition} - Preference {self.preference_number}"


###################-----------------------------Services Providers Soil Services Prices------------------------################
class SoilCharges(models.Model):
    fk_providername=models.ManyToManyField(Service_Provider,blank=True)
    fk_shop=models.ForeignKey('fponsuppliers.ShopDetails',on_delete=models.CASCADE,blank=True,null=True)
    price=models.FloatField(default=0, blank=True, null=True)
    test_choice=(
    ("In Branch", "In Branch"),
    ("Collection", "Collection"),
    )
    price_before=models.FloatField(null=True,blank=True,max_length=100)
    plans=models.CharField(max_length= 200 , choices = test_choice,default='Basic')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)