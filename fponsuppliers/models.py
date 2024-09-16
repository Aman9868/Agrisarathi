# Create your models here.
##models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password, check_password
import re
from django.apps import apps
from datetime import datetime
import os
from .managers import *
def validate_mobile_no(value):
    if not re.match(r'^\d{10}$', value):
        raise ValidationError("Mobile number must be exactly 10 digits.")
    

##################-------------------------------Supplier----------------------------------##################
class Supplier(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='supplier')
    email=models.EmailField(max_length=255,null=True, blank=True)
    email_verified=models.BooleanField(null=True,blank=True,default="False")
    mobile = models.CharField(null=True, blank=True, max_length=10, validators=[validate_mobile_no], unique=True)
    profile = models.FileField(upload_to="shop/supplier_profile", blank=True, null=True)
    supplier_name=models.CharField(max_length=100,null=True, blank=True)
    supplier_pincode=models.CharField(max_length=10,null=True, blank=True)
    password = models.CharField(max_length=128)
    village=models.CharField(max_length=128,null=True,blank=True)
    fk_state = models.ForeignKey('farmers.StateMaster',on_delete=models.CASCADE,null=True,blank=True)
    fk_district = models.ForeignKey('farmers.DistrictMaster',on_delete=models.CASCADE,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(CustomUser, related_name='supplier_created_by', null=True, blank=True, on_delete=models.SET_NULL)
    last_updated_by = models.ForeignKey(CustomUser, related_name='supplier_last_updated_by', null=True, blank=True, on_delete=models.SET_NULL)
    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
##################--------------------------FPO---------------------------------#########################
class FPO(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='fpo')
    email=models.EmailField(max_length=255,null=True, blank=True)
    email_verified=models.BooleanField(null=True,blank=True,default="False")
    mobile = models.CharField(null=True, blank=True, max_length=10, validators=[validate_mobile_no], unique=True)
    fpo_name=models.CharField(max_length=100,null=True, blank=True)
    email = models.EmailField(null=True,blank=True)
    profile = models.FileField(upload_to="fpo_profile", blank=True, null=True)
    address = models.TextField(null=True, blank=True)
    password = models.CharField(max_length=128)
    fk_state = models.ForeignKey('farmers.StateMaster',on_delete=models.CASCADE,null=True,blank=True)
    fk_district = models.ForeignKey('farmers.DistrictMaster',on_delete=models.CASCADE,null=True,blank=True)
    village=models.CharField(max_length=128,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    coins = models.IntegerField(null=True, blank=True, default=0)
    created_by = models.ForeignKey(CustomUser, related_name='fpo_created_by', null=True, blank=True, on_delete=models.SET_NULL)
    last_updated_by = models.ForeignKey(CustomUser, related_name='fpo_last_updated_by', null=True, blank=True, on_delete=models.SET_NULL)
    badgecolor = models.ImageField(upload_to="fpo_badges/", null=True, blank=True)
    BADGE_CHOICES = {
        'white': 'badge-white.png',
        'yellow': 'badge-yellow.png',
        'red': 'badge-red.jpg',
        'blue': 'badge-blue.jpg',
        'green': 'badge-green.jpg'
    }

    def updatefpoBadgeColor(self, coinCount):
        if coinCount == 0:
            return None
        badges = {'white': 100, 'yellow': 500, "red": 1000, "blue": 1500, "green": 200000000000}
        for color, threshold in badges.items():
            if coinCount < threshold:
                return os.path.join('badges/', self.BADGE_CHOICES[color])
        return os.path.join('badges/', self.BADGE_CHOICES['green'])  

    def addfpo_coins(self, amount):
        self.coins += amount
        self.badgecolor = self.updatefpoBadgeColor(self.coins)
        self.save()
    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
##############################--------------------------------------Shops & Products-----------------------############################
class ShopDetails(models.Model):
    shopName = models.CharField(max_length=100, blank=True, null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    shopContactNo = models.CharField(max_length=12, null=True, blank=True)
    shopaddress = models.CharField(max_length=50, blank=True, null=True)
    fk_state = models.ForeignKey('farmers.StateMaster',on_delete=models.CASCADE,null=True,blank=True)
    fk_district = models.ForeignKey('farmers.DistrictMaster',on_delete=models.CASCADE,null=True,blank=True)
    village=models.CharField(max_length=100,blank= True,null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    shopLatitude = models.DecimalField(max_digits=15, decimal_places=10, blank=True, null=True)
    shopLongitude = models.DecimalField(max_digits=15, decimal_places=10, blank=True, null=True)
    productDealsIn = models.CharField(max_length=500, blank=True, null=True)
    Tehsil = models.CharField(max_length=50, blank=True, null=True)
    time_open = (
    ("1 a.m", "1 a.m"),
    ("2 a.m", "2 a.m"),
    ("3 a.m", "3 a.m"),
    ("4 a.m", "4 a.m"),
    ("5 a.m", "5 a.m"),
    ("6 a.m", "6 a.m"),
    ("7 a.m", "7 a.m"),
    ("8 a.m", "8 a.m"),
    ("9 a.m", "9 a.m"),
    ("10 a.m", "10 a.m"),
    ("11 a.m", "11 a.m"),
    )

    time_close = (
    ("12 p.m", "12 p.m"),
    ("1 p.m", "1 p.m"),
    ("2 p.m", "2 p.m"),
    ("3 p.m", "3 p.m"),
    ("4 p.m", "4 p.m"),
    ("5 p.m", "5 p.m"),
    ("6 p.m", "6 p.m"),
    ("7 p.m", "7 p.m"),
    ("8 p.m", "8 p.m"),
    ("9 p.m", "9 p.m"),
    ("10 p.m", "10 p.m"),
    ("11 p.m", "11 p.m"),
    )

    shopd = (
    ("Monday - Tuesday", "Monday - Tuesday"),
    ("Monday - Wednesday", "Monday - Wednesday"),
    ("Monday - Thursday", "Monday - Thursday"),
    ("Monday - Friday", "Monday - Friday"),
    ("Monday - Saturday", "Monday - Saturday"),
    ("Monday - Sunday", "Monday - Sunday"),
    )

    shopclosed = (
    ("Monday", "Monday"),
    ("Tuesday", "Tuesday"),
    ("Wednesday", "Wednesday"),
    ("Thursday", "Thursday"),
    ("Friday", "Friday"),
    ("Saturday", "Saturday"),
    ("Sunday", "Sunday"),
    )
    
    shop_opentime=models.CharField(max_length=100,choices=time_open,default="10 a.m")
    shop_closetime=models.CharField(max_length=100,choices=time_close,default="10 p.m")
    shop_opendays=models.CharField(max_length=100,choices=shopd,default="Monday - Tuesday")
    shop_closedon=models.CharField(max_length=100,choices=shopclosed,default="Sunday")
    shopimage = models.ImageField(upload_to='shopimage/', blank=True, null=True)
    pincode = models.CharField(null=True, blank=True, max_length=10)
    no_of_ratings = models.IntegerField(default=0, blank=True, null=True)
    choices=(
        ("Loan", "Loan"),
      	("Soil Testing", "Soil Testing"),
        ("Shops","Shops"),
        ("Yojna","Yojna")
	)
    provided_by=models.CharField(max_length= 200 , choices = choices,default='Shops')
    fk_fpo=models.ForeignKey(FPO,on_delete=models.CASCADE,blank=True,null=True)
    fk_supplier=models.ForeignKey(Supplier,on_delete=models.CASCADE,null=True,blank=True)
    have_soil = models.BooleanField(null=True,blank=True)

############################-------------------------------Banks Business Details----------------------###############
class BankBusinessDetails(models.Model):
    fk_fpo=models.ForeignKey(FPO,on_delete=models.CASCADE,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    fk_supplier=models.ForeignKey(Supplier,on_delete=models.CASCADE,null=True,blank=True)
    accountholder_name=models.CharField(max_length=100,null=True,blank=True)
    account_number=models.IntegerField(null=True,blank=True)
    bank_name=models.CharField(max_length=100,null=True,blank=True)
    ifsc_code=models.CharField(max_length=100,null=True,blank=True)
    business_establishdate=models.DateField(null=True,blank=True)
    pan_no=models.CharField(max_length=100,null=True,blank=True)
    registration_id=models.CharField(max_length=100,null=True,blank=True)
    gst_number=models.CharField(max_length=100,null=True,blank=True)

##################################--------------------------Product Type For Sale----------------------#############
class ProductType(models.Model):
    typchoic=[
        ("Agricultural Inputs","Agricultural Inputs"),
        ("Crops","Crops"),
        ("Finish Goods","Finish Goods")
    ]
    product_type=models.CharField(max_length=100,null=True,blank=True,choices=typchoic)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
######################---------------------------------FPO Suppliers-----------------------------########################
class FPOSuppliers(models.Model):
    fk_fpo=models.ForeignKey(FPO,on_delete=models.CASCADE,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    purchase_date=models.DateField(null=True,blank=True)
    party_name=models.CharField(null=True,blank=True,max_length=100)
    party_mobileno=models.CharField(null=True,blank=True,max_length=10)
    party_company=models.CharField(null=True,blank=True,max_length=10)
    total_amount=models.FloatField(null=True,blank=True,max_length=100)
    unit_price=models.FloatField(null=True,blank=True,max_length=100)
    party_gst=models.CharField(null=True,blank=True,max_length=100)
    state=models.CharField(null=True,blank=True,max_length=100)
    district=models.CharField(null=True,blank=True,max_length=100)
    fk_productype=models.ForeignKey(ProductType,on_delete=models.CASCADE,null=True,blank=True)
    quantity=models.FloatField(null=True,blank=True)
##################----------------------------------Input Suppliers ----------#########
class InputSuppliers(models.Model):
    purchase_date=models.DateField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    fk_supplier=models.ForeignKey(Supplier,on_delete=models.CASCADE,null=True)
    party_name=models.CharField(null=True,blank=True,max_length=100)
    party_mobileno=models.CharField(null=True,blank=True,max_length=10)
    party_company=models.CharField(null=True,blank=True,max_length=100)
    total_amount=models.FloatField(null=True,blank=True,max_length=100)
    unit_price=models.FloatField(null=True,blank=True,max_length=100)
    fk_productype=models.ForeignKey(ProductType,on_delete=models.CASCADE,null=True,blank=True)
    quantity=models.FloatField(null=True,blank=True)
    state=models.CharField(null=True,blank=True,max_length=100)
    district=models.CharField(null=True,blank=True,max_length=100)
    party_gst=models.CharField(null=True,blank=True,max_length=100)
    
#########################-------------------Product Measurements------------------#####################
class ProductMeasurements(models.Model):
    measurement_code=models.CharField(max_length=100,null=True,blank=True)
    description=models.CharField(max_length=100,null=True,blank=True)
    created_at=models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
#####----------Product Information----------------------##################
class ProductDetails(models.Model):
    productName = models.CharField(max_length=100, blank=True, null=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    productDescription = models.CharField(max_length=500, blank=True, null=True)
    composition=models.CharField(max_length=500, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    manufacturerName = models.CharField(max_length=100, blank=True, null=True)
    manufacturing_date=models.DateField(null=True,blank=True)
    product_image = models.ImageField(upload_to='productimage/', blank=True, null=True)
    fk_serviceprovider=models.ForeignKey('farmers.Service_Provider',on_delete=models.CASCADE,blank=True,null=True)
    measurement_type=models.ForeignKey(ProductMeasurements,on_delete=models.CASCADE,blank=True,null=True)
    measurement_unit=models.IntegerField(null=True,blank=True)
    sellby_choice=[
        ("Pcs","PCS"),
        ("Weight","WEIGHT")
    ]
    sellby=models.CharField(max_length=100,choices=sellby_choice,null=True,blank=True,default="")
    quantity=models.IntegerField(null=True,blank=True)
    pieces = models.IntegerField(null=True,blank=True)
    sell_statschoice=[
        ("Online","Online"),
        ("Offline","Offline"),
        ("All","All")
    ]
    selling_status=models.CharField(max_length=100,null=True,blank=True,choices=sell_statschoice,default="")
    fk_productype=models.ForeignKey(ProductType,on_delete=models.CASCADE,null=True,blank=True)
    Category=models.CharField(max_length=100,null=True,blank=True)
    fk_fpo=models.ForeignKey(FPO,on_delete=models.CASCADE,null=True,blank=True)
    fk_crops=models.ForeignKey('farmers.CropMaster',on_delete=models.CASCADE,null=True,blank=True)
    fk_variety=models.ForeignKey('farmers.CropVariety',on_delete=models.CASCADE,null=True,blank=True)
    fk_supplier=models.ManyToManyField(Supplier,blank=True)
    expiry_date=models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    is_deleted = models.BooleanField(default=False)
    fk_fposupplier=models.ForeignKey(FPOSuppliers,on_delete=models.CASCADE,null=True,blank=True)
    fk_inputsupplier=models.ForeignKey(InputSuppliers,on_delete=models.CASCADE,null=True,blank=True)
    fk_poptype=models.ForeignKey('farmers.POPTypes',blank=True,null=True,on_delete=models.CASCADE)
    def expiry_datestatus(self):
        if self.expiry_date:
            current_date = datetime.now().date()
            delta = (self.expiry_date - current_date).days
            if delta > 10:
                return None
            elif delta > 0:
                return f"Expires in {delta} days"
            elif delta == 0:
                return "Expires today"
            else:
                return "Expired"
        return "No expiry date set"

    

############################################-------------------Pricing Table------------------------###################
class ProductPrices(models.Model):
    fk_product=models.ForeignKey(ProductDetails,blank=True,null=True,on_delete=models.CASCADE)
    fk_fpo=models.ForeignKey(FPO,blank=True,null=True,on_delete=models.CASCADE)
    fk_supplier=models.ForeignKey(Supplier,blank=True,null=True,on_delete=models.CASCADE)
    fk_fposupplier=models.ForeignKey(FPOSuppliers,blank=True,null=True,on_delete=models.CASCADE)
    fk_inputsupplier=models.ForeignKey(InputSuppliers,blank=True,null=True,on_delete=models.CASCADE)
    purchase_price=models.FloatField(null=True,blank=True,max_length=100)
    unit_price=models.FloatField(null=True,blank=True,max_length=100)
    discount=models.FloatField(null=True,blank=True,max_length=100)
    gst=models.FloatField(null=True,blank=True,max_length=100,default=0)
    sgst=models.FloatField(null=True,blank=True,max_length=100,default=0)
    cgst=models.FloatField(null=True,blank=True,max_length=100,default=0)
    final_price_unit=models.FloatField(null=True,blank=True,max_length=100)
    is_deleted = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)   

################-------------------Inventory Details-----------------####################
class InventoryDetails(models.Model):
    fk_product=models.ForeignKey(ProductDetails, on_delete=models.CASCADE,null=True, blank=True)
    fk_fpo=models.ForeignKey(FPO,blank=True,null=True,on_delete=models.CASCADE)
    fk_supplier=models.ForeignKey(Supplier,blank=True,null=True,on_delete=models.CASCADE)
    fk_fposupplier=models.ForeignKey(FPOSuppliers,on_delete=models.CASCADE,null=True,blank=True)
    fk_inputsupplier=models.ForeignKey(InputSuppliers,on_delete=models.CASCADE,null=True,blank=True)
    stock = models.PositiveIntegerField()
    location = models.CharField(max_length=100,null=True,blank=True)
    created_at=models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    fk_productype=models.ForeignKey(ProductType,on_delete=models.CASCADE,null=True,blank=True)
    fk_price=models.ForeignKey(ProductPrices,blank=True,null=True,on_delete=models.CASCADE)
    def stock_status(self):
        if self.stock==0:
            return "Out of Stock"
        elif self.stock<10:
            return "Low Stock"
        else:
            return "In Stock"
    def save(self, *args, **kwargs):
        if not self.stock:
            self.stock = self.fk_product.quantity
        super().save(*args, **kwargs)
#####################################---------------------------Buyer Details------------------------#############
class CustomerDetails(models.Model):
    buyer_name=models.CharField(null=True,blank=True,max_length=100)
    mobile_no=models.CharField(null=True,blank=True,max_length=10)
    address=models.TextField(max_length=400,null=True,blank=True)
    company_name=models.CharField(null=True,blank=True,max_length=100)
    gst_number=models.CharField(null=True,blank=True,max_length=100)
    created_at=models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    fk_fpo=models.ForeignKey(FPO,blank=True,null=True,on_delete=models.CASCADE)
    fk_farmer=models.ForeignKey('farmers.FarmerProfile',blank=True,null=True,on_delete=models.CASCADE)
    fk_supplier=models.ForeignKey(Supplier,blank=True,null=True,on_delete=models.CASCADE)
#####################----------------------------------Product Sale------------------------################
class ProductSale(models.Model):
    fk_invent=models.ForeignKey(InventoryDetails,on_delete=models.CASCADE,null=True,blank=True)
    fk_custom=models.ForeignKey(CustomerDetails,on_delete=models.CASCADE,null=True,blank=True)
    amount = models.FloatField(null=True,blank=True,max_length=100)
    paymentchocie=[
        ('Cash','Cash'),
        ('Card','Card'),
        ('Online','Online'),
        ('Cheque','Cheque'),
        ('Others','Others'),
    ]
    payment_method = models.CharField(max_length=100, choices=paymentchocie, null=True, blank=True)
    sales_date = models.DateField(null=True,blank=True)
    final_price=models.FloatField(null=True,blank=True,max_length=100)
    created_at=models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

#########################---------------------------Sales Record-----------------------##################
class SalesRecordItem(models.Model):
    fk_fpo=models.ForeignKey(FPO,on_delete=models.CASCADE,null=True,blank=True)
    fk_supplier=models.ForeignKey(Supplier,on_delete=models.CASCADE,null=True,blank=True)
    paymentchocie=[
        ('Cash','Cash'),
        ('Card','Card'),
        ('Online','Online'),
        ('Cheque','Cheque'),
        ('Others','Others'),
    ]
    payment_method = models.CharField(max_length=100, choices=paymentchocie, null=True, blank=True)
    fk_fposupplier=models.ForeignKey(FPOSuppliers,on_delete=models.CASCADE,null=True,blank=True)
    fk_inputsupplier=models.ForeignKey(InputSuppliers,on_delete=models.CASCADE,null=True,blank=True)
    fk_invent=models.ForeignKey(InventoryDetails,on_delete=models.CASCADE,null=True,blank=True)
    fk_customer=models.ForeignKey(CustomerDetails,on_delete=models.CASCADE,null=True,blank=True)
    fk_productype=models.ForeignKey(ProductType,on_delete=models.CASCADE,null=True,blank=True)
    category = models.CharField(max_length=100,null=True,blank=True)
    product_name = models.CharField(max_length=100,null=True,blank=True)
    quantity = models.PositiveIntegerField()
    total_amount=models.FloatField(null=True,blank=True,max_length=100)
    sales_date = models.DateField(null=True,blank=True)
    name=models.CharField(max_length=100,null=True,blank=True)
    created_at=models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    


