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
    fio = TextField()
    birthday = DateField()
    gender = TextField()
    rielter_type = ForeignKeyField(Rielter_type)


class Report(BaseModel):

    class Meta:
        db_table = "Reports"

    rielter_id = ForeignKeyField(Rielter)

    cold_call_count = IntegerField()
    meet_new_objects = IntegerField()
    take_in_work = IntegerField()
    contrects_signed = IntegerField()
    show_objects = IntegerField()
    posting_adverts = IntegerField()
    ready_deposit_count = IntegerField()
    take_deposit_count = IntegerField()
    deals_count = IntegerField()
    
    total_cold_call_count = IntegerField()
    total_meet_new_objects = IntegerField()
    total_take_in_work = IntegerField()
    total_contrects_signed = IntegerField()
    total_show_objects = IntegerField()
    total_posting_adverts = IntegerField()
    total_ready_deposit_count = IntegerField()
    total_take_deposit_count = IntegerField()
    total_deals_count = IntegerField()


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