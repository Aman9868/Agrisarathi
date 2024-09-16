from django.urls import path
from .views import *
from .data import *
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
urlpatterns = [
    path('UserRegistration',UserRegistration.as_view(),name='UserRegistration'),
    path('UserLogin',UserLogin.as_view(), name='UserLogin'),
    path('UserLogout',UserLogout.as_view(), name='UserLogout'),
    path('UserProfileView',UserProfileView.as_view(), name='UserProfileView'),
    path('UpdateProfile',UpdateProfile.as_view(), name='UpdateProfile'),
    path('UpdateProfilePicture',UpdateProfilePicture.as_view(), name='UpdateProfilePicture'),
    path('ResetPasssword',ResetPasssword.as_view(), name='ResetPasssword'),
    path('FarmerByFPO',FarmerByFPO.as_view(), name='FarmerByFPO'), #add framer+delete framers,
    path('AddFarmerCsv',AddFarmerCsv.as_view(), name='AddFarmerCsv'),
    path('api/token/refresh/',TokenRefreshView.as_view(), name='token_refresh'),
    path('GetSingleFarmerDetailsbyFPO',GetSingleFarmerDetailsbyFPO.as_view(), name='GetSingleFarmerDetailsbyFPO'),
    path('GetAllFarmerbyFPO',GetAllFarmerbyFPO.as_view(), name='GetAllFarmerbyFPO'),
    path('GetProductDetailsByFPOSupplier',GetProductDetailsByFPOSupplier.as_view(), name='GetProductDetailsByFPOSupplier'),
    path('ADDProductDetailsCSV',ADDProductDetailsCSV.as_view(), name='ADDProductDetailsCSV'),
    # add product supplier/fpo   # get single productinfo supplier/fpo # del product info # update
    path('ProductDetailsAddGetDelUpdate',ProductDetailsAddGetDelUpdate.as_view(),name='ProductDetailsAddGetDelUpdate'),
    path('PurchaseInfo',PurchaseInfo.as_view(),name='PurchaseInfo'), 
    path('GetallProductsInfo',GetallProductsInfo.as_view(),name='GetallProductsInfo'),
    path('AddMeasurements',AddMeasurements,name='AddMeasurements'),
    path('GetMeasurements',GetMeasurements.as_view(),name='GetMeasurements'),
    path('InventorySection',InventorySection.as_view(),name='InventorySection'), # inventiry get/update
    path('AddGetSales',AddGetSales.as_view(),name='AddGetSales'), # add sales and get sales info
    path('InventoryInoutStock',InventoryInoutStock.as_view(),name='InventoryInoutStock'), # instock and oytstock
    path('CheckCustomerisFarmerornot',CheckCustomerisFarmerornot.as_view(),name='CheckCustomerisFarmerornot'),
    path('CheckBuyerisFarmerorNot',CheckBuyerisFarmerorNot.as_view(),name='CheckBuyerisFarmerorNot'),
    path('GetallFPOCrops',GetallFPOCrops.as_view(),name='GetallFPOCrops'),      
    path('GetFPOCropVariety',GetFPOCropVariety.as_view(),name='GetFPOCropVariety'), 
    path('MonthlySales',MonthlySales.as_view(),name='MonthlySales'),
    path('TotalSales',TotalSales.as_view(),name='TotalSales'),
    path('GetAllProductsFponSupplier',GetAllProductsFponSupplier.as_view(),name='GetAllProductsFponSupplier'),
    path('GetallFPOGovtSchemes',GetallFPOGovtSchemes.as_view(),name='GetAllFPOGovtSchemes'),      
    path('FPOGovtSchemesbyID',FPOGovtSchemesbyID.as_view(),name='FPOGovtSchemesbyID'),                                                                                                                                                    
                                                                                    
]