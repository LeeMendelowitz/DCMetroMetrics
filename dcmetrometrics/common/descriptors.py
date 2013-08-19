# descriptors.py
# Defines class descriptors
#
# setOnce: descriptor for a class attribute that can be set
#          once, and then is read-only thereafter.
#
# computeOnce: descriptor for a class attribute that should be
#              computed once on the first access. All future accesses
#              returned the computed value. This is similar to using
#              the @property decorator.


######################################################
# Descriptor to define a read only attribute
# which can only be set once.
class setOnce(object):
    def __init__(self, name, default = None):
        self.name = "_" + name # Need leading underscore
        self.default = default

    def __get__(self, instance, cls):
        if not instance:
            raise AttributeError('Can only access property through instance')
        return getattr(instance, self.name, self.default)

    # Only allow the attribute to be set once
    def __set__(self, instance, value):
        if not getattr(instance, self.name, None):
            setattr(instance, self.name, value)
            return
        raise AttributeError('Attribute is read-only.')

    def __delete__(self, instance):
        raise AttributeError('Attribute is read-only')

######################################################
# Descriptor to define a read only attribute
# which should only be computed once on the first access.
#
# The advantage of using this descriptor is that if the
# class attribute is never used, it is never computed, and
# if it is used, it is only computed once.
class computeOnce(object):
    count = 0 # used to assign a unique variable name to store
              # value within an instance

    def __init__(self, fget):
        self.name = "_" + 'computeOnce%i'%computeOnce.count
        computeOnce.count = computeOnce.count + 1
        self.fget = fget

    def __get__(self, instance, cls):
        if not instance:
            raise AttributeError('Can only access property through instance')

        retVal = getattr(instance, self.name, None)
        if retVal is None:
            retVal = self.fget(instance)
            setattr(instance, self.name, retVal)
        return retVal

    def __set__(self, instance, value):
        raise AttributeError('Attribute is read-only.')

    def __delete__(self, instance):
        raise AttributeError('Attribute is read-only')
