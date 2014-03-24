from hippy.objects.resources import W_Resource


class W_StreamContext(W_Resource):

    def is_valid(self):
        return False

    def get_resource_type(self):
        return "stream-context"

