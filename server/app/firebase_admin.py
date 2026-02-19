"""
Firebase Admin SDK initialization and token verification.
"""

import os
import logging
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, auth
from dotenv import load_dotenv

load_dotenv(override=True)
logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
_firebase_app: Optional[firebase_admin.App] = None


def initialize_firebase() -> Optional[firebase_admin.App]:
    """Initialize Firebase Admin SDK with service account credentials."""
    global _firebase_app

    if _firebase_app is not None:
        return _firebase_app

    try:
        # Check for service account file path
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')

        if service_account_path and os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin initialized with service account file")
        else:
            # Try using default credentials (for Cloud Run, etc.)
            try:
                _firebase_app = firebase_admin.initialize_app()
                logger.info("Firebase Admin initialized with default credentials")
            except Exception:
                logger.warning("Firebase Admin not initialized - no credentials found")
                return None

        return _firebase_app

    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin: {e}")
        return None


def verify_token(id_token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a Firebase ID token and return the decoded claims.

    Args:
        id_token: The Firebase ID token to verify

    Returns:
        Decoded token claims if valid, None if invalid
    """
    if not _firebase_app:
        initialize_firebase()

    if not _firebase_app:
        logger.warning("Firebase Admin not initialized, cannot verify token")
        return None

    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except auth.ExpiredIdTokenError:
        logger.warning("Token has expired")
        return None
    except auth.RevokedIdTokenError:
        logger.warning("Token has been revoked")
        return None
    except auth.InvalidIdTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


def get_user_by_uid(uid: str) -> Optional[auth.UserRecord]:
    """Get Firebase user by UID."""
    if not _firebase_app:
        initialize_firebase()

    if not _firebase_app:
        return None

    try:
        return auth.get_user(uid)
    except auth.UserNotFoundError:
        return None
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None


# Initialize on import
initialize_firebase()
