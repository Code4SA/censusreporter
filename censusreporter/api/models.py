from sqlalchemy import (Column, ForeignKey, Integer, SmallInteger,
                        String, Table, Numeric)
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship

from .utils import get_table_name


class Base(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join(['%s="%s"' % (c.name, getattr(self, c.name))
                                      for c in self.__table__.columns]))


Base = declarative_base(cls=Base)


'''
Geographic models
'''

class GeoNameMixin(object):

    @property
    def short_name(self):
        return getattr(self, 'name', '')

    @property
    def long_name(self):
        long_name = self.short_name
        parent_names = [p.name for p in self.parents()
                        if p.level != 'district']
        if len(parent_names) > 0:
            return '%s, %s' % (long_name, ', '.join(parent_names))
        return long_name

    def __unicode__(self):
        return self.long_name


class Ward(Base, GeoNameMixin):
    # an 8-digit number where the last 2 digits refer
    # to the ward number, e.g. 21001001 where ward_no = 1
    code = Column(String(8), primary_key=True)
    ward_no = Column(SmallInteger, nullable=False)
    year = Column(String(4), index=True, nullable=False)
    muni_code = Column(String(8), ForeignKey('municipality.code'))
    district_code = Column(String(8), ForeignKey('district.code'))
    province_code = Column(String(3), ForeignKey('province.code'))

    # associations
    municipality  = relationship('Municipality', lazy=False)
    district      = relationship('District', lazy=False)
    province      = relationship('Province', lazy=False)

    level = 'ward'

    def parents(self):
        return [self.municipality, self.district, self.province]

    @property
    def short_name(self):
        return 'Ward %d (%s)' % (self.ward_no, self.code)


class Municipality(Base, GeoNameMixin):
    # a 5-character string where the first 2 characters is the
    # province code and the last 3 are digits, e.g. MP322
    # Note: a few municipalities exist for large city areas with
    # 3-letter codes, e.g. CPT (same code used for district)
    code = Column(String(8), primary_key=True)
    name = Column(String(32), nullable=False)
    year = Column(String(4), index=True, nullable=False)
    district_code = Column(String(8), ForeignKey('district.code'))
    province_code = Column(String(3), ForeignKey('province.code'))

    # associations
    district  = relationship('District', lazy=False)
    province  = relationship('Province', lazy=False)

    level = 'municipality'

    def parents(self):
        return [self.district, self.province]


class District(Base, GeoNameMixin):
    # a 4-character string starting with 'DC' and followed by
    # 1 or 2 digits, e.g. DC10
    # Note: a few districts exist for large city areas with
    # 3-letter codes, e.g. CPT (same code used for municipality)
    code = Column(String(8), primary_key=True)
    name = Column(String(32), nullable=False)
    year = Column(String(4), index=True, nullable=False)
    province_code = Column(String(3), ForeignKey('province.code'))

    province  = relationship('Province', lazy=False)

    level = 'district'

    def parents(self):
        return [self.province]


class Province(Base, GeoNameMixin):
    # a 2 or 3-letter string
    code = Column(String(3), primary_key=True)
    name = Column(String(16), nullable=False)
    year = Column(String(4), index=True, nullable=False)
    # as defined here:
    # http://en.wikipedia.org/wiki/List_of_FIPS_region_codes_(S%E2%80%93U)#SF:_South_Africa
    fips_code = Column(String(4), index=True, unique=True, nullable=False)

    level = 'province'
    census_release = 2011

    def parents(self):
        # TODO: return nation
        return []


'''
Elections models
'''

class Votes(Base):
    ward_code = Column(String(8), ForeignKey('ward.code'))
    province_code = Column(String(3), ForeignKey('province.code'))
    municipality_code = Column(String(8), ForeignKey('municipality.code'))
    district_code = Column(String(8), ForeignKey('district.code'))

    # an 8-digit code
    # Note: a voting district is at sub-ward level
    voting_district_code = Column(String(8), primary_key=True)
    # current only 'municipal 2011'
    electoral_event = Column(String(32), primary_key=True)
    party = Column(String(64), primary_key=True)
    # one of PR (provincial), WARD or DC 40%
    ballot_type = Column(String(8), primary_key=True)
    # register votes in whole voting district
    registered_voters = Column(Integer)
    # total votes in whole voting district per ballot type
    total_votes = Column(Integer)
    # valid votes for the particular party per ballot type
    # we are mostly interested in this
    valid_votes = Column(Integer)
    # spoilt votes in whole voting district per ballot type
    spoilt_votes = Column(Integer)
    # mec7 votes in whole voting district - only valid for provincial ballots
    mec7_votes = Column(Integer)
    # percentage in whole voting district
    # This value is a percentage close to, but not equal to, (total_votes / registered_voters * 100)
    # The Electoral Commission must have some other way of calculating it.
    voter_turnout = Column(Numeric(precision=5, scale=2))

    # associations
    ward  = relationship('Municipality', lazy=True)
    municipality  = relationship('Municipality', lazy=True)
    province      = relationship('Province', lazy=True)
    district  = relationship('District', lazy=True)


'''
Census data models
'''

_census_table_models = {}


def get_model_from_fields(fields, geo_level, table_name=None):
    '''
    Generates an ORM model for arbitrary census fields by geography.

    :param list fields: the census fields in `api.utils.census_fields`, e.g. ['highest educational level', 'type of sector']
    :param str geo_level: one of the geographics levels defined in `api.utils.geo_levels`, e.g. 'province'
    :param str table_name: the name of the database table, if different from the default table
    :return: ORM model class containing the given fields with type String(128), a 'total' field
    with type Integer and '%(geo_level)s_code' with type ForeignKey('%(geo_level)s.code')
    :rtype: Model
    '''
    if table_name is None:
        table_name = get_table_name(fields, geo_level)
    if table_name in _census_table_models:
        return _census_table_models[table_name]

    field_columns = [Column(field, String(128), primary_key=True)
                     for field in fields]
    # no foreign key for country - we assume there is only 1 country's data
    if geo_level != 'country':
        field_columns.append(Column('%s_code' % geo_level, String(8),
                                    ForeignKey('%s.code' % geo_level),
                                    primary_key=True))
    class Model(Base):
        __table__ = Table(table_name, Base.metadata,
            Column('total', Integer, nullable=False),
            *field_columns
        )
    _census_table_models[table_name] = Model
    return Model
