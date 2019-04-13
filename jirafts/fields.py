import datetime
import json
import zlib

from peewee import BlobField


class JSONGzipField(BlobField):
    def python_value(self, value):
        if value is not None:
            if isinstance(value, memoryview):
                value = bytes(value)
            return json.loads(zlib.decompress(value))

    def db_value(self, value):
        if value is not None:
            encoded = json.dumps(value, cls=DateTimeJSONEncoder).encode("utf-8")
            return self._constructor(zlib.compress(encoded))


class DateTimeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            obj = obj.replace(microsecond=0, tzinfo=None)
            return obj.isoformat()
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        else:
            return super(DateTimeJSONEncoder, self).default(obj)
