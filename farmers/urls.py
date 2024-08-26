from django.urls import path
from .views import *

urlpatterns = [
    path('FarmerLogin',FarmerLogin.as_view(), name='FarmerLogin'),
    path('VerifyOTP',VerifyOTP.as_view(), name='VerifyOTP'),
    path('FarmerLogout',FarmerLogout.as_view(), name='FarmerLogout'),
    ################---------------------Get Farmer ALL Land INfo & Add Farm Land by Farmer------------------#########
    path('FarmerAllLandsInfo',FarmerAddGetallLandInfo.as_view(),name='FarmerAllLandsInfo'),

    ########---Get Farmer Single Land Details ,Update Farmer and Land Details-------##
    path('FarmerDetailsGetUpdate',FarmerDetailsGetUpdate.as_view(),name='FarmerDetailsGetUpdate'),

    #####################-----------------Send Otp to Users Email and Verfy it successfully with is_verified True-----##
    path('SendEmailVerification',SendEmailVerification.as_view(),name='SendEmailVerification'),
    path('VerifyEmail',VerifyEmail.as_view(),name='VerifyEmail'),
    path('FarmerFpoPart',FarmerFpoPart.as_view(),name='FarmerFpoPart'),

    ##################----------------------Get Inital Screen Crops------------------################
    path('GetInitialScreenCrops',GetInitialScreenCrops.as_view(), name='GetInitialScreenCrops'),
    #################--------------------Service Providers----------------------##############
    path('ServiceProviderList',ServiceProviderList.as_view(),name='ServiceProviderList'),

    ##################----------------------Govt Schemes---------------------#######
    path('GetallGovtSchemes',GetallGovtSchemes.as_view(),name='GetallGovtSchemes'),
    path('GovtSchemesbyID',GovtSchemesbyID.as_view(),name='GovtSchemesbyID'),
    ####--------------------------------------Fertilizers Calculators------------------########
    path('Fertilizerswithtest',Fertilizerswithtest.as_view(),name='Fertilizerswithtest'),
    path('AdvanceFertilizercalculator',AdvanceFertilizercalculator.as_view(),name='AdvanceFertilizercalculator'),

    ##############----------------------Disease Detection---------------#######
    path('DetectDiseaseAPIView',DetectDiseaseAPIView.as_view(),name='DetectDiseaseAPIView'),
    path('GetSingleDiagnosisReport',GetSingleDiagnosisReport.as_view(),name='GetSingleDiagnosisReport'),
    path('GetDiagnosisReport',GetDiagnosisReport.as_view(),name='GetDiagnosisReport'),
    path('GetDiseaseVideos',GetDiseaseVideos.as_view(), name='GetDiseaseVideos'),

    #####################-----------------COMMUNITY------------######################
    path('AddCommunityPost',AddCommunityPost.as_view(), name='AddCommunityPost'),
    path('CommentOnPost',CommentOnPost.as_view(), name='CommentOnPost'),
    path('ReplyOnPostComment',ReplyOnPostComment.as_view(), name='ReplyOnPostComment'),
    path('LikeUnlikePost',LikeUnlikePost.as_view(), name='LikeUnlikePost'),
    path('CommunityPostsList',CommunityPostsList.as_view(), name='CommunityPostsList'),

    ##############----------------------CROP SUGGESTION(Get crop details and  Post for Crop Suggest)------------------##############
    path('CropSuggestion',CropSuggestion.as_view(), name='CropSuggestion'),
    path('AddSuggcropcsv',AddSuggcropcsv,name='AddSuggcropcsv'),

    ############----------------------Adding Pop Data-----------------------#################
    path('AddPOP',AddPOP,name='AddPOP'),

    ###################-------------------VEGETABLE POP------------------------##########
    path('VegetableStagesAPIView',VegetableStagesAPIView.as_view(), name='VegetableStagesAPIView'),
    path('MarkVegetableStageCompleteAPIView',MarkVegetableStageCompleteAPIView.as_view(), name='MarkVegetableStageCompleteAPIView'),
    path('VegetableProgressAPIView',VegetableProgressAPIView.as_view(), name='VegetableProgressAPIView'),
    path('GetVegetablePopNotification',GetVegetablePopNotification.as_view(), name='GetVegetablePopNotification'),

    #########################------------------Spices POP----------------------####################
    path('SpicesStagesAPIView',SpicesStagesAPIView.as_view(), name='SpicesStagesAPIView'),
    path('MarkSpicesStageCompleteAPIView',MarkSpiceStageCompleteAPIView.as_view(), name='MarkSpicesStageCompleteAPIView'),
    path('SpicesProgressAPIView',SpicesProgressAPIView.as_view(), name='SpicesProgressAPIView'),
    path('GetSpicesPopNotification',GetSpicesPopNotification.as_view(), name='GetSpicesPopNotification'),

    ########---------------------------------Cereals POP---------------------######################
    path('CerealStagesAPIView',CerealStagesAPIView.as_view(), name='CerealStagesAPIView'),
    path('MarkCerealStageCompleteAPIView',MarkCerealStageCompleteAPIView.as_view(), name='MarkCerealStageCompleteAPIView'),
    path('GetCerealsPopNotification',GetCerealsPopNotification.as_view(), name='GetCerealsPopNotification'),
    path('CerealProgressAPIView',CerealProgressAPIView.as_view(), name='CerealProgressAPIView'),

    ########################--------------FRUITS POP---------------------------################
    path('GetFruitsPopAPIView',GetFruitsPopAPIView.as_view(), name='GetFruitsPopAPIView'),
    








    ##################---------------------Farmer Rating and Comment on Shop-------------#########
    path('FarmerCommentonShop',FarmerCommentonShop.as_view(),name='FarmerCommentonShop'),
    #############--------------------------Show all Crop Types----------------#############
    path('CropTypes',CropTypes.as_view(), name='CropTypes')
    # Add more URL patterns here
]