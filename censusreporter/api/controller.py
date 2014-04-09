from collections import OrderedDict

from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import or_, and_
from sqlalchemy import func

from .models import (get_model_from_fields, Ward, District, Municipality,
                     Province)
from .utils import get_session, ward_search_api, geo_levels


class LocationNotFound(Exception):
    pass


PROFILE_SECTIONS = (
    'demographics',  # population group, age group in 5 years, age in completed years
    'economics',  # individual monthly income, type of sector, official employment status
    'service_delivery',  # source of water, refuse disposal
    'education',  # highest educational level
)

# Education categories

COLLAPSED_EDUCATION_CATEGORIES = {
    'Gade 0': '<= Gr 3',
    'Grade 1 / Sub A': '<= Gr 3',
    'Grade 2 / Sub B': '<= Gr 3',
    'Grade 3 / Std 1/ABET 1Kha Ri Gude;SANLI': '<= Gr 3',
    'Grade 4 / Std 2': 'GET',
    'Grade 5 / Std 3/ABET 2': 'GET',
    'Grade 6 / Std 4': 'GET',
    'Grade 7 / Std 5/ ABET 3': 'GET',
    'Grade 8 / Std 6 / Form 1': 'GET',
    'Grade 9 / Std 7 / Form 2/ ABET 4': 'GET',
    'Grade 10 / Std 8 / Form 3': 'FET',
    'Grade 11 / Std 9 / Form 4': 'FET',
    'Grade 12 / Std 10 / Form 5': 'FET',
    'NTC I / N1/ NIC/ V Level 2': 'FET',
    'NTC II / N2/ NIC/ V Level 3': 'FET',
    'NTC III /N3/ NIC/ V Level 4': 'FET',
    'N4 / NTC 4': 'FET',
    'N5 /NTC 5': 'HET',
    'N6 / NTC 6': 'HET',
    'Certificate with less than Grade 12 / Std 10': 'FET',
    'Diploma with less than Grade 12 / Std 10': 'FET',
    'Certificate with Grade 12 / Std 10': 'HET',
    'Diploma with Grade 12 / Std 10': 'HET',
    'Higher Diploma': 'HET',
    'Post Higher Diploma Masters; Doctoral Diploma': 'Post-grad',
    'Bachelors Degree': 'HET',
    'Bachelors Degree and Post graduate Diploma': 'Post-grad',
    'Honours degree': 'Post-grad',
    'Higher Degree Masters / PhD': 'Post-grad',
    'Other': 'Other',
    'No schooling': 'None',
    'Unspecified': 'Other',
    'Not applicable': 'Other',
}
EDUCATION_GET_OR_HIGHER = set([
    'Grade 9 / Std 7 / Form 2/ ABET 4',
    'Grade 10 / Std 8 / Form 3',
    'Grade 11 / Std 9 / Form 4',
    'Grade 12 / Std 10 / Form 5',
    'NTC I / N1/ NIC/ V Level 2',
    'NTC II / N2/ NIC/ V Level 3',
    'NTC III /N3/ NIC/ V Level 4',
    'N4 / NTC 4',
    'N5 /NTC 5',
    'N6 / NTC 6',
    'Certificate with less than Grade 12 / Std 10',
    'Diploma with less than Grade 12 / Std 10',
    'Certificate with Grade 12 / Std 10',
    'Diploma with Grade 12 / Std 10',
    'Higher Diploma',
    'Post Higher Diploma Masters; Doctoral Diploma',
    'Bachelors Degree',
    'Bachelors Degree and Post graduate Diploma',
    'Honours degree',
    'Higher Degree Masters / PhD',
])
EDUCATION_FET_OR_HIGHER = set([
    'Grade 12 / Std 10 / Form 5',
    'N4 / NTC 4',
    'N5 /NTC 5',
    'N6 / NTC 6',
    'Certificate with Grade 12 / Std 10',
    'Diploma with Grade 12 / Std 10',
    'Higher Diploma',
    'Post Higher Diploma Masters; Doctoral Diploma',
    'Bachelors Degree',
    'Bachelors Degree and Post graduate Diploma',
    'Honours degree',
    'Higher Degree Masters / PhD',
])

# Age categories

COLLAPSED_AGE_CATEGORIES = {
    '00 - 04': '0-9',
    '05 - 09': '0-9',
    '10 - 14': '10-19',
    '15 - 19': '10-19',
    '20 - 24': '20-29',
    '25 - 29': '20-29',
    '30 - 34': '30-39',
    '35 - 39': '30-39',
    '40 - 44': '40-49',
    '45 - 49': '40-49',
    '50 - 54': '50-59',
    '55 - 59': '50-59',
    '60 - 64': '60-69',
    '65 - 69': '60-69',
    '70 - 74': '70-79',
    '75 - 79': '70-79',
    '80 - 84': '80+',
    '85+': '80+',
}

# Income categories

COLLAPSED_INCOME_CATEGORIES = {
    "No income": "0k",
    "Not applicable": "N/A",
    "R 102 401 - R 204 800": "> 102.4k",
    "R 12 801 - R 25 600": "51.2k",
    "R 1 601 - R 3 200": "3.2k",
    "R 1 - R 400": "0.8k",
    "R 204 801 or more": "> 102.4k",
    "R 25 601 - R 51 200": "51.2k",
    "R 3 201 - R 6 400": "6.4k",
    "R 401 - R 800": "0.8k",
    "R 51 201 - R 102 400": "102.4k",
    "R 6 401 - R 12 800": "12.8k",
    "R 801 - R 1 600": "1.6k",
    "Unspecified": "Unspec.",
}

# Sanitation categories

SHORT_WATER_SOURCE_CATEGORIES = {
    "Regional/local water scheme (operated by municipality or other water services provider)": "Service provider",
    "Water tanker": "Tanker",
    "Spring": "Spring",
    "Other": "Other",
    "Dam/pool/stagnant water": "Dam",
    "River/stream": "River",
    "Not applicable": "N/A",
    "Borehole": "Borehole",
    "Rain water tank": "Rainwater tank",
    "Water vendor": "Vendor",
}

SHORT_REFUSE_DISPOSAL_CATEGORIES = {
    "Removed by local authority/private company less often": "Service provider (not regularly)",
    "Own refuse dump": "Own dump",
    "Communal refuse dump": "Communal dump",
    "Other": "Other",
    "Not applicable": "N/A",
    "No rubbish disposal": "None",
    "Unspecified": "Unspecified",
    "Removed by local authority/private company at least once a week": "Service provider (regularly)",
}


def get_profile(geo_code, geo_level):
    session = get_session()
    data = {}
    for section in PROFILE_SECTIONS:
        function_name = 'get_%s_profile' % section
        if function_name in globals():
            data[section] = globals()[function_name](geo_code, geo_level, session)
    
    session.close()
    return data


def get_demographics_profile(geo_code, geo_level, session):
    # population group
    db_model_pop = get_model_from_fields(['population group'], geo_level)
    objects = get_objects_by_geo(db_model_pop, geo_code, geo_level,
                                 session, order_by='population group')

    pop_dist_data = OrderedDict()
    total_pop = 0.0
    for obj in objects:
        pop_group = getattr(obj, 'population group')
        total_pop += obj.total
        pop_dist_data[pop_group] = {
            "name": pop_group,
            "numerators": {"this": obj.total},
            "error": {"this": 0.0},
        }

    # age groups
    db_model_age = get_model_from_fields(['age groups in 5 years'], geo_level)
    objects = get_objects_by_geo(db_model_age, geo_code, geo_level, session)

    age_dist_data = {}
    total_age = 0.0
    for obj in objects:
        age_group = getattr(obj, 'age groups in 5 years')
        total_age += obj.total
        age_dist_data[age_group] = {
            "name": age_group,
            "numerators": {"this": obj.total},
            "error": {"this": 0.0},
        }
    age_dist_data = collapse_categories(age_dist_data,
                                        COLLAPSED_AGE_CATEGORIES,
                                        key_order=('0-9', '10-19',
                                                   '20-29', '30-39',
                                                   '40-49', '50-59',
                                                   '60-69', '70-79',
                                                   '80+'))

    # calculate percentages
    for data, total in zip((pop_dist_data, age_dist_data),
                           (total_pop, total_age)):
        for fields in data.values():
            fields["values"] = {"this": round(fields["numerators"]["this"]
                                              / total * 100, 2)}

    final_data = {'population_group_distribution': pop_dist_data,
                  'age_group_distribution': age_dist_data}

    # median age/age category if possible (might not have data at ward level)
    try:
        db_model_age = get_model_from_fields(['age in completed years'], geo_level)
        objects = sorted(
            get_objects_by_geo(db_model_age, geo_code, geo_level, session),
            key=lambda x: int(getattr(x, 'age in completed years'))
        )
        # median age
        median = calculate_median(objects, 'age in completed years')
        final_data['median_age'] = {
            "name": "Median age",
            "values": {"this": median},
            "error": {"this": 0.0}
        }
        # age category
        under_18 = 0.0
        over_or_65 = 0.0
        between_18_64 = 0.0
        total = 0.0
        for obj in objects:
            age = int(getattr(obj, 'age in completed years'))
            total += obj.total
            if age < 18:
                under_18 += obj.total
            elif age >= 65:
                over_or_65 += obj.total
            else:
                between_18_64 += obj.total
        final_data['age_category_distribution'] = OrderedDict((
            ("under_18", {
                "name": "Under 18",
                "error": {"this": 0.0},
                "values": {"this": round(under_18 / total * 100, 2)}
            }),
            ("18_to_64", {
                "name": "18 to 64",
                "error": {"this": 0.0},
                "values": {"this": round(between_18_64 / total * 100, 2)}
            }),
            ("65_and_over", {
                "name": "65 and over",
                "error": {"this": 0.0},
                "values": {"this": round(over_or_65 / total * 100, 2)}
            })
        ))
    except LocationNotFound:
        final_data['median_age'] = {
            "name": "Median age",
            "error": {"this": 0.0}
        }
        final_data['age_category_distribution'] = {
            "": {
                "name": "N/A",
                "error": {"this": 0.0},
                "values": {"this": 0}
            }
        }

    return final_data


def get_economics_profile(geo_code, geo_level, session):
    # income
    db_model_income = get_model_from_fields(['individual monthly income'],
                                            geo_level,
                                            'individualmonthlyincome_%s_employedonly'
                                            % geo_level)
    objects = get_objects_by_geo(db_model_income, geo_code, geo_level, session)
    income_dist_data = {}
    total_income = 0.0
    for obj in objects:
        income_group = getattr(obj, 'individual monthly income')
        if income_group == 'Not applicable':
            continue
        total_income += obj.total
        income_dist_data[income_group] = {
            "name": income_group,
            "numerators": {"this": obj.total},
            "error": {"this": 0.0},
        }
    income_dist_data = collapse_categories(income_dist_data,
                                           COLLAPSED_INCOME_CATEGORIES,
                                           key_order=('Unspec.', '0k',
                                                      '0.8k', '1.6k', '3.2k',
                                                      '6.4k', '12.8k', '51.2k',
                                                      '102.4k', '> 102.4k'))

    db_model_employ = get_model_from_fields(['official employment status'],
                                            geo_level)
    objects = get_objects_by_geo(db_model_employ, geo_code, geo_level, session)
    employ_status = {}
    total_workers = 0.0
    for obj in objects:
        employ_st = getattr(obj, 'official employment status')
        if employ_st in ('Age less than 15 years', 'Not applicable'):
            continue
        total_workers += obj.total
        employ_status[employ_st] = {
            "name": employ_st,
            "numerators": {"this": obj.total},
            "error": {"this": 0.0}
        }

    # sector
    db_model_sector = get_model_from_fields(['type of sector'], geo_level)
    objects = get_objects_by_geo(db_model_sector, geo_code, geo_level,
                                 session, order_by='type of sector')
    sector_dist_data = OrderedDict()
    total_sector = 0.0
    for obj in objects:
        sector = getattr(obj, 'type of sector')
        if sector == 'Not applicable' or obj.total == 0:
            continue
        total_sector += obj.total
        sector_dist_data[sector] = {
            "name": sector,
            "numerators": {"this": obj.total},
            "error": {"this": 0.0},
        }

    for data, total in zip((income_dist_data, sector_dist_data, employ_status),
                           (total_income, total_sector, total_workers)):
        for fields in data.values():
            fields["values"] = {"this": round(fields["numerators"]["this"]
                                              / total * 100, 2)}

    income_dist_data['metadata'] = {'universe': 'Officially employed individuals'}
    employ_status['metadata'] = {'universe': 'Workers 15 and over'}

    return {'individual_income_distribution': income_dist_data,
            'employment_status': employ_status,
            'sector_type_distribution': sector_dist_data}


def get_service_delivery_profile(geo_code, geo_level, session):
    # water source
    db_model_wsrc = get_model_from_fields(['source of water'], geo_level)
    objects = get_objects_by_geo(db_model_wsrc, geo_code, geo_level, session,
                                 order_by='-total')
    water_src_data = OrderedDict()
    total_wsrc = 0.0
    total_water_sp = 0.0
    # show 3 largest groups on their own and group the rest as 'Other'
    for i, obj in enumerate(objects):
        attr = getattr(obj, 'source of water')
        if i < 3:
            src = SHORT_WATER_SOURCE_CATEGORIES[attr]
            water_src_data[src] = {
                "name": src,
                "numerators": {"this": obj.total},
                "error": {"this": 0.0},
            }
        else:
            src = 'Other'
            water_src_data.setdefault(src, {
                "name": src,
                "numerators": {"this": 0.0},
                "error": {"this": 0.0},
            })
            water_src_data[src]["numerators"]["this"] += obj.total
        total_wsrc += obj.total
        if attr.startswith('Regional/local water scheme'):
            total_water_sp += obj.total

    # refuse disposal
    db_model_ref = get_model_from_fields(['refuse disposal'], geo_level)
    objects = get_objects_by_geo(db_model_ref, geo_code, geo_level, session,
                                 order_by='-total')
    refuse_disp_data = OrderedDict()
    total_ref = 0.0
    total_ref_sp = 0.0
    # show 3 largest groups on their own and group the rest as 'Other'
    for i, obj in enumerate(objects):
        attr = getattr(obj, 'refuse disposal')
        if i < 3:
            disp = SHORT_REFUSE_DISPOSAL_CATEGORIES[attr]
            refuse_disp_data[disp] = {
                "name": disp,
                "numerators": {"this": obj.total},
                "error": {"this": 0.0},
            }
        else:
            disp = 'Other'
            refuse_disp_data.setdefault(disp, {
                "name": disp,
                "numerators": {"this": 0.0},
                "error": {"this": 0.0},
            })
            refuse_disp_data[disp]["numerators"]["this"] += obj.total
        total_ref += obj.total
        if attr.startswith('Removed by local authority'):
            total_ref_sp += obj.total

    for data, total in zip((water_src_data, refuse_disp_data),
                           (total_wsrc, total_ref)):
        for fields in data.values():
            fields["values"] = {"this": round(fields["numerators"]["this"]
                                              / total * 100, 2)}

    return {'water_source_distribution': water_src_data,
            'percentage_water_from_service_provider': {
                "name": "Are getting water from a regional or local service provider",
                "values": {"this": round(total_water_sp / total_wsrc * 100, 2)},
                "error": {"this": 0}
            },
            'refuse_disposal_distribution': refuse_disp_data,
            'percentage_ref_disp_from_service_provider': {
                "name": "Are getting refuse disposal from a local authority or private company",
                "values": {"this": round(total_ref_sp / total_ref * 100, 2)},
                "error": {"this": 0}
            }
    }


def get_education_profile(geo_code, geo_level, session):
    db_model = get_model_from_fields(['highest educational level'], geo_level,
                                     'highesteducationallevel_%s_25andover'
                                     % geo_level)
    objects = get_objects_by_geo(db_model, geo_code, geo_level, session)

    edu_dist_data = {}
    get_or_higher = 0.0
    fet_or_higher = 0.0
    total = 0.0
    for i, obj in enumerate(objects):
        category_val = getattr(obj, 'highest educational level')
        # increment counters
        total += obj.total
        if category_val in EDUCATION_GET_OR_HIGHER:
            get_or_higher += obj.total
            if category_val in EDUCATION_FET_OR_HIGHER:
                fet_or_higher += obj.total
        # add data points for category
        edu_dist_data[str(i)] = {
            "name": category_val,
            "numerators": {"this": obj.total},
            "error": {"this": 0.0},
        }
    edu_dist_data = collapse_categories(edu_dist_data,
                                        COLLAPSED_EDUCATION_CATEGORIES,
                                        key_order=('None', 'Other',
                                                   '<= Gr 3', 'GET',
                                                   'FET', 'HET',
                                                   'Post-grad'))
    edu_split_data = {
        'percent_get_or_higher': {
            "name": "Completed GET or higher",
            "numerators": {"this": get_or_higher},
            "error": {"this": 0.0},
        },
        'percent_fet_or_higher': {
            "name": "Completed FET or higher",
            "numerators": {"this": fet_or_higher},
            "error": {"this": 0.0},
        }
    }
    # calculate percentages
    for data in (edu_dist_data, edu_split_data):
        for fields in data.values():
            fields["values"] = {"this": round(fields["numerators"]["this"]
                                              / total * 100, 2)}

    edu_dist_data['metadata'] = {'universe': 'Invididuals 25 and over'}
    edu_split_data['metadata'] = {'universe': 'Invididuals 25 and over'}

    return {'educational_attainment_distribution': edu_dist_data,
            'educational_attainment': edu_split_data}


def collapse_categories(data, categories, key_order=None):
    if key_order:
        collapsed = OrderedDict((key, {'name': key}) for key in key_order)
    else:
        collapsed = {}

    # level 1: iterate over categories in data
    for fields in data.values():
        new_category_name = categories[fields['name']]
        collapsed.setdefault(new_category_name, {'name': new_category_name})
        new_fields = collapsed[new_category_name]
        # level 2: iterate over measurement objects in category
        for measurement_key, measurement_objects in fields.iteritems():
            if measurement_key == 'name':
                continue
            new_fields.setdefault(measurement_key, {})
            new_measurement_objects = new_fields[measurement_key]
            # level 3: iterate over data points in measurement objects
            for datapoint_key, datapoint_value in measurement_objects.iteritems():
                try:
                    new_measurement_objects.setdefault(datapoint_key, 0)
                    new_measurement_objects[datapoint_key] += float(datapoint_value)
                except (ValueError, TypeError):
                    new_measurement_objects[datapoint_key] = datapoint_value

    return collapsed


def get_objects_by_geo(db_model, geo_code, geo_level, session, order_by=None):
    geo_attr = '%s_code' % geo_level
    objects = session.query(db_model).filter(getattr(db_model, geo_attr)
                                             == geo_code)
    if order_by is not None:
        if order_by[0] == '-':
            objects = objects.order_by(getattr(db_model, order_by[1:]).desc())
        else:
            objects = objects.order_by(getattr(db_model, order_by))
    objects = objects.all()
    if len(objects) == 0:
        raise LocationNotFound("%s.%s with code '%s' not found"
                               % (db_model.__tablename__, geo_attr, geo_code))
    return objects


def calculate_median(objects, field_name):
    '''
    Calculates the median where obj.total is the distribution count and
    getattr(obj, field_name) is the distribution segment.
    Note: this function assumes the objects are sorted.
    '''
    total = 0
    for obj in objects:
        total += obj.total
    half = total / 2.0

    counter = 0
    for i, obj in enumerate(objects):
        counter += obj.total
        if counter > half:
            if counter - half == 1:
                # total must be even (otherwise counter - half ends with .5)
                return (float(getattr(objects[i - 1], field_name)) +
                        float(getattr(obj, field_name))) / 2.0
            return float(getattr(obj, field_name))
        elif counter == half:
            # total must be even (otherwise half ends with .5)
            return (float(getattr(obj, field_name)) +
                    float(getattr(objects[i + 1], field_name))) / 2.0


def get_locations(search_term, geo_level=None):
    if geo_level is not None and geo_level not in geo_levels:
        raise ValueError('Invalid geo_level: %s' % geo_level)
    session = get_session()

    if geo_level == 'ward':
        # try to find by ward code first, then address/place name
        ward = session.query(Ward).get(search_term)
        if not ward:
            locations = ward_search_api.search(search_term)
            if locations:
                ward_codes = [l.ward_code for l in locations]
                wards = session.query(Ward).filter(Ward.code.in_(ward_codes)).all()
                _complete_ward_data_from_api(locations, session)
            else:
                wards = []
        else:
            wards = [ward]
        return serialize_demarcations(wards)

    elif geo_level is not None:
        model = globals()[geo_level.capitalize()]
        # try to find by code or name
        demarcations = session.query(model).filter(
            or_(model.name.ilike(search_term + '%'),
                model.code == search_term.upper())
        ).all()
        return serialize_demarcations(demarcations)

    else:
        '''
        This search differs from the above in that it first
        search for wards. If it finds wards it adds the wards and
        their provinces, districts and municipalities to the results.
        It then also checks if any province, district or municipality
        matches the search term in their own right, adding these
        to the results as well.
        '''
        objects = set()
        # look up wards
        locations = ward_search_api.search(search_term)
        if locations:
            _complete_ward_data_from_api(locations, session)
            ward_codes = [l.ward_code for l in locations]
            wards = session.query(Ward).options(
                joinedload('*', innerjoin=True)
            ).filter(Ward.code.in_(ward_codes)).all()
            objects.update(wards)
            for ward in wards:
                objects.update([ward.municipality, ward.district, ward.province])

        # find other matches
        for model in (Municipality, District, Province):
            objects.update(session.query(model).filter(
                or_(model.name.ilike(search_term + '%'),
                    model.name.ilike('City of %s' % search_term + '%'),
                    model.code == search_term.upper())
            ).all())

        order_map = {Ward: 1, Municipality: 2, District: 3, Province: 4}
        objects = sorted(objects, key=lambda o: "%d%s" % (
            order_map[o.__class__],
            getattr(o, 'name', getattr(o, 'code'))
        ))
        return serialize_demarcations(objects)


def serialize_demarcations(objects):
    data = []
    for obj in objects:
        if isinstance(obj, Ward):
            obj_dict = {
                'full_name': '%s, %s, %s' % (obj.code, obj.municipality.name,
                                             obj.province_code),
                'full_geoid': 'ward-%s' % obj.code,
            }
        elif isinstance(obj, Municipality):
            obj_dict = {
                'full_name': '%s, %s' % (obj.name, obj.province_code),
                'full_geoid': 'municipality-%s' % obj.code,
            }
        elif isinstance(obj, District):
            obj_dict = {
                'full_name': '%s, %s' % (obj.name, obj.province_code),
                'full_geoid': 'district-%s' % obj.code,
            }
        elif isinstance(obj, Province):
            obj_dict = {
                'full_name': '%s' % obj.name,
                'full_geoid': 'province-%s' % obj.code,
            }
        else:
            raise ValueError("Unrecognized demarcation class")
        data.append(obj_dict)
    return data


def _complete_ward_data_from_api(locations, session):
    '''
    Completes the ward data in the DB when a ward appears in a search result
    '''
    for location in locations:
        ward_obj = session.query(Ward).get(location.ward_code)
        if ward_obj is not None and not (ward_obj.province_code and
                                         ward_obj.district_code and
                                         ward_obj.muni_code):
            ward_obj.province_code = location.province_code
            # there are no duplicate names within a province, incidentally
            municipality = session.query(Municipality).filter(
                and_(func.lower(Municipality.name) ==
                     func.lower(location.municipality),
                     Municipality.province_code == location.province_code)
            ).one()
            ward_obj.muni_code = municipality.code
            ward_obj.district_code = municipality.district_code

    session.commit()
