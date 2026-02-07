"""
Database handles for Firestore collections (production) or in-memory storage (mock mode).
Provides dependency injection for routers.
"""
from settings import settings
from core.types import UserInfo, BotProfile, OTP, RoundResult
import logging


class InMemoryDict:
    """
    In-memory storage that mimics FirestoreDict interface.
    Used in mock mode instead of Firestore.
    """
    def __init__(self, name: str):
        self.name = name
        self._data = {}

    def __getitem__(self, key):
        if key not in self._data:
            raise KeyError(key)
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        if key in self._data:
            del self._data[key]

    def __contains__(self, key):
        return key in self._data

    def get(self, key, default=None):
        return self._data.get(key, default)

    def find(self, filters=None):
        """
        Find items matching filters.
        Yields (key, value) tuples.
        """
        for key, value in self._data.items():
            if filters is None:
                yield key, value
            else:
                match = True
                for f in filters:
                    field_name = f.field if hasattr(f, 'field') else f.get('field')
                    field_value = f.value if hasattr(f, 'value') else f.get('value')

                    if hasattr(value, field_name):
                        obj_value = getattr(value, field_name)
                        if hasattr(obj_value, 'value'):
                            obj_value = obj_value.value
                        if obj_value != field_value:
                            match = False
                            break
                    else:
                        match = False
                        break
                if match:
                    yield key, value

    def find_ids(self, filters=None):
        """Yield keys matching filters."""
        for key, value in self.find(filters):
            yield key

    def find_data(self, filters=None):
        """Yield values matching filters."""
        for key, value in self.find(filters):
            yield value

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def __len__(self):
        return len(self._data)

    def update(self, key, updates: dict):
        """Update specific fields of an object."""
        if key not in self._data:
            raise KeyError(key)
        obj = self._data[key]
        if hasattr(obj, 'model_dump'):
            data = obj.model_dump()
            data.update(updates)
            self._data[key] = obj.__class__(**data)
        elif isinstance(obj, dict):
            obj.update(updates)


# Global database handles
users_data = None
candidate_users_data = None
bots_data = None
otps_data = None
rounds_data = None


def get_db_handle_users():
    global users_data
    return users_data


def get_db_handle_candidate_users():
    global candidate_users_data
    return candidate_users_data


def get_db_handle_bots():
    global bots_data
    return bots_data


def get_db_handle_otps():
    global otps_data
    return otps_data


def get_db_handle_rounds():
    global rounds_data
    return rounds_data


def initialize():
    """Initialize all database connections (Firestore or in-memory based on mock_mode)"""
    global users_data, candidate_users_data, bots_data, otps_data, rounds_data

    if settings.mock_mode:
        _initialize_mock_storage()
    else:
        _initialize_firestore()


def _initialize_mock_storage():
    """Initialize in-memory storage for mock mode"""
    global users_data, candidate_users_data, bots_data, otps_data, rounds_data

    logging.info("Initializing in-memory storage for MOCK MODE")

    users_data = InMemoryDict("Users")
    candidate_users_data = InMemoryDict("CandidateUsers")
    bots_data = InMemoryDict("Bots")
    otps_data = InMemoryDict("OTPs")
    rounds_data = InMemoryDict("Rounds")

    logging.info("In-memory storage initialized")


def _initialize_firestore():
    """Initialize Firestore connections for production"""
    global users_data, candidate_users_data, bots_data, otps_data, rounds_data

    from core.firestore_dict import FirestoreDict

    db_name = settings.database_name
    logging.info(f"Initializing Firestore connections (database: {db_name})")

    users_data = FirestoreDict(
        "Users",
        model_classes={"UserInfo": UserInfo},
        database_name=db_name
    )

    candidate_users_data = FirestoreDict(
        "CandidateUsers",
        model_classes={"UserInfo": UserInfo},
        database_name=db_name
    )

    bots_data = FirestoreDict(
        "Bots",
        model_classes={"BotProfile": BotProfile},
        database_name=db_name
    )

    otps_data = FirestoreDict(
        "OTPs",
        model_classes={"OTP": OTP},
        database_name=db_name
    )

    rounds_data = FirestoreDict(
        "Rounds",
        model_classes={"RoundResult": RoundResult},
        database_name=db_name
    )

    logging.info("Firestore connections initialized")
