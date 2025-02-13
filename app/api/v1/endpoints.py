import json
import time
from secrets import token_hex
from datetime import datetime, timedelta

import jwt
from django.conf import settings
from django.core.cache import caches
from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError, AuthenticationFailed
from drf_spectacular.utils import extend_schema

from account.models import RefreshToken, Account

from .shemas import OTPConfirmSchema, OTPCreateSchema 


class OTPEndpoint(viewsets.ViewSet):
    
    authentication_classes = [JWTAuthentication]
    
    _secret_nbytes = 16
    _expiration_sec = 300  # 5 min
    _algorithm = 'HS256'
    
    # Это надо вынести в settings но для Демо нагляднее тут
    _access_token_ttl = 60*60  # 1 hour
    _refresh_token_ttl = 60*60*24  # 1 day
    
    def get_serializer_class(self):
        if self.action == 'generate':
            return OTPCreateSchema
        elif self.action == 'confirm':
            return OTPConfirmSchema
        
    @extend_schema(tags=['OTP'])
    @action(methods=['POST'], detail=False)
    def generate(self, request: Request) -> Response:
        data = self._validate(request.data)
        
        confirm_id = token_hex(nbytes=self._secret_nbytes)
        otp_code = self._generate_otp_code()
        caches['otp'].set(
            key=confirm_id, 
            value=json.dumps(
                {
                    'code': otp_code,
                    'address': data['address']
                }
            ), 
            timeout=self._expiration_sec
        )
        
        return Response(
            data={
                'confirm_id': confirm_id,
                'ttl': self._expiration_sec
            }
        )
        
    @extend_schema(tags=['OTP'])
    @action(methods=['POST'], detail=True)
    def confirm(self, request: Request, pk: str = None) -> Response:
        data = self._validate(request.data)
        
        confirm_id = pk
        
        value = caches['otp'].get(confirm_id)
        if value is None:
            raise NotFound(detail='OTP code expired or invalid!')
        
        value = json.loads(value)
        otp_code = value['code']
        address = value['address']
        if otp_code != data.get('code'):
            raise ValidationError(detail='OTP code invalid!')
        
        # Создаем пару токенов
        payload = {}
        access_token = self._generate_jwt_token(payload, ttl=self._access_token_ttl)
        refresh_token = self._generate_jwt_token(payload, ttl=self._refresh_token_ttl)
        
        # Access Token держим в кеше, чтобы лишний раз не нагружать БД частыми запросами 
        caches['access_token'].set(
            key=access_token, value='*', timeout=self._access_token_ttl
        )
        # Refresh token держим в базе в захешированном виде
        account = Account.objects.ensure_exists(address)
        RefreshToken.objects.register(
            token=refresh_token, 
            payload=payload, 
            account=account, 
            ttl=self._refresh_token_ttl
        )
        
        #  OTP нам больше не нужен
        caches['otp'].delete(confirm_id)
        
        return Response(
            data={
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'bearer'
            }
        )
        
    @extend_schema(tags=['Auth'])
    @action(methods=['GET'], detail=False)
    def check_access(self, request: Request) -> Response:
        if request.user:
            return Response(
                data={
                    'username': request.user.username
                }
            )
        else:
            raise AuthenticationFailed
    
    def _validate(self, data) -> dict:
        serializer = self.get_serializer_class()(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data
        
    @classmethod
    def _generate_otp_code(cls, digits: int = 4) -> str:
        # Конечно же это для тестов
        return '0' * digits
    
    def _generate_jwt_token(self, payload: dict, ttl: int):
        """
        Генерирует веб-токен JSON, в котором хранится идентификатор этого
        пользователя, срок действия токена составляет 1 день от создания
        """
        exp = time.time() + ttl

        token = jwt.encode(
            payload={
                **payload,
                **{'exp': int(exp)}
            }, 
            headers={
                'typ': 'JWT',
                'alg': self._algorithm
            },
            key=settings.SECRET_KEY, 
            algorithm=self._algorithm
        )

        return token
