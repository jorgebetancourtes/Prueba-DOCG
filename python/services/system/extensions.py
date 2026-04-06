from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect
from cryptography.fernet import Fernet

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[]
)

csrf = CSRFProtect()
