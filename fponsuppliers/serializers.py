##serialziers.py
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from .models import *
from farmers.models import FarmerProfile,CropMapper,CropVariety
from .managers import *
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.pagination import PageNumberPagination
####################-----------------------------------User Serializer*---------------#############
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'mobile', 'name', 'age', 'password']
        extra_kwargs = {'password': {'write_only': True}}

######################----------------------------------------FPO--------------------------###########
class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['mobile','password','user_type'] 
        extra_kwargs = {'password': {'write_only': True}}

    def create_user(self, validated_data, user_type):
        user = CustomUser.objects.create_user(
            mobile=validated_data['mobile'],
            password=validated_data['password'],
            user_type=validated_data['user_type']
        )
        if user_type == 'fpo':
            FPO.objects.create(user=user, mobile=user.mobile,password=user.password)
        elif user_type == 'supplier':
            Supplier.objects.create(user=user, mobile=user.mobile,password=user.password)
        else:
            raise ValueError("Invalid user type")
        print(f"Created {user_type} user: {user}")
        return user 
#################----------------------------------FPO Profile Details----------------------##########################
class FPOProfileSerializer(serializers.ModelSerializer):
  fpo_id=serializers.IntegerField(source='id')
  state=serializers.SerializerMethodField()
  district=serializers.SerializerMethodField()
  class Meta:
    model = FPO
    fields = ['fpo_id', 'mobile', 'fpo_name','state','district','profile','address']
  def get_state(self,obj):
        return obj.fk_state.state if obj.fk_state else None
  def get_district(self,obj):
        return obj.fk_district.district if obj.fk_district else None
  
class FPOBankDetailSerializer(serializers.ModelSerializer):
    fpobank_id = serializers.IntegerField(source='id')
    class Meta:
        model = BankBusinessDetails
        fields = ["fpobank_id","fk_fpo_id","created_at","updated_at","accountholder_name","account_number","bank_name","ifsc_code",
                    "business_establishdate","pan_no","registration_id","gst_number"
                    ]
class FPOShopDetailsSerializer(serializers.ModelSerializer):
    fposhop_id = serializers.IntegerField(source='id')
    class Meta:
        model = ShopDetails
        fields = ["fposhop_id","shopName","created_at","updated_at","shopContactNo","shopaddress","fk_state_id","fk_district_id","village",
                  "city","shopLatitude","shopLongitude","shop_opentime","shop_closetime","shop_opendays","shop_closedon","shopimage",
                    "pincode","no_of_ratings","fk_fpo_id","have_soil"
]
        
class FPODetailsSerializer(serializers.ModelSerializer):
    profile = FPOProfileSerializer(source='*')
    bank_details = serializers.SerializerMethodField()
    shop_details = serializers.SerializerMethodField()
    class Meta:
        model = FPO
        fields = ['profile', 'bank_details', 'shop_details']

    def get_bank_details(self, obj):
        bank_details = BankBusinessDetails.objects.filter(fk_fpo_id=obj.id).first()
        if bank_details:
            return FPOBankDetailSerializer(bank_details).data
        return None

    def get_shop_details(self, obj):
        shop_details = ShopDetails.objects.filter(fk_fpo_id=obj.id).first()
        if shop_details:
            return FPOShopDetailsSerializer(shop_details).data
        return None

    
#################----------------------------------Supplier---------------------------#################

class SupplierProfileSerializer(serializers.ModelSerializer):
  state=serializers.SerializerMethodField()
  supplier_id=serializers.IntegerField(source='id')
  #district=serializers.SerializerMethodField()
  class Meta:
    model = FPO
    fields = ['supplier_id', 'mobile', 'supplier_name','state']
  def get_state(self,obj):
        return obj.fk_state.state if obj.fk_state else None
  
class SupplierBankDetailSerializer(serializers.ModelSerializer):
    supplierbank_id = serializers.IntegerField(source='id')
    class Meta:
        model = BankBusinessDetails
        fields = ["supplierbank_id","fk_supplier_id","created_at","updated_at","accountholder_name","account_number","bank_name","ifsc_code",
                    "business_establishdate","pan_no","registration_id","gst_number"
                    ]
class SupplierShopDetailsSerializer(serializers.ModelSerializer):
    suppliershop_id = serializers.IntegerField(source='id')
    class Meta:
        model = ShopDetails
        fields = ["suppliershop_id","shopName","created_at","updated_at","shopContactNo","shopaddress","fk_state_id","fk_district_id","village",
                  "city","shopLatitude","shopLongitude","shop_opentime","shop_closetime","shop_opendays","shop_closedon","shopimage",
                    "pincode","no_of_ratings","fk_supplier_id","have_soil"]

class SupplierDetailsSerializer(serializers.ModelSerializer):
    profile = SupplierProfileSerializer(source='*')
    bank_details = serializers.SerializerMethodField()
    shop_details = serializers.SerializerMethodField()
    class Meta:
        model = Supplier
        fields = ['profile', 'bank_details', 'shop_details']

    def get_bank_details(self, obj):
        bank_details = BankBusinessDetails.objects.filter(fk_supplier_id=obj.id).first()
        if bank_details:
            return SupplierBankDetailSerializer(bank_details).data
        return None

    def get_shop_details(self, obj):
        shop_details = ShopDetails.objects.filter(fk_supplier_id=obj.id).first()
        if shop_details:
            return SupplierShopDetailsSerializer(shop_details).data
        return None
    
###########################------------------------------------------SingleProduct Serializer FPO--------------#########################
class FPOProductDetailsSerializer(serializers.ModelSerializer):
    product_info = serializers.SerializerMethodField()
    prices_info = serializers.SerializerMethodField()

    class Meta:
        model = ProductDetails
        fields = ['product_info', 'prices_info']

    def get_product_info(self, obj):
        return {
            "product_id": obj.id,
            "product_name": obj.productName,
            "product_description": obj.productDescription,
            "fk_product_type_id": obj.fk_productype_id,
            "manufacturer_name": obj.manufacturerName,
            "measurement_type": obj.measurement_type,
            "measurement_unit": obj.measurement_unit,
            "quantity": obj.quantity,
            "expiry_date": obj.expiry_date,
            "composition": obj.composition,
            "selling_status": obj.selling_status,
            "category": obj.Category,
            "fpo_id": obj.fk_fpo.id if obj.fk_fpo else None,
            'crop_name':obj.fk_crops.crop_name if obj.fk_crops else None,
            'variety': obj.fk_variety.variety if obj.fk_variety else None,
        }

    def get_prices_info(self, obj):
        fpo_id = self.context['fpo_id']
        prices = obj.productprices_set.filter(fk_fpo_id=fpo_id)  
        return [
            {
                "price_id": price.id,
                "purchase_price": price.purchase_price,
                "unit_price": price.unit_price,
                "discount": price.discount,
                "final_price_unit": price.final_price_unit
            }
            for price in prices
        ]
#######################-
class FPOProductDetailFilterSerializer(serializers.ModelSerializer):
    fpo_id = serializers.IntegerField(source='fk_fpo.id', read_only=True)
    crop_name = serializers.CharField(source='fk_crops.crop_name', read_only=True)
    variety = serializers.CharField(source='fk_variety.variety', read_only=True)
    prices = serializers.SerializerMethodField()

    class Meta:
        model = ProductDetails
        fields = [
            'id', 'productName', 'productDescription', 'fk_productype_id', 
            'manufacturerName', 'measurement_type', 'measurement_unit', 
            'quantity', 'expiry_date', 'composition', 'selling_status', 
            'Category', 'fpo_id', 'crop_name', 'variety', 'prices'
        ]

    def get_prices(self, obj):
        fpo_id = self.context['fpo_id']
        prices = obj.productprices_set.filter(fk_fpo_id=fpo_id)  
        return [
            {
                "price_id": price.id,
                "purchase_price": price.purchase_price,
                "unit_price": price.unit_price,
                "discount": price.discount,
                "final_price_unit": price.final_price_unit
            }
            for price in prices
        ]
#############################-------------------------------------SingleProduct Serializer Supplier------------------------#####
class SupplierProductDetailsSerializer(serializers.ModelSerializer):
    product_info = serializers.SerializerMethodField()
    prices_info = serializers.SerializerMethodField()
    class Meta:
        model = ProductDetails
        fields = ['product_info', 'prices_info']
    def get_product_info(self, obj):
        return {
            "product_id": obj.id,
            "product_name": obj.productName,
            "product_description": obj.productDescription,
            "fk_product_type_id": obj.fk_productype_id,
            "manufacturer_name": obj.manufacturerName,
            "measurement_type": obj.measurement_type,
            "measurement_unit": obj.measurement_unit,
            "quantity": obj.quantity,
            "composition": obj.composition,
            "selling_status": obj.selling_status,
            "category": obj.Category,
            "supplier_id": obj.fk_supplier.id if obj.fk_supplier else None
        }

    def get_prices_info(self, obj):
        supplier_id = self.context['supplier_id']
        prices = obj.productprices_set.filter(fk_supplier_id=supplier_id)  
        return [
            {
                "price_id": price.id,
                "purchase_price": price.purchase_price,
                "unit_price": price.unit_price,
                "discount": price.discount,
                "final_price_unit": price.final_price_unit
            }
            for price in prices
        ]
#######-----
class SupplierProductFilterDetailsSerializer(serializers.ModelSerializer):
    supplier_id = serializers.IntegerField(source='fk_supplier.id', read_only=True)
    prices = serializers.SerializerMethodField()

    class Meta:
        model = ProductDetails
        fields = [
            'id', 'productName', 'productDescription', 'fk_productype_id', 
            'manufacturerName', 'measurement_type', 'measurement_unit', 
            'quantity', 'composition', 'selling_status', 'Category', 
            'supplier_id', 'prices'
        ]

    def get_prices(self, obj):
        supplier_id = self.context['supplier_id']
        prices = obj.productprices_set.filter(fk_supplier_id=supplier_id)  
        return [
            {
                "price_id": price.id,
                "purchase_price": price.purchase_price,
                "unit_price": price.unit_price,
                "discount": price.discount,
                "final_price_unit": price.final_price_unit
            }
            for price in prices
        ]
######################------------------------------FPO/Supplier Purchase Records--------------------------###################
class FPOSuppliersSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    class Meta:
        model=FPOSuppliers
        fields = [
            'id', 'party_name', 'party_mobileno', 'party_company', 
            'total_amount', 'unit_price', 'party_gst', 'fk_productype', 
            'quantity', 'products'
        ]
    def get_products(self, obj):
        fpo_id = self.context['fpo_id']
        products = ProductDetails.objects.filter(fk_fposupplier=obj, fk_fpo_id=fpo_id)
        return FPOProductDetailsSerializer(products, many=True, context={'fpo_id': fpo_id}).data
class SupplierSupplySerializer(serializers.ModelSerializer):
    data=SupplierProductDetailsSerializer(many=True, read_only=True, source='supplierproductdetails_set')
    class Meta:
        model=InputSuppliers
        fields = [
            'id', 'party_name', 'party_mobileno', 'party_company', 
            'total_amount', 'unit_price', 'party_gst', 'fk_productype', 
            'quantity', 'products',
        ]
    def get_products(self, obj):
        supplier_id = self.context['supplier_id']
        products = ProductDetails.objects.filter(fk_inputsupplier=obj, fk_supplier_id=supplier_id)
        return SupplierProductDetailsSerializer(products, many=True, context={'supplier_id': supplier_id}).data


######################-------------------------------Getall Product FPO/Suppliers---------------###################
class ProductPricesSerializer(serializers.ModelSerializer):
    price_id=serializers.IntegerField(source='id')
    class Meta:
        model = ProductPrices
        fields = ['price_id','purchase_price', 'unit_price', 'discount', 'final_price_unit']
class FPOProductDetailSerializer(serializers.ModelSerializer):
    inventory_id=serializers.IntegerField(source='id')
    supplier_id=serializers.SerializerMethodField()
    stock_status=serializers.SerializerMethodField()
    product_id = serializers.IntegerField(source='fk_product.id')
    productName = serializers.CharField(source='fk_product.productName')
    supplier_name = serializers.CharField(source='fk_fposupplier.party_name')
    product_price = serializers.FloatField(source='fk_price.unit_price')
    Category = serializers.CharField(source='fk_product.Category')
    product_type = serializers.CharField(source='fk_product.fk_productype.product_type')
    stock_quantity = serializers.IntegerField(source='stock')
    class Meta:
        model=InventoryDetails
        fields=['inventory_id','product_id','productName','Category','product_type','supplier_id','stock_status','stock_quantity',
                'supplier_name','product_price']
    def get_stock_status(self, obj):
        return obj.stock_status() if obj else None
    def get_supplier_id(self, obj):
        return obj.fk_fposupplier.id if obj.fk_fposupplier else None
    
class SupplierProductDetailSerializer(serializers.ModelSerializer):
    inventory_id=serializers.IntegerField(source='id')
    supplier_id=serializers.SerializerMethodField()
    stock_status=serializers.SerializerMethodField()
    product_id = serializers.IntegerField(source='fk_product.id')
    productName = serializers.CharField(source='fk_product.productName')
    supplier_name = serializers.CharField(source='fk_inputsupplier.party_name', allow_null=True)
    product_price = serializers.CharField(source='fk_price.unit_price', allow_null=True)
    Category = serializers.CharField(source='fk_product.Category')
    product_type = serializers.CharField(source='fk_product.fk_productype.product_type')
    stock_quantity = serializers.IntegerField(source='stock')
    class Meta:
        model=InventoryDetails
        fields=['inventory_id','product_id','productName','Category','product_type','supplier_id','stock_status','stock_quantity',
                'supplier_name','product_price']
    def get_stock_status(self, obj):
        return obj.stock_status() if obj else None
    def get_supplier_id(self, obj):
        return obj.fk_inputsupplier.id if obj.fk_inputsupplier else None
    
######################-----------------------------------Sales by FPO/Suppliers-----------------------------#############
class FPOCustomerDetailsSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(source='id', read_only=True)
    class Meta:
        model = CustomerDetails
        fields = ['customer_id','buyer_name', 'mobile_no', 'address', 'fk_fpo']

class SupplierCustomerDetailsSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(source='id', read_only=True)
    class Meta:
        model = CustomerDetails
        fields = ['customer_id','buyer_name', 'mobile_no', 'address','fk_supplier']

class ProductSaleSerializer(serializers.ModelSerializer):
    sale_id=serializers.IntegerField(source='id',read_only=True)
    product_name = serializers.CharField(source='fk_invent.fk_product.productName', read_only=True)
    remaining_stock = serializers.IntegerField(source='fk_invent.stock', read_only=True)
    
    class Meta:
        model = ProductSale
        fields = ['sale_id', 'product_name', 'final_price', 'remaining_stock']

class FPOSalesRecordItemSerializer(serializers.ModelSerializer):
    salesrecord_id=serializers.IntegerField(source='id',read_only=True)
    class Meta:
        model = SalesRecordItem
        fields = ['salesrecord_id','name', 'quantity', 'total_amount', 'fk_fpo', 'sales_date', 'product_name', 'category', 'fk_fposupplier_id',
                  ]
class SupplierSalesRecordItemSerializer(serializers.ModelSerializer):
    salesrecord_id=serializers.IntegerField(source='id',read_only=True)
    class Meta:
        model = SalesRecordItem
        fields = ['salesrecord_id','name', 'quantity', 'total_amount','sales_date', 'product_name', 'category', 
                  'fk_supplier','fk_inputsupplier_id']
class MonthlySalesSerializer(serializers.ModelSerializer):
    salesrecord_id=serializers.IntegerField(source='id')
    class Meta:
        model=SalesRecordItem
        fields=['salesrecord_id','total_amount','sales_date']   
################---------------------------Inventory Stock Status---------------------------################
def format_inventory_details(inventory_items):
    """Helper function to format inventory details."""
    return [{
        'inventory_id': item.id,
        'product_id': item.fk_product.id if item.fk_product else None,
        'productname': item.fk_product.productName if item.fk_product else None,
        'productytpe': item.fk_product.fk_productype.product_type if item.fk_product else None,
        'expiry_date':item.fk_product.expiry_date if item.fk_product else None,
        'stock': item.stock,
        'stock_status': item.stock_status()
    } for item in inventory_items]

#######################-----------------Getall farmers Pagination-----------------############
class FarmersAllPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size'

class FarmerProfileSerializer(serializers.ModelSerializer):
    farmer_id = serializers.IntegerField(source='id')
    farmer_name = serializers.CharField(source='name')
    farmer_mobile = serializers.CharField(source='mobile')
    farmer_district = serializers.CharField(source='district')
    farmer_village = serializers.CharField(source='village')
    farmer_block = serializers.CharField(source='block')
    created_at = serializers.DateTimeField()

    class Meta:
        model = FarmerProfile
        fields = ['farmer_id', 'farmer_name', 'farmer_mobile', 'farmer_district', 'farmer_village', 'farmer_block', 'created_at']

##############################------------------------GET ALL Products Serializer----------------------############
class GetallProductPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size'
    max_page_size = 100 

#####################-------------------------------GET ALL INventory---------------------------###############
class GetallInventoryPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size'
    max_page_size = 100 

#################################----------------------GET ALL SALES ------------------------#####################
class GetallSalesPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size'
    max_page_size = 100 

class CropMapperSerializer(serializers.ModelSerializer):
    crop_id = serializers.IntegerField(source='id')
    name = serializers.CharField(source='eng_crop.crop_name', read_only=True)
    class Meta:
        model = CropMapper
        fields = ['crop_id', 'name']


class CropVarietySerializer(serializers.ModelSerializer):
    variety_id = serializers.IntegerField(source='id')
    name = serializers.CharField(source='eng_name', read_only=True)
    class Meta:
        model = CropVariety
        fields = ['variety_id', 'name']