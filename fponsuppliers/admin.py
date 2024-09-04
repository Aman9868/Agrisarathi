from django.contrib import admin
from .models import *
from django.utils.html import format_html

###################---------------------------FPO---------------------####################
@admin.register(FPO)
class FPOUserAdmin(admin.ModelAdmin):
    list_display = ('id','fpo_name','mobile','created_at','last_updated_at')


##################-----------------------------------Supplier-----------------------##########
@admin.register(Supplier)
class SupplierUserAdmin(admin.ModelAdmin):
    list_display = ('supplier_name','mobile','profile','created_at','last_updated_at')
    def display_profile(self, obj):
        if obj.profile:
            return format_html('<a href="{}" target="_blank"><img src="{}" width="100px" /></a>',  obj.profile.url,obj.profile.url)
        else:
            return '-'
    display_profile.short_description = 'Profile Picture'

@admin.register(CustomUser)
class FPOnSupplierUserAdmin(admin.ModelAdmin):
    list_display = ('id','mobile','last_login','user_type')


################--------------------------------------SHOP Details-----------------------------#######################
@admin.register(ShopDetails)
class ShopDetailsAdmin(admin.ModelAdmin):
    list_display = ('shopName', 'shopContactNo', 'city', 'fk_state','fk_fpo','fk_supplier')
    search_fields = ('shopName', 'city', 'fk_state')
    list_filter = ('fk_state', 'city', 'shop_opendays')
#################-------------------------------------FPO Busines Details-----------------------###########
@admin.register(BankBusinessDetails)
class BankBusinessDetailsAdmin(admin.ModelAdmin):
    list_display = ('fk_fpo','fk_supplier','accountholder_name','bank_name')
    list_filter = ('fk_fpo', 'fk_supplier')
###################----------------------------------Admin Product and Supplier Details------------------------#################
@admin.register(ProductDetails)
class ProductDetailsAdmin(admin.ModelAdmin):
    list_display = ('id', 'productName', 'Category', 'weight', 'price', 'manufacturerName', 'display_product_image',"measurement_type",
                    "quantity")
    list_filter = ('Category', 'manufacturerName')
    search_fields = ('productName', 'manufacturerName')

    def display_product_image(self, obj):
        if obj.product_image:
            return format_html('<a href="{}" target="_blank"><img src="{}" width="100px" /></a>', obj.product_image.url, obj.product_image.url)
        else:
            return '-'
    display_product_image.short_description = 'Product Image'

##########################----------------------------Input Suppliers------------------################
@admin.register(InputSuppliers)
class InputSuppliersAdmin(admin.ModelAdmin):
    list_display = ('purchase_date', 'fk_supplier', 'party_name', 'party_mobileno', 'party_company', 'total_amount', 'unit_price', 'fk_productype', 'quantity', 'party_gst')
    search_fields = ('party_name', 'party_company', 'party_mobileno')
    list_filter = ('purchase_date', 'fk_supplier', 'fk_productype')
#######################################---------------------------Customers Who Buy Products-------------------#########
@admin.register(CustomerDetails)
class CustomerDetailsAdmin(admin.ModelAdmin):
    list_display=('buyer_name','mobile_no','address','company_name','gst_number','created_at')

###########################--------------Inventory & Packaging-------------------------------###########################
@admin.register(InventoryDetails)
class InventoryDetailsAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_produtcname','stock','location','created_at','updated_at','fk_product')
    def get_produtcname(self, obj):
        return obj.fk_product.productName if obj.fk_product else None
    get_produtcname.short_description = 'Product Name'

    def get_filtertype(self,obj):
        return obj.fk_product.fk_productype.product_type if obj.fk_product else None
    
#################################----------------------------------Product Sales---------------------------##################
@admin.register(ProductSale)
class ProductSaleAdmin(admin.ModelAdmin):
    list_display = ('get_produtcname', 'amount', 'sales_date','final_price')
    def get_produtcname(self, obj):
        return obj.fk_invent.fk_product.productName if obj.fk_invent else None
    get_produtcname.short_description = 'Product Name'
######################--------------------------------------------Sales Record of Each Buyer---------------------------##########
@admin.register(SalesRecordItem)
class SalesRecordItemAdmin(admin.ModelAdmin):
    list_display=('display_fponame','category','quantity','total_amount','name')
    list_filter=("fk_fpo",'name')
    def display_fponame(self,obj):
        return obj.fk_fpo.fpo_name if obj.fk_fpo else None
    
##########################################---------------Product Prices--------------------------------------------------###############
@admin.register(ProductPrices)
class ProductPricesAdmin(admin.ModelAdmin):
    list_display = ('fk_product', 'purchase_price', 'unit_price', 'discount', 'final_price_unit')
    search_fields = ('fk_product__productName',)  # Assuming the ProductDetails model has a 'name' field
    list_filter = ('fk_product',)

#################################---------------------------------Product Type--------------------------------###############
@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display=('id','product_type')
###################---------------------------------------------FPO Supplers-------------------------##############
@admin.register(FPOSuppliers)
class FPOSuppliersAdmin(admin.ModelAdmin):
    list_display = ('fk_fpo', 'purchase_date', 'party_name', 'party_mobileno', 'party_company', 'total_amount', 'unit_price', 'fk_productype', 'quantity')
    search_fields = ('party_name', 'party_mobileno', 'party_company')
    list_filter = ('purchase_date', 'fk_productype')