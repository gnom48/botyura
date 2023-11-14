from peewee import *


db = SqliteDatabase('rielters.db')


class BaseModel(Model):

    class Meta:
        database = db


class Rielter_type(BaseModel):

    class Meta:
        db_table = "Rielter_types"

    type_id = PrimaryKeyField()
    rielter_type_name = TextField()


class Rielter(BaseModel):

    class Meta:
        db_table = "Rielters"
    
    rielter_id = PrimaryKeyField()
    fio = TextField(default="")
    birthday = DateField(default="")
    gender = TextField(default="")
    rielter_type = ForeignKeyField(Rielter_type)


class Report(BaseModel):

    class Meta:
        db_table = "Reports"

    rielter_id = ForeignKeyField(Rielter)

    cold_call_count = IntegerField(default=0)
    meet_new_objects = IntegerField(default=0)
    take_in_work = IntegerField(default=0)
    contrects_signed = IntegerField(default=0)
    show_objects = IntegerField(default=0)
    posting_adverts = IntegerField(default=0)
    ready_deposit_count = IntegerField(default=0)
    take_deposit_count = IntegerField(default=0)
    deals_count = IntegerField(default=0)
    
    total_cold_call_count = IntegerField(default=0)
    total_meet_new_objects = IntegerField(default=0)
    total_take_in_work = IntegerField(default=0)
    total_contrects_signed = IntegerField(default=0)
    total_show_objects = IntegerField(default=0)
    total_posting_adverts = IntegerField(default=0)
    total_ready_deposit_count = IntegerField(default=0)
    total_take_deposit_count = IntegerField(default=0)
    total_deals_count = IntegerField(default=0)


def create_db():
    db.connect()
    if not Rielter_type.table_exists():
        db.create_tables([Rielter_type])

        Rielter_type.create(type_id=0, rielter_type_name="Риелтор жилой недвижимости").save()
        Rielter_type.create(type_id=1, rielter_type_name="Риелтор коммерческой недвижимости").save()

    if not Rielter.table_exists():
        db.create_tables([Rielter])
        
    if not Report.table_exists():
        db.create_tables([Report])