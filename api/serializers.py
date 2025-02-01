from django.contrib.auth.models import User
from rest_framework import serializers
from .models import UserProfile,CustomUser,BackerProfile, CreatorProfile
import hashlib
from rest_framework import serializers
from .models import Project
from rest_framework import serializers
import hashlib
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile, BackerProfile, CreatorProfile
from rest_framework import serializers
from .models import CustomUser
from .models import Contribution
from rest_framework import serializers
from .models import Contribution
from .models import ChatReason,Message
from django.utils.timezone import now

class ChatReasonSerializer(serializers.ModelSerializer):
    project_title = serializers.ReadOnlyField(source='project.title')

    class Meta:
        model = ChatReason
        fields = ['id', 'reason', 'user', 'project', 'project_title', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']



class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.ReadOnlyField(source='sender.username')
    receiver_username = serializers.ReadOnlyField(source='receiver.username')
    reason_display = serializers.ReadOnlyField(source='reason.reason')
    parent_message_id = serializers.PrimaryKeyRelatedField(queryset=Message.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'sender_username', 'receiver', 'receiver_username',
            'content', 'created_at', 'reason', 'reason_display', 'parent_message_id', 'read'
        ]
        read_only_fields = ['id', 'created_at', 'sender', 'receiver']




class ContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contribution
        fields = '__all__'

    def create(self, validated_data):
        verified = self.context.get('verified', False)
        amount = validated_data.get('amount', 0)
        platform_fee = validated_data.get('platform_fee')
        if platform_fee is None:
            raise serializers.ValidationError("Platform fee calculation failed")
        validated_data['verified'] = verified
        validated_data['platform_fee'] = round(float(platform_fee), 6)
        print("Saving with platform fee:", validated_data['platform_fee'])
        return Contribution.objects.create(**validated_data)



class ProjectSerializer(serializers.ModelSerializer):
    creator_wallet_address = serializers.SerializerMethodField()
    creator = serializers.StringRelatedField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'funding_goal', 'current_funding',
                  'deadline', 'creator', 'files', 'creator_wallet_address', 'status', 'is_expired']

        read_only_fields = ['creator', 'status', 'is_expired']

    def get_creator_wallet_address(self, obj):
        """Retrieve the wallet address from the creator's profile."""
        user_profile = getattr(obj.creator, 'userprofile', None)
        return user_profile.wallet_address if user_profile else "No Wallet Address"

    def get_is_expired(self, obj):
        """Return whether the project is expired or not."""
        return obj.deadline < now()



CustomUser = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
    contact_address = serializers.CharField(required=True)
    national_id = serializers.FileField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=True)
    wallet_address = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)

    def hash_wallet_address(self, wallet_address):
        return hashlib.sha256(wallet_address.encode('utf-8')).hexdigest()

    def validate(self, data):
        role = data.get('role')
        wallet_address = data.get('wallet_address')
        username = data.get('username')
        email = data.get('email')

        if CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "This username is already taken."})


        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "This email is already registered."})

        if role == 'creator' and not wallet_address:
            raise serializers.ValidationError({"wallet_address": "Creators must provide a wallet address."})

        if wallet_address:
            hashed_wallet_address = self.hash_wallet_address(wallet_address)
            if CustomUser.objects.filter(wallet_address=hashed_wallet_address).exists():
                raise serializers.ValidationError({"wallet_address": "This wallet address is already in use."})

        return data

    def create(self, validated_data):
        role = validated_data.get('role')
        wallet_address = validated_data.get('wallet_address')


        hashed_wallet_address = self.hash_wallet_address(wallet_address) if wallet_address else None

        user_data = {
            'username': validated_data['username'],
            'email': validated_data['email'],
            'wallet_address': hashed_wallet_address,
            'first_name': validated_data['first_name'],
            'last_name': validated_data['last_name']
        }


        user = CustomUser.objects.create_user(**user_data, password=validated_data['password'])


        user_profile = UserProfile.objects.create(
            user=user,
            role=role,
            wallet_address=wallet_address if role == 'creator' else '',
            national_id=validated_data.get('national_id', None),
            contact_address=validated_data.get('contact_address', None)
        )


        if role == 'backer':
            BackerProfile.objects.create(user=user_profile.user)
        elif role == 'creator':
            CreatorProfile.objects.create(user=user_profile.user)

        return user_profile

    class Meta:
        model = UserProfile
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'role', 'wallet_address', 'national_id', 'contact_address']


class RegisterSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=True)
    contact_address = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    national_id = serializers.FileField(required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'role', 'contact_address', 'first_name', 'last_name', 'national_id']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def create(self, validated_data):

        role = validated_data.pop('role')
        contact_address = validated_data.pop('contact_address')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        national_id = validated_data.pop('national_id')

        # Create the CustomUser instance
        user = CustomUser(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(validated_data['password'])
        user.save()


        user_profile_data = {
            'role': role,
            'contact_address': contact_address,
            'national_id': national_id,
            'user': user
        }
        user_profile = UserProfile.objects.create(**user_profile_data)


        if role == 'backer':
            BackerProfile.objects.create(user=user_profile.user)
        elif role == 'creator':
            CreatorProfile.objects.create(user=user_profile.user)

        return user_profile


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    contact_address = serializers.CharField(required=False)

    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'contact_address']

    def validate(self, data):

        if 'wallet_address' in data or 'national_id' in data:
            raise serializers.ValidationError({"error": "You cannot update wallet address or national ID."})
        return data
