##serialziers.py
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from fponsuppliers.models import *

######################----------------------------------------FPO--------------------------###########
class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['mobile','user_type'] 

    def create_user(self, validated_data, user_type):
        user = CustomUser.objects.create_user(
            mobile=validated_data['mobile'],
            user_type=validated_data['user_type']
        )
        if user_type == 'farmer':
            FPO.objects.create(user=user, mobile=user.mobile)
        else:
            raise ValueError("Invalid user type")
        print(f"Created {user_type} user: {user}")
        return user 