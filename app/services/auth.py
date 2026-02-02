from app.models.user import User
from app.extensions import db, bcrypt
from flask_jwt_extended import create_access_token


def register_user(username, email, password):
    """
    Registers a new user.
    """
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return None, "User already exists"

    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    user = User(
        username=username,
        email=email,
        password_hash=password_hash
    )

    db.session.add(user)
    db.session.commit()

    return user, None


def login_user(email, password):
    """
    Logs in a user and returns JWT token.
    """
    user = User.query.filter_by(email=email).first()

    if not user:
        return None, "Invalid email or password"

    if not bcrypt.check_password_hash(user.password_hash, password):
        return None, "Invalid email or password"

    access_token = create_access_token(
        identity={"user_id": user.user_id}
    )

    return access_token, None
