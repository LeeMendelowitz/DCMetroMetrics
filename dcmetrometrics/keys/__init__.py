from .key_utils import keyModuleError, MissingKeyError

try:
    from .keys import MetroEscalatorKeys,\
                      MetroElevatorKeys,\
                      HotCarKeys,\
                      WUNDERGROUND_API_KEY,\
                      WMATA_API_KEY,\
                      MissingKeyError,\
                      TwitterKeyError

except ImportError as e:

    # The key module is not properly defined.
    keyModuleError()

