import json

class ComplexEncoder(json.JSONEncoder):

    def default(self, o):
        """
        Args:
            o (object): An arbitrary object that must be converted to a dict
        """
        try:
            # Check if the object has the "as_dict" function
            if callable(getattr(o, "as_dict", None)):
                return o.as_dict()
            # Check if the object has an overidden "__repr__"
            if type(o).__repr__ != object.__repr__:
                return repr(o)
            return {key: self.encode(element) for key, element in vars(o).items()}
        except Exception:
            return super().default(o)