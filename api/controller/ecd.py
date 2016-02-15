from collections import OrderedDict

from api.models import get_model_from_fields
from api.models.tables import get_datatable
from api.utils import get_session, percent

from api.controller.geography import get_geography


from .utils import (get_summary_geo_info, merge_dicts, group_remainder, add_metadata, get_stat_data,
                    get_objects_by_geo, percent, ratio)


PROFILE_SECTIONS = (
    "demographics",
    "hospitals",
    "schools",
    "ecd_centres",
    "ecd_educators",
    "ecd_budgets",
    "households",
    "service_delivery"
)

ECD_AGE_CATEGORIES = {
    '0': '0-2',
    '1': '0-2',
    '2': '0-2',
    '3': '3-5',
    '4': '3-5',
    '5': '3-5',
    '6': '6',
}

TYPE_OF_DWELLING_RECODE = {
    'House or brick/concrete block structure on a separate stand or yard or on a farm': 'House',
    'Traditional dwelling/hut/structure made of traditional materials': 'Traditional',
    'Flat or apartment in a block of flats': 'Apartment',
    'Cluster house in complex': 'Cluster house',
    'Townhouse (semi-detached house in a complex)': 'Townhouse',
    'Semi-detached house': 'Semi-detached house',
    'House/flat/room in backyard': 'Backyard in flat',
    'Informal dwelling (shack; in backyard)': 'Shack',
    'Informal dwelling (shack; not in backyard; e.g. in an informal/squatter settlement or on a farm)': 'Shack',
    'Room/flatlet on a property or larger dwelling/servants quarters/granny flat': 'Room or flatlet',
    'Caravan/tent': 'Caravan/tent',
    'Other': 'Other',
    'Unspecified': 'Unspecified',
    'Not applicable': 'N/A',
}

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

COLLAPSED_TOILET_CATEGORIES = {
    "Flush toilet (connected to sewerage system)": "Flush toilet",
    "Flush toilet (with septic tank)": "Flush toilet",
    "Chemical toilet": "Chemical toilet",
    "Pit toilet with ventilation (VIP)": "Pit toilet",
    "Pit toilet without ventilation": "Pit toilet",
    "Bucket toilet": "Bucket toilet",
    "Other": "Other",
    "None": "None",
    "Unspecified": "Unspecified",
    "Not applicable": "N/A",
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

        group_remainder(data['households']['type_of_dwelling_distribution'], 5)
        group_remainder(data['service_delivery']['water_source_distribution'], 5)
        group_remainder(data['service_delivery']['toilet_facilities_distribution'], 5)

        return data

    finally:
        session.close()


def get_demographics_profile(geo_code, geo_level, session):
    # population group
    pop_dist_data, total_pop = get_stat_data(
        ['population group'], geo_level, geo_code, session)

    ecd_age_groups, ecd_children = get_stat_data(
        ['age in completed years'], geo_level, geo_code, session,
        table_name='ageincompletedyears_%s' % geo_level,
        only=['0', '1', '2', '3', '4', '5', '6'],
        recode=ECD_AGE_CATEGORIES)

    ecd_gender, total_ecd_gender = get_stat_data(
        ['gender'], geo_level, geo_code, session,
        table_name='genderunder9_%s' % geo_level)

    women_child_bearing_age, total_women_child_bearing_age = get_stat_data(
        ['age groups in 5 years'], geo_level, geo_code, session,
        table_name='womenagegroupsin5years15to44_%s' % geo_level,
        order_by='age groups in 5 years'
    )

    final_data = {
        'total_population': {
            "name": "People",
            "values": {"this": total_pop}
        },
        'ecd_age_groups': ecd_age_groups,
        'ecd_children': {
            "name": "Children under the age of 9 years",
            "values": {"this": ecd_children}
        },
        'ecd_gender': ecd_gender,
        'women_child_bearing_age': women_child_bearing_age,
        'total_women_child_bearing_age': {
            "name": "Women between the age of 15-44 years",
            "values": {"this": total_women_child_bearing_age}
        }
    }

    geo = get_geography(geo_code, geo_level)
    if geo.square_kms:
        final_data['population_density'] = {
            'name': "people per square kilometre",
            'values': {"this": total_pop / geo.square_kms}
        }
        final_data['child_population_density'] = {
            'name': 'Children (0-9 years) per square kilometre',
            'values': {"this": ecd_children / geo.square_kms}
        }

        ecd_pop_density = OrderedDict()

        for k, age_group in ecd_age_groups.iteritems():
            if k != 'metadata':
                ecd_pop_density[age_group['name']] = {
                    "name": age_group['name'],
                    "values": {
                        "this": age_group['numerators']['this'] / geo.square_kms
                    },
                    "numerators": {
                        "this": age_group['numerators']['this']
                    }
                }
        ecd_pop_density['metadata'] = ecd_age_groups['metadata']

        final_data['ecd_pop_density'] = ecd_pop_density

    return final_data


def get_schools_profile(geo_code, geo_level, session):
    # population group
    _, total_pop = get_stat_data(
        ['population group'], geo_level, geo_code, session)

    # Schools
    table = get_datatable('schools_2015')
    keys = ['primary_schools', 'combined_schools', 'intermediate_schools', 'secondary_schools']
    school_breakdown, total_schools = table.get_stat_data(
        geo_level, geo_code, keys, percent=False)

    primary_school_ages = ['6', '7', '8', '9', '10', '11', '12', '13']
    secondary_school_ages = ['14', '15', '16', '17', '18']

    _, total_primary_children = get_stat_data(
        ['age in completed years'], geo_level, geo_code, session,
        table_name='ageincompletedyears_%s' % geo_level,
        only=primary_school_ages)

    _, total_secondary_children = get_stat_data(
        ['age in completed years'], geo_level, geo_code, session,
        table_name='ageincompletedyears_%s' % geo_level,
        only=secondary_school_ages)

    children_per_primary_school = ratio(total_primary_children, school_breakdown['primary_schools']['values']['this'])
    children_per_secondary_school = ratio(total_secondary_children, school_breakdown['secondary_schools']['values']['this'])

    final_data = {
        'total_schools': {
            "name": "Schools",
            "values": {"this": total_schools}
        },
        "school_breakdown": school_breakdown,
        "children_per_primary_school": {
            "name": "Children (6-13 years) in the region for each primary school",
            "values": {"this": children_per_primary_school}
        },
        "children_per_secondary_school": {
            "name": "Children (14-18 years) for each secondary school",
            "values": {"this": children_per_secondary_school}
        }
    }

    return final_data


def get_ecd_centres_profile(geo_code, geo_level, session):

    children_age_groups, total_children = get_stat_data(
        ['age in completed years'], geo_level, geo_code, session,
        table_name='ageincompletedyears_%s' % geo_level,
        only=['3', '4', '5', '6'],
        recode=ECD_AGE_CATEGORIES,
        percent=False)

    children_3_to_5 = children_age_groups['3-5']['values']['this']

    # This will not be needed when the column names for centres are changed.
    recode = OrderedDict([
        ('reg_full', 'Registered'),
        ('reg_conditional', 'Conditionally registered'),
        ('reg_not_registered', 'Unregistered'),
        ('reg_in_process', 'Registration in process'),
        ('reg_unspecified', 'Unspecified')
    ])

    table = get_datatable('ecd_centres_2014')

    ecd_centres_by_registration, total_ecd_centres = table.get_stat_data(
        geo_level, geo_code, recode.keys(), percent=True, total='total_ecd_centres',
        recode=recode)

    # incomplete is everything else
    ecd_incomplete = total_ecd_centres - sum(ecd_centres_by_registration[k]['numerators']['this'] for k in recode.itervalues())
    ecd_centres_by_registration['reg_incomplete'] = {
        "name": "Registration incomplete",
        "values": {"this": percent(ecd_incomplete, total_ecd_centres)},
        "numerators": {"this": ecd_incomplete}
    }

    table = get_datatable('ecd_children_enrolled')
    children_enrolled, _ = table.get_stat_data(
         geo_level, geo_code, percent=False)
    children_enrolled['children_enrolled_age_3_to_5']['name'] = 'Children enrolled in ECD centres'

    children_3_to_5_coverage = percent(
        children_enrolled['children_enrolled_age_3_to_5']['values']['this'],
        children_3_to_5)

    children_3_to_5_per_ecd_centre = ratio(
        children_3_to_5,
        total_ecd_centres)

    children_3_to_5_per_ecd_centre_enrolled = ratio(
        children_enrolled['children_enrolled_age_3_to_5']['values']['this'],
        total_ecd_centres)

    table = get_datatable('ecd_centres_by_type')
    ecd_centres_by_type, _ = table.get_stat_data(
        geo_level, geo_code)

    # Currently there's no data available for these datapoints.
    # They are displayed in the template to promote this fact.

    registered_ecd_programmes = {
        "name": "Registered ECD programs",
        "values": {"this": None},
    }
    children_in_ecd_programmes = {
        "name": "Children in programmes",
        "values": {"this": None},
    }
    children_in_play_groups = {
        "name": "Children in play groups",
        "values": {"this": None},
    }

    children_grade_r_age = {
        "name": "Children of Grade R age (6 years)",
        "values": {"this": children_age_groups['6']['values']['this']}
    }

    ecd_centres_with_grade_r_learners = {
        "name": "Centres with Grade R learners",
        "values": {"this": None}
    }

    schools_with_grade_r_learners = {
        "name": "Schools with Grade R learners",
        "values": {"this": None}
    }

    children_receiving_subsidy = {
        "name": "Children receiving an early learning subsidy",
        "values": {"this": None}
    }

    return {
        "total_ecd_centres": {
            "name": "Number of ECD centres",
            "values": {"this": total_ecd_centres}
        },
        "ecd_centres_by_registration": ecd_centres_by_registration,
        "ecd_centres_by_type": ecd_centres_by_type,
        "registered_ecd_programmes": registered_ecd_programmes,
        "children_enrolled_age_3_to_5": children_enrolled['children_enrolled_age_3_to_5'],
        "children_3_to_5_coverage": {
            "name": "Enrolment coverage. Children living in the area who are enrolled in ECD centres",
            "values": {"this": children_3_to_5_coverage}
        },
        "children_3_to_5_per_ecd_centre": {
            "name": "Average number of children living in the region per ECD centre",
            "values": {"this": children_3_to_5_per_ecd_centre}
        },
        "children_3_to_5_per_ecd_centre_enrolled": {
            "name": "Average number of children enrolled in each ECD centre",
            "values": {"this": children_3_to_5_per_ecd_centre_enrolled}
        },
        "children_in_ecd_programmes": children_in_ecd_programmes,
        "children_in_play_groups": children_in_play_groups,
        "children_grade_r_age": children_grade_r_age,
        "ecd_centres_with_grade_r_learners": ecd_centres_with_grade_r_learners,
        "schools_with_grade_r_learners": schools_with_grade_r_learners,
        "children_receiving_subsidy": children_receiving_subsidy
    }


def get_ecd_educators_profile(geo_code, geo_level, session):
    # These values will be filled as information becomes available.
    total_practitioners_per_child = {
        "name": "Number of practitioners per child",
        "values": {"this": None}
    }

    trained_practitioners_per_child = {
        "name": "Number of trained practitioners per child *",
        "values": {"this": None}
    }

    untrained_practitioners_per_child = {
        "name": "Number of untrained practitioners per child *",
        "values": {"this": None}
    }

    return {
        "total_practitioners_per_child": total_practitioners_per_child,
        "trained_practitioners_per_child": trained_practitioners_per_child,
        "untrained_practitioners_per_child": untrained_practitioners_per_child,
    }


def get_ecd_budgets_profile(geo_code, geo_level, session):
    # These values will be filled as information becomes available.
    ecd_subsidies_budgeted = {
        "name": "Amount budgeted for early learning subsidies",
        "values": {"this": None}
    }

    ecd_subsidies_paid = {
        "name": "Amount paid for early learning subsidies",
        "values": {"this": None}
    }

    return {
        "ecd_subsidies_budgeted": ecd_subsidies_budgeted,
        "ecd_subsidies_paid": ecd_subsidies_paid
    }


def get_hospitals_profile(geo_code, geo_level, session):
    # population group
    _, total_pop = get_stat_data(
        ['population group'], geo_level, geo_code, session)

    # Hospitals
    table = get_datatable('hospitals_2012')
    keys = ['regional_hospital', 'central_hospital', 'district_hospital', 'clinic', 'chc']
    hospital_breakdown, total_hospitals = table.get_stat_data(
        geo_level, geo_code, keys, percent=False,
        recode={'chc': 'Community health centre'})

    people_per_hospital = ratio(total_pop, total_hospitals)

    return {
        "total_hospitals": {
            "name": "Hospitals / Clinics",
            "values": {"this": total_hospitals}
        },
        "hospital_breakdown": hospital_breakdown,
        "people_per_hospital": {
            "name": "People living in the region for each hospital / clinic",
            "values": {"this": people_per_hospital}
        },
    }


def get_households_profile(geo_code, geo_level, session):
    # head of household
    # gender
    head_gender_dist, total_households = get_stat_data(
        ['gender of household head'], geo_level, geo_code, session,
        order_by='gender of household head')
    female_heads = head_gender_dist['Female']['numerators']['this']

    # age
    db_model_u18 = get_model_from_fields(
        ['gender of head of household'], geo_level,
        table_name='genderofheadofhouseholdunder18_%s' % geo_level
    )
    objects = get_objects_by_geo(db_model_u18, geo_code, geo_level, session)
    total_under_18 = float(sum(o[0] for o in objects))

    # type of dwelling
    type_of_dwelling_dist, _ = get_stat_data(
        ['type of dwelling'], geo_level, geo_code, session,
        recode=TYPE_OF_DWELLING_RECODE,
        order_by='-total')
    informal = type_of_dwelling_dist['Shack']['numerators']['this']

    return {
        'total_households': {
            'name': 'Households',
            'values': {'this': total_households},
        },
        'type_of_dwelling_distribution': type_of_dwelling_dist,
        'informal': {
            'name': 'Households that are informal dwellings (shacks)',
            'values': {'this': percent(informal, total_households)},
            'numerators': {'this': informal},
        },
        'head_of_household': {
            'gender_distribution': head_gender_dist,
            'female': {
                'name': 'Households with women as their head',
                'values': {'this': percent(female_heads, total_households)},
                'numerators': {'this': female_heads},
            },
            'under_18': {
                'name': 'Households with heads under 18 years old',
                'values': {'this': total_under_18},
            }
        },
    }


def get_service_delivery_profile(geo_code, geo_level, session):
    # water source
    water_src_data, total_wsrc = get_stat_data(
        ['source of water'], geo_level, geo_code, session,
        recode=SHORT_WATER_SOURCE_CATEGORIES,
        order_by='-total')
    if 'Service provider' in water_src_data:
        total_water_sp = water_src_data['Service provider']['numerators']['this']
    else:
        total_water_sp = 0.0

    # electricity
    elec_attrs = ['electricity for cooking',
                  'electricity for heating',
                  'electricity for lighting']
    db_model_elec = get_model_from_fields(elec_attrs, geo_level)
    objects = get_objects_by_geo(db_model_elec, geo_code, geo_level, session)
    total_elec = 0.0
    total_some_elec = 0.0
    elec_access_data = {
        'total_all_elec': {
            "name": "Have electricity for everything",
            "numerators": {"this": 0.0},
        },
        'total_some_not_all_elec': {
            "name": "Have electricity for some things",
            "numerators": {"this": 0.0},
        },
        'total_no_elec': {
            "name": "No electricity",
            "numerators": {"this": 0.0},
        }
    }
    for obj in objects:
        total_elec += obj.total
        has_some = False
        has_all = True
        for attr in elec_attrs:
            val = not getattr(obj, attr).startswith('no ')
            has_all = has_all and val
            has_some = has_some or val
        if has_some:
            total_some_elec += obj.total
        if has_all:
            elec_access_data['total_all_elec']['numerators']['this'] += obj.total
        elif has_some:
            elec_access_data['total_some_not_all_elec']['numerators']['this'] += obj.total
        else:
            elec_access_data['total_no_elec']['numerators']['this'] += obj.total

    for data, total in zip((elec_access_data,), (total_elec,)):
        for fields in data.values():
            fields["values"] = {"this": percent(fields["numerators"]["this"], total)}

    add_metadata(elec_access_data, db_model_elec)

    # toilets
    toilet_data, total_toilet = get_stat_data(
        ['toilet facilities'], geo_level, geo_code, session,
        exclude_zero=True,
        recode=COLLAPSED_TOILET_CATEGORIES,
        order_by='-total')

    total_flush_toilet = 0.0
    total_no_toilet = 0.0
    for key, data in toilet_data.iteritems():
        if key.startswith('Flush') or key.startswith('Chemical'):
            total_flush_toilet += data['numerators']['this']
        if key == 'None':
            total_no_toilet += data['numerators']['this']

    return {
        'water_source_distribution': water_src_data,
        'percentage_water_from_service_provider': {
            "name": "Are getting water from a regional or local service provider",
            "numerators": {"this": total_water_sp},
            "values": {"this": percent(total_water_sp, total_wsrc)},
        },
        'percentage_electricity_access': {
            "name": "Have electricity for at least one of cooking, heating or lighting",
            "numerators": {"this": total_some_elec},
            "values": {"this": percent(total_some_elec, total_elec)},
        },
        'electricity_access_distribution': elec_access_data,
        'percentage_flush_toilet_access': {
            "name": "Have access to flush or chemical toilets",
            "numerators": {"this": total_flush_toilet},
            "values": {"this": percent(total_flush_toilet, total_toilet)},
        },
        'percentage_no_toilet_access': {
            "name": "Have no access to any toilets",
            "numerators": {"this": total_no_toilet},
            "values": {"this": percent(total_no_toilet, total_toilet)},
        },
        'toilet_facilities_distribution': toilet_data,
    }
