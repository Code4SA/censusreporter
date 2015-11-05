from collections import OrderedDict

from sqlalchemy import func

from api.models import get_model_from_fields
from api.models.tables import get_datatable, get_table_id
from api.utils import get_session, LocationNotFound

from .utils import (collapse_categories, calculate_median, calculate_median_stat, get_summary_geo_info,
                    merge_dicts, group_remainder, add_metadata, get_stat_data, get_objects_by_geo, percent,
                    create_debug_dump)


PROFILE_SECTIONS = (
    'age_groups',  # children in ECD age groups (0-2, 3-5, 6-9)
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
    '8': '6-9',
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


def get_age_groups_profile(geo_code, geo_level, session):
    ecd_ages, total = get_stat_data(
        ['age in completed years'], geo_level, geo_code, session,
        table_name='ageincompletedyears_%s' % geo_level,
        only=['0', '1', '2', '3', '4', '5', '6', '7', '8'],
        recode=ECD_AGE_CATEGORIES,
        percent=False)

    return {
        'age_groups': {
            'age_distribt=ution': ecd_ages,
            'total_ecd_children': {
                "name": "ECD aged Children",
                "values": {"this": total}
            }
        }
    }
