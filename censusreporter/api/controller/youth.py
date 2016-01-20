from collections import OrderedDict

from api.models import get_model_from_fields
from api.models.tables import get_datatable, get_table_id
from api.utils import get_session, LocationNotFound

from api.controller.geography import get_geography


from .utils import (collapse_categories, calculate_median, calculate_median_stat,
    get_summary_geo_info, merge_dicts, group_remainder, add_metadata, get_stat_data,
    get_objects_by_geo, percent, create_debug_dump)


PROFILE_SECTIONS = (
    "demographics",
    "depravation"

)

def get_youth_profile(geo_code, geo_level):
    session = get_session()

    try:
        geo_summary_levels = get_summary_geo_info(geo_code, geo_level, session)
        data = {}
        sections = list(PROFILE_SECTIONS)
        if geo_level not in ['country', 'province', 'district', 'municipality']:
            pass
            # Raise error as we don't have this data

        for section in sections:
            function_name = 'get_%s_profile' % section
            if function_name in globals():
                func = globals()[function_name]
                data[section] = func(geo_code, geo_level, session)

                # get profiles for province and/or country
                for level, code in geo_summary_levels:
                    # merge summary profile into current geo profile
                    merge_dicts(data[section], func(code, level, session), level)


        return data

    finally:
        session.close()


def get_demographics_profile(geo_code, geo_level, session):
    # population group
    pop_dist_data, total_pop = get_stat_data(
            ['population group'], geo_level, geo_code, session)

    final_data = {
        'total_population': {
            "name": "People",
            "values": {"this": total_pop}
        },
    }

    geo = get_geography(geo_code, geo_level)
    if geo.square_kms:
        final_data['population_density'] = {
            'name': "people per square kilometre",
            'values': {"this": total_pop / geo.square_kms}
        }

    return final_data


def get_depravation_profile(geo_code, geo_level, session):
    table = get_datatable('youth').table
    youth_pop, youth_prop, edu_dep = session\
            .query(table.c.youth_pop,
                   table.c.youth_proportion,
                   table.c.edu_dep) \
            .filter(table.c.geo_level == geo_level) \
            .filter(table.c.geo_code == geo_code) \
            .one()

    return {
        'name': 'youth',
        'youth_pop': {
            "name": "Youth population (age 15-24)",
            "values": {"this": youth_pop},
            },
        'youth_prop': {
            "name": "Youth (age 15-24) as a percentage of total population",
            "values": {"this": float(youth_prop) or 0.0},
            },
        'edu_dep': {
            "name": "of youth deprived in educational attainment",
            "values": {"this": float(edu_dep) or 0.0},
            },
    }
