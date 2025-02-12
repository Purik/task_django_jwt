from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema

from .shemas import OTPConfirmSchema, OTPCreateSchema 


class OTPEndpoint(viewsets.GenericViewSet):
    
    def get_serializer_class(self):
        if self.action == 'generate':
            return OTPCreateSchema
        elif self.action == 'confirm':
            return OTPConfirmSchema
        
    @extend_schema(tags=['OTP'])
    @action(methods=['POST'], detail=False)
    def generate(self, request: Request) -> Response:
        ...
        
    @extend_schema(tags=['OTP'])
    @action(methods=['POST'], detail=True)
    def confirm(self, request: Request, pk: str = None) -> Response:
        ...