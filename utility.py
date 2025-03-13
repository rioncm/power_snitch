from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    return generate_password_hash(password)

def check_password(password, hashed_password):
    return check_password_hash(hashed_password, password)


if __name__ == "__main__":
    password = "password"
    hashed_password = hash_password(password)
    print(f"Hashed password: {hashed_password}")
    print(f"Check password: {check_password(password, hashed_password)}")
