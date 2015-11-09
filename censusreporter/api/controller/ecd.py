from collections import OrderedDict

from api.models import get_model_from_fields
from api.models.tables import get_datatable, get_table_id
from api.utils import get_session, LocationNotFound

from api.controller.geography import get_geography


from .utils import (collapse_categories, calculate_median, calculate_median_stat, get_summary_geo_info,
                    merge_dicts, group_remainder, add_metadata, get_stat_data, get_objects_by_geo, percent,
                    create_debug_dump)


PROFILE_SECTIONS = (
    'demographics',
)

ECD_AGE_CATEGORIES = {
    '0': '0-2',
    '1': '0-2',
    '2': '0-2',
    '3': '3-5',
    '4': '3-5',
    '5': '3-5',
    '6': '6-9',
    '7': '6-9',
    '8': '6-9'
}


def get_ecd_profile(geo_code, geo_level):
    session = get_session()

    try:
        geo_summary_levels = get_summary_geo_info(geo_code, geo_level, session)
        data = {}

        sections = list(PROFILE_SECTIONS)
        if geo_level not in ['country', 'province', 'municipality']:
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

    ecd_age_groups, total_ecd = get_stat_data(
        ['age in completed years'], geo_level, geo_code, session,
        table_name='ageincompletedyears_%s' % geo_level,
        only=['0', '1', '2', '3', '4', '5', '6', '7', '8'],
        recode=ECD_AGE_CATEGORIES,
        percent=False)

    final_data = {
        'total_population': {
            "name": "People",
            "values": {"this": total_pop}
        },
        'ecd_age_groups': ecd_age_groups,
        'total_ecd': {
            "name": "Children under the age of nine years",
            "values": {"this": total_ecd}
        }
    }

    geo = get_geography(geo_code, geo_level)
    if geo.square_kms:
        final_data['population_density'] = {
            'name': "people per square kilometre",
            'values': {"this": total_pop / geo.square_kms}
        }
        final_data['child_population_density'] = {
            'name': 'children under the age of nine years per square kilometre',
            'values': {"this": total_ecd / geo.square_kms}
        }

    return final_data
