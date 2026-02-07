from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter


class FirestoreWhereFilter:
    def __init__(self, name, op, value):
        self.field = name
        self.operation = op
        self.value = value


class FirestoreEqualsFilter(FirestoreWhereFilter):
    def __init__(self, name, value):
        super().__init__(name, "==", value)


class FirestoreDict:
    """
    A dict-like interface to a Firestore collection, with automatic
    (de)serialization of Pydantic models.
    """
    def __init__(self, collection_name, model_classes=None, database_name=None):
        self.db = firestore.Client(database=database_name)
        self.collection = self.db.collection(collection_name)
        self.model_classes = model_classes or {}

    @staticmethod
    def _convert_firestore_datetypes(obj):
        import datetime
        if type(obj) is datetime.datetime:
            return obj
        if isinstance(obj, datetime.datetime):
            return datetime.datetime(
                obj.year, obj.month, obj.day, obj.hour, obj.minute, obj.second, obj.microsecond, obj.tzinfo
            )
        if isinstance(obj, dict):
            return {k: FirestoreDict._convert_firestore_datetypes(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [FirestoreDict._convert_firestore_datetypes(v) for v in obj]
        return obj

    def __getitem__(self, key):
        doc = self.collection.document(key).get()
        if not doc.exists:
            raise KeyError(key)
        data = doc.to_dict()
        data = self._convert_firestore_datetypes(data)
        model_type = data.get("_object_type")
        if model_type and model_type in self.model_classes:
            model_cls = self.model_classes[model_type]
            data = {k: v for k, v in data.items() if k != "_object_type"}
            return model_cls(**data)
        return data

    def __setitem__(self, key, value):
        if hasattr(value, "model_dump") and hasattr(value, "__class__"):
            class_name = value.__class__.__name__
            if self.model_classes and class_name not in self.model_classes:
                raise ValueError(
                    f"Cannot store object of type '{class_name}'. "
                    f"Allowed types: {list(self.model_classes.keys())}"
                )
            data = value.model_dump()
            data["_object_type"] = class_name
        else:
            data = value
        self.collection.document(key).set(data)

    def __delitem__(self, key):
        if not self.collection.document(key).get().exists:
            raise KeyError(key)
        self.collection.document(key).delete()

    def __contains__(self, key):
        return self.collection.document(key).get().exists

    def __iter__(self):
        for doc in self.collection.stream():
            yield doc.id

    def keys(self):
        return list(self.__iter__())

    def values(self):
        for doc in self.collection.stream():
            yield self[doc.id]

    def items(self):
        for doc in self.collection.stream():
            yield (doc.id, self[doc.id])

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __len__(self):
        return sum(1 for _ in self.collection.stream())

    def clear(self):
        for doc in self.collection.stream():
            self.collection.document(doc.id).delete()

    def _query_with_filters(self, filters):
        query = self.collection
        for f in filters:
            query = query.where(filter=FieldFilter(f.field, f.operation, f.value))
        return query

    def find(self, filters=None):
        """Yield (key, value) pairs where value matches all filters."""
        filters = filters or []
        query = self._query_with_filters(filters)
        for doc in query.stream():
            value = self[doc.id]
            yield (doc.id, value)

    def find_ids(self, filters=None):
        """Yield keys where value matches all filters."""
        filters = filters or []
        query = self._query_with_filters(filters)
        for doc in query.stream():
            yield doc.id

    def find_data(self, filters=None):
        """Yield values where value matches all filters."""
        filters = filters or []
        query = self._query_with_filters(filters)
        for doc in query.stream():
            yield self[doc.id]

    def update(self, key, updates: dict):
        """Update specific fields in a document"""
        if key not in self:
            raise KeyError(key)
        self.collection.document(key).update(updates)

    def subcollection(self, key, subcollection_name, model_classes=None):
        """Get a FirestoreDict for a subcollection of a document"""
        return FirestoreSubcollection(
            self.collection.document(key).collection(subcollection_name),
            model_classes=model_classes
        )


class FirestoreSubcollection(FirestoreDict):
    """FirestoreDict for subcollections"""
    def __init__(self, collection_ref, model_classes=None):
        self.db = collection_ref._client
        self.collection = collection_ref
        self.model_classes = model_classes or {}
