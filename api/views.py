from rest_framework import serializers
from datetime import datetime, timedelta
import hashlib
import jwt
from base64 import b64decode
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render
from .models import CustomUser, Message
from .serializers import UserProfileSerializer,ContributionSerializer
from rest_framework import generics
from .models import Project
from .serializers import ProjectSerializer,MessageSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Project, Contribution,UserProfile, ChatReason
from solana.rpc.api import Client
from solana.publickey import PublicKey
import json
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import ContributionSerializer, UserProfileUpdateSerializer
from solana.rpc.api import Client
from .serializers import ChatReasonSerializer
from rest_framework.permissions import IsAuthenticated

class ChatReasonListCreateView(generics.ListCreateAPIView):
    queryset = ChatReason.objects.all()
    serializer_class = ChatReasonSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all().order_by('-created_at')
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Automatically set the sender to the current logged-in user
        sender = self.request.user

        receiver = CustomUser.objects.get(username='paul')

        serializer.save(sender=sender, receiver=receiver)


class UserprofileUpdateView(generics.RetrieveUpdateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileUpdateSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self):
        return self.request.user.userprofile


SOLANA_RPC_URL = "https://api.devnet.solana.com"
client = Client(SOLANA_RPC_URL)

@api_view(['POST'])
def contribute(request):
    if request.method == 'POST':
        transaction_hash = request.data.get('transaction_hash')


        response = client.get_transaction(transaction_hash)

        if response.get('result') is None:
            return Response({"error": "Transaction not found."}, status=status.HTTP_400_BAD_REQUEST)


        if not response['result'].get('meta'):
            data = request.data.copy()
            data['payment_status'] = 'pending'


            context = {'verified': False}
            serializer = ContributionSerializer(data=data, context=context)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


        if response['result']['meta']['err'] is None:
            amount = extract_amount_from_transaction(response['result'])
            if amount is None:
                return Response({"error": "Amount not found in the transaction."}, status=status.HTTP_400_BAD_REQUEST)


            platform_fee = calculate_fee(amount)

            data = request.data.copy()
            data['amount'] = amount
            data['platform_fee'] = platform_fee
            data['payment_status'] = 'completed'


            context = {'verified': True}
            serializer = ContributionSerializer(data=data, context=context)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({"error": f"Transaction failed: {response['result']['meta']['err']}"}, status=status.HTTP_400_BAD_REQUEST)


def extract_amount_from_transaction(transaction_data):
    try:

        pre_balances = transaction_data['meta']['preBalances']
        post_balances = transaction_data['meta']['postBalances']

        print("Pre Balances:", pre_balances)
        print("Post Balances:", post_balances)


        if len(pre_balances) > 1 and len(post_balances) > 1:

            pre_balance = pre_balances[1]
            post_balance = post_balances[1]


            amount = post_balance - pre_balance
            print("Calculated Amount (in lamports):", amount)


            if amount > 0:

                sol_amount = amount / 1_000_000_000
                print("Calculated Amount (in SOL):", sol_amount)
                return sol_amount
            else:
                print("No increase in balance.")
                return None
        else:
            print("Invalid balance data.")
            return None

    except KeyError as e:
        print(f"Error extracting amount: Missing key {e}")
        return None

    except Exception as e:

        print(f"Unexpected error: {e}")
        return None

from decimal import Decimal

def calculate_fee(amount):
    fee_percentage = Decimal('0.0009')  # Use Decimal for precision
    platform_fee = Decimal(str(amount)) * fee_percentage  # Convert amount to Decimal
    return platform_fee.quantize(Decimal('0.000000'))

class ProjectListCreateView(generics.ListCreateAPIView):
    queryset = Project.objects.filter(status='approved')
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        if Project.objects.filter(creator=self.request.user).exists():
            raise serializers.ValidationError("Sorry! you cannot create more than one project")
        serializer.save(creator=self.request.user, status='pending')


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        login_data = request.data
        username = login_data.get('username')
        wallet_address = login_data.get('wallet_address')
        password = login_data.get('password')
        user = None


        if wallet_address:
            try:
                user = CustomUser.objects.get(wallet_address=wallet_address)


                if user.userprofile.role != 'creator':
                    return Response(
                        {"error": "Only creators can log in using wallet address."},
                        status=status.HTTP_400_BAD_REQUEST
                    )


                user.userprofile.wallet_verified = True
                user.userprofile.save()

            except CustomUser.DoesNotExist:
                return Response({"error": "Invalid wallet address."}, status=status.HTTP_400_BAD_REQUEST)


        elif username and password:
            try:
                user = CustomUser.objects.get(username=username)


                if user.userprofile.role == 'creator' and not user.userprofile.wallet_verified:
                    return Response(
                        {"error": "Creators must log in with their wallet address first."},
                        status=status.HTTP_400_BAD_REQUEST
                    )


                user = authenticate(request, username=username, password=password)
                if not user:
                    return Response({"error": "Invalid username or password."}, status=status.HTTP_400_BAD_REQUEST)

            except CustomUser.DoesNotExist:
                return Response({"error": "Invalid username."}, status=status.HTTP_400_BAD_REQUEST)


        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Login successful",
                "username": user.username,
                "role": user.userprofile.role,
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            }, status=status.HTTP_200_OK)

        return Response({"error": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)


CustomUser = get_user_model()

class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserProfileSerializer(data=request.data)

        if serializer.is_valid():
            try:
                user_profile = serializer.save()
                user_role = user_profile.role.lower()
                recipient_email = user_profile.user.email
                username = user_profile.user.username


                if user_role == 'creator':
                    wallet_address = user_profile.user.wallet_address if hasattr(user_profile.user,
                                                                                 'wallet_address') else 'N/A'
                    email_subject = "Welcome to Our Service!"
                    email_message = (
                        f"Hi {user_profile.user.username},\n\n"
                        f"Thank you for registering as a creator! Here is your wallet address:\n"
                        f"{wallet_address}\n\n"
                        "DON'T SHARE! Keep this address only for login purposes."
                    )
                elif user_role == 'backer':
                    email_subject = "Welcome to Our Service!"
                    email_message = (
                        f"Hi {user_profile.user.username},\n\n"
                        "Thank you for joining us as a backer! We appreciate your support.\n\n"
                        "Feel free to explore our platform and support your favorite projects."
                    )
                else:
                    email_subject = "Welcome to Our Service!"
                    email_message = f"Hi {user_profile.user.username},\n\nThank you for registering!"

                send_mail(
                    subject=email_subject,
                    message=email_message,
                    from_email="no-reply@yourdomain.com",
                    recipient_list=[user_profile.user.email],
                    fail_silently=False,
                )
            except Exception as e:
                return Response({"error": f"Failed to send email: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            national_id_url = user_profile.national_id.url if user_profile.national_id else 'No ID uploaded'

            return Response(
                {
                    "message": "User registered successfully. An email has been sent.",
                    "user_profile": {
                        "username": user_profile.user.username,
                        "role": user_profile.role,
                        "wallet_address": user_profile.wallet_address if user_profile.wallet_address else 'N/A',
                        "contact_address": user_profile.contact_address,
                        "national_id": national_id_url
                    }
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)