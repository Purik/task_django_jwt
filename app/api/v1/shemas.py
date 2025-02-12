from rest_framework.serializers import Serializer, CharField, ChoiceField


class OTPCreateSchema(Serializer):
    
    # адрес, куда посылаем одноразовый код
    address = CharField(max_length=128)
    
    # метод доставки
    method = ChoiceField(choices=['phone', 'email'])
    
    # ID OTP заявки
    confirm_id = CharField(read_only=True)

    
class OTPConfirmSchema(Serializer):
    
    # одноразовый код
    code = CharField(max_length=16)
