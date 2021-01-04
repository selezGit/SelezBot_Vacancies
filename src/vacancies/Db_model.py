from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    create_engine,
)
from uuid import UUID, uuid4
from sqlalchemy.dialects.postgresql import UUID as UUIDField
from datetime import datetime
from json import dumps

engine = create_engine("postgres+psycopg2://")
Base = declarative_base()
Session = sessionmaker(bind=engine)

class TemplateModel:
    __table_args__ = {'schema': 'public'}
    uuid = Column( 
        UUIDField(as_uuid=True)
        ,primary_key=True
        ,default=uuid4
        ,unique=True
        ,nullable=False
    )
    def _dictify(self):
        _fields = [ field for
            field in dir( self ) if 
                bool(
                    str(field).startswith('_') + bool(field == 'metadata') 
                ) 
            is False
        ]
        _dict = dict()
        for elem in _fields:
            val = self.__dict__.get( elem )
            if bool( isinstance(val, Base) + isinstance(val, list) ) is True:
                continue
            elif bool(\
                isinstance(val, UUID) + isinstance(val, datetime)\
            ) is True:
                _dict[elem] = str( self.__dict__.get(elem) )
            else:
                _dict[elem] = self.__dict__.get(elem)
        return _dict



class Vacancy(Base, TemplateModel):
    __tablename__ = "vacancy"
    name = Column(String())
    publication_date = Column(String())

class Vacancy_responce(Base, TemplateModel):
    __tablename__ = "vacancy_responce"
    vacid = Column(Integer())
    state = Column(Integer())
    timestamp = Column(DateTime())
    score = Column(Integer())

class Vacancy_data(Base, TemplateModel):
    __tablename__= "data"
    link = Column(String())
    experience = Column(String())
    salary = Column(String())
    _full =  Column(String())
    skils =  Column(String())

def create_tables():
    #Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
def valid_responce(data):
    '''function converted of JSON in DUMP'''
    if bool(isinstance(data, list)):
        ready_data = []
        for item in data:
            ready_data.append(item._dictify())
    else:
        ready_data = data._dictify()
    return dumps(ready_data)
