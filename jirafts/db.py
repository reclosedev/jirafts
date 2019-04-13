from peewee import Model, SqliteDatabase, CharField, DateTimeField, fn

from .fields import JSONGzipField


db = SqliteDatabase(None)


class BaseModel(Model):
    class Meta:
        database = db


class Ticket(BaseModel):
    key = CharField(primary_key=True)
    updated = DateTimeField(index=True)
    created = DateTimeField(index=True)
    data = JSONGzipField()

    @classmethod
    def get_min_max_dates(cls):
        return cls.select(fn.Min(cls.updated), fn.Max(cls.updated)).scalar(as_tuple=True)

    @classmethod
    def query_reverse_alphanum(cls):
        return cls.select(cls).order_by(fn.Length(cls.key), cls.key).namedtuples().iterator()


def connect(path):
    db.init(path)
    db.connect()
    db.create_tables([Ticket])
