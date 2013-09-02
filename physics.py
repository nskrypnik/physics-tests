
from kivy.utils import platform

if platform() in ('ios', 'android'):
    # use cymunk for mobile platforms 
    import cymunk as phy
else:
    import pymunk as phy