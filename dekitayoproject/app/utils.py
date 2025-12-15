import secrets
import string

# 招待コード作成 #
def generate_invite_code(length=6):
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))