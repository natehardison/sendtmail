class Nominal(object):
    def __init__(self, value):
        self._value = value

    def __eq__(self, other):
        return self._value == other.value

    def __ne__(self, other):
        return self._value != other.value

    def __hash__(self):
        return hash(self._value)

    def __str__(self):
        return self._value

    @property
    def value(self):
        return self._value

class Ordinal(Nominal):
    def __lt__(self, other):
        return self._value < other.value

    def __le__(self, other):
        return self._value <= other.value

    def __gt__(self, other):
        return self._value > other.value

    def __ge__(self, other):
        return self._value >= other.value