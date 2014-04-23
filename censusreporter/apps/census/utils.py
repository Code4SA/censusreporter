from __future__ import division
from collections import OrderedDict

from django.utils import simplejson
from django.utils.functional import Promise
from django.utils.encoding import force_unicode


def get_object_or_none(klass, *args, **kwargs):
    try:
        return klass._default_manager.get(*args, **kwargs)
    except klass.DoesNotExist:
        return None

class LazyEncoder(simplejson.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_unicode(obj)
        return obj

## A little generator to pluck out max values ##
def drill(item):
    if isinstance(item, int) or isinstance(item, float):
        yield item
    elif isinstance(item, list):
        for i in item:
            for result in drill(i):
                yield result
    elif isinstance(item, dict):
        for k,v in item.items():
            for result in drill(v):
                yield result

def get_max_value(nested_dicts):
    max_value = max([item for item in drill(nested_dicts)])
    return max_value

def get_ratio(num1, num2, precision=2):
    '''requires ints or int-like strings'''
    if num1 and num2:
        return round(round(float(num1) / float(num2), precision)*100, 1) or None
    return None


# Sources:
# http://mcdc2.missouri.edu/pub/data/sf32000/Techdoc/ch4_summary_level_seq_chart.pdf
# http://www2.census.gov/acs2011_1yr/summaryfile/ACS_2011_SF_Tech_Doc.pdf
SUMMARY_LEVEL_DICT = {
    "010": {
        "name": "United States",
        "plural": "",
    },
    "020": {
        "name": "Region",
        "plural": "regions",
    },
    "030": {
        "name": "Division",
        "plural": "divisions",
    },
    "040": {
        "name": "State",
        "plural": "states",
    },
    "050": {
        "name": "County",
        "plural": "counties",
    },
    "060": {
        "name": "County Subdivision",
        "plural": "county subdivisions",
    },
    "061": {
        "name": "Minor Civil Division (MCD)/Census County Division (CCD) (10,000+)",
        "plural": "minor civil divisions (10,000+)",
    },
    "062": {
        "name": "Minor Civil Division (MCD)/Census County Division (CCD) (<10,000)",
        "plural": "minor civil divisions (<10,000)",
    },
    "063": {
        "name": "Minor Civil Division (MCD)/Census County Division (CCD) (2500+)",
        "plural": "minor civil divisions (2,500+)",
    },
    "064": {
        "name": "Minor Civil Division (MCD)/Census County Division (CCD) (< 2500 in Metro Area)",
        "plural": "minor civil divisions (<2,500 in metro area)",
    },
    "067": {
        "name": "Subbarrio",
        "plural": "",
    },
    "070": {
        "name": "County Subdivision-Place/Remainder",
        "plural": "",
    },
    "071": {
        "name": "County Subdivision-Place (10,000+)/Remainder",
        "plural": "",
    },
    "072": {
        "name": "County Subdivision-Place (2500+)/Remainder",
        "plural": "",
    },
    "080": {
        "name": "Place/Remainder-Census Tract",
        "plural": "",
    },
    "082": {
        "name": "County Subdivision-Place(2500+)/Remainder-Census Tract",
        "plural": "",
    },
    "085": {
        "name": "County Subdivision-Place/Remainder-Census Tract-Urban/Rural",
        "plural": "",
    },
    "090": {
        "name": "Census Tract-Urban/Rural-Block Group",
        "plural": "",
    },
    "091": {
        "name": "County Subdivision-Place/Remainder-Census Tract-Block Group",
        "plural": "",
    },
    "101": {
        "name": "Block",
        "plural": "blocks",
    },
    "140": {
        "name": "Census Tract",
        "plural": "Census tracts",
    },
    "144": {
        "name": "Census Tract-American Indian Area/Alaska Native Area/Hawaiian Home Land",
        "plural": "",
    },
    "150": {
        "name": "Block Group",
        "plural": "block groups",
    },
    "154": {
        "name": "Block Group-American Indian Area/Alaska Native Area/Hawaiian Home Land",
        "plural": "",
    },
    "155": {
        "name": "Place-County",
        "plural": "",
    },
    "157": {
        "name": "Place (no CDPs)-County" ,
        "plural": "",
    },
    "158": {
        "name": "Place-County-Census Tract",
        "plural": "",
    },
    "160": {
        "name": "Place",
        "plural": "places",
    },
    "161": {
        "name": "State-Place (10,000+)",
        "plural": "",
    },
    "162": {
        "name": "State-Place (no CDPs)",
        "plural": "",
    },
    "170": {
        "name": "Consolidated City",
        "plural": "consolidated cities",
    },
    "172": {
        "name": "Place Within Consolidated City",
        "plural": "",
    },
    "200": {
        "name": "American Indian Reservation with Trust Lands",
        "plural": "",
    },
    "201": {
        "name": "American Indian Reservation with Trust Lands: Reservation Only",
        "plural": "",
    },
    "202": {
        "name": "American Indian Reservations with Trust Lands: Trust Lands Only",
        "plural": "",
    },
    "203": {
        "name": "American Indian Reservation No Trust Lands/Tribal Jurisdiction Sa/Etc",
        "plural": "",
    },
    "204": {
        "name": "American Indian Trust Lands (With No Reservation)",
        "plural": "",
    },
    "205": {
        "name": "American Indian Reservation with Trust Lands: Reservation Only-State",
        "plural": "",
    },
    "206": {
        "name": "American Indian Reservation with Trust Lands: Trust Lands Only-State",
        "plural": "",
    },
    "207": {
        "name": "American Indian Reservation No Trust Lands/Tribal Jurisdiction Sa/Etc-State",
        "plural": "",
    },
    "208": {
        "name": "American Indian Trust Lands (With No Reservation)-State",
        "plural": "",
    },
    "210": {
        "name": "State-American Indian Reservation",
        "plural": "American Indian reservations",
    },
    "211": {
        "name": "State-American Indian Reservation Only",
        "plural": "",
    },
    "212": {
        "name": "State-American Indian Reservation Trust Land Only",
        "plural": "",
    },
    "215": {
        "name": "State-American Indian Reservation Jurisdiction",
        "plural": "",
    },
    "216": {
        "name": "State-American Indian Trust Lands",
        "plural": "",
    },
    "220": {
        "name": "American Indian Reservation Jurisdiction-Co",
        "plural": "",
    },
    "221": {
        "name": "American Indian Trust Lands Only-Co",
        "plural": "",
    },
    "230": {
        "name": "State-Alaska Native Regional Corporation",
        "plural": "",
    },
    "250": {
        "name": "American Indian Area/Alaska Native Area/Hawaiian Home Land",
        "plural": "",
    },
    "252": {
        "name": "American Indian Area/Alaska Native Area (Reservation or Statistical Entity Only)",
        "plural": "",
    },
    "251": {
        "name": "American Indian Area/Alaska Native Area/Hawaiian Home Land-Tribal Subdivision/Remainder",
        "plural": "",
    },
    "253": {
        "name": "American Indian Area/Alaska Native Area (Reservation or Statistical Entity Only)-Tribal Subdivision/Remainder",
        "plural": "",
    },
    "254": {
        "name": "American Indian Area (Off-Reservation Trust Land Only)/Hawaiian Home Land",
        "plural": "",
    },
    "255": {
        "name": "American Indian Area (Off-Reservation Trust Land Only)/Hawaiian Home Land-Tribal Subdivision/Remainder",
        "plural": "",
    },
    "256": {
        "name": "Specified American Indian Area-Tribal Census Tract",
        "plural": "",
    },
    "257": {
        "name": "Specified American Indian Area-Tribal Subdivision/Remainder-Tribal Census Tract",
        "plural": "",
    },
    "259": {
        "name": "Specified American Indian Area-Tribal Subdivision/Remainder-Tribal Census Tract-Tribal Block Group",
        "plural": "",
    },
    "258": {
        "name": "Specified American Indian Area-Tribal Census Tract-Tribal Block Group",
        "plural": "",
    },
    "259": {
        "name": "Specified American Indian Area-Tribal Subdivision/Remainder-Tribal Census Tract-Tribal Block Group",
        "plural": "",
    },
    "260": {
        "name": "American Indian Area/Alaska Native Area/Hawaiian Home Land-State",
        "plural": "",
    },
    "261": {
        "name": "State-American Indian Area/Alaska Native Area/Hawaiian Home Land-County-County Subdivision",
        "plural": "",
    },
    "262": {
        "name": "American Indian Area/Alaska Native Area (Reservation or Statistical Entity Only)-State",
        "plural": "",
    },
    "263": {
        "name": "State-American Indian Area/Alaska Native Area/Hawaiian Home Land-County-County Subdivision-Place/Remainder",
        "plural": "",
    },
    "264": {
        "name": "American Indian Area (Off-Reservation Trust Land Only)/Hawaiian Home Land-State",
        "plural": "",
    },
    "265": {
        "name": "State-American Indian Area/Alaska Native Area (Reservation or Statistical Entity Only)-County-County Subdivision",
        "plural": "",
    },
    "266": {
        "name": "State-American Indian Area/Alaska Native Area (Reservation or Statistical Entity Only)-County-County Subdivision-Place/Remainder",
        "plural": "",
    },
    "267": {
        "name": "State-American Indian Area (Off-Reservation Trust Land Only)/Hawaiian Home Land-County-County Subdivision",
        "plural": "",
    },
    "268": {
        "name": "State-American Indian Area (Off-Reservation Trust Land Only)/Hawaiian Home Land-County-County Subdivision-Place/Remainder",
        "plural": "",
    },
    "269": {
        "name": "American Indian Area/Alaska Native Area/Hawaiian Home Land-Place-Remainder",
        "plural": "",
    },
    "270": {
        "name": "American Indian Area/Alaska Native Area/Hawaiian Home Land-State-County",
        "plural": "",
    },
    "271": {
        "name": "American Indian Area/Alaska Native Area/Hawaiian Home Land-State-County-County Subdivision ",
        "plural": "",
    },
    "272": {
        "name": "American Indian Area/Alaska Native Area (Reservation or Statistical Entity Only)-State-County",
        "plural": "",
    },
    "273": {
        "name": "American Indian Area/Alaska Native Area/Hawaiian Home Land-State-County-County Subdivision-Place/Remainder ",
        "plural": "",
    },
    "274": {
        "name": "American Indian Area (Off-Reservation Trust Land Only)/Hawaiian Home Land-State-County",
        "plural": "",
    },
    "275": {
        "name": "American Indian Area/Alaska Native Area (Reservation or Statistical Entity Only)-State-County-County Subdivision",
        "plural": "",
    },
    "276": {
        "name": "American Indian Area/Alaska Native Area (Reservation or Statistical Entity Only)-State-County-County Subdivision-Place/Remainder",
        "plural": "",
    },
    "277": {
        "name": "American Indian Area (Off-Reservation Trust Land Only)/Hawaiian Home Land-State-County-County Subdivision ",
        "plural": "",
    },
    "278": {
        "name": "American Indian Area (Off-Reservation Trust Land Only)/Hawaiian Home Land-State-County-County Subdivision-Place/Remainder",
        "plural": "",
    },
    "280": {
        "name": "State-American Indian Area/Alaska Native Area/Hawaiian Home Land",
        "plural": "",
    },
    "281": {
        "name": "State-AmericanIndianArea/AlaskaNativeArea/Hawaiian Home Land-Tribal Subdivision/Remainder",
        "plural": "",
    },
    "282": {
        "name": "State-American Indian Area/Alaska Native Area/Hawaiian Home Land-County",
        "plural": "",
    },
    "283": {
        "name": "State-American Indian Area/Alaska Native Area (Reservation or Statistical Entity Only)",
        "plural": "",
    },
    "284": {
        "name": "State-American Indian Area/Alaska Native Area (Reservation or Statistical Entity Only)-Tribal Subdivision/Remainder",
        "plural": "",
    },
    "285": {
        "name": "State-American Indian Area/Alaska Native Area (Reservation or Statistical Entity Only)-County",
        "plural": "",
    },
    "286": {
        "name": "State-American Indian Area (Off-Reservation Trust Land Only)/Hawaiian Home Land",
        "plural": "",
    },
    "287": {
        "name": "State-American Indian Area (Off-Reservation Trust Land Only)/Hawaiian Home Land-Tribal Subdivision/Remainder",
        "plural": "",
    },
    "288": {
        "name": "State-American Indian Area (Off-Reservation Trust Land Only)/Hawaiian Home Land-County",
        "plural": "",
    },
    "290": {
        "name": "American Indian Area/Alaska Native Area/Hawaiian Home Land-Tribal Subdivision/Remainder-State",
        "plural": "",
    },
    "291": {
        "name": "Specified American Indian Area (Reservation Only)-Tribal Census Tract",
        "plural": "",
    },
    "292": {
        "name": "Specified American Indian Area (Off-Reservation Trust Land Only)-Tribal Census Tract",
        "plural": "",
    },
    "293": {
        "name": "Specified American Indian Area (Reservation Only)-Tribal Census Tract-Tribal Block Group",
        "plural": "",
    },
    "294": {
        "name": "Specified American Indian Area (Off-Reservation Trust Land Only)-Tribal Census Tract-Tribal Block Group",
        "plural": "",
    },
    "300": {
        "name": "Metropolitan Statistical Area",
        "plural": "MSAs",
    },
    "301": {
        "name": "Primary Metropolitan Statistical Area",
        "plural": "",
    },
    "310": {
        "name": "Core Based Statistical Area",
        "plural": "CBSAs",
    },
    "311": {
        "name": "Core Based Statistical Area (CBSA)-State",
        "plural": "",
    },
    "312": {
        "name": "Core Based Statistical Area (CBSA)-State-Principal City",
        "plural": "",
    },
    "313": {
        "name": "Core Based Statistical Area (CBSA)-State-County",
        "plural": "",
    },
    "314": {
        "name": "Metropolitan Statistical Area (MSA)/Metropolitan Division",
        "plural": "",
    },
    "315": {
        "name": "Metropolitan Statistical Area (MSA)/Metropolitan Division-State",
        "plural": "",
    },
    "316": {
        "name": "Metropolitan Statistical Area (MSA)/Metropolitan Division-State-County",
        "plural": "",
    },
    "319": {
        "name": "State-Metropolitan Statistical Area (MSA)/Consolidated Metropolitan Statistical Area (CMSA)",
        "plural": "",
    },
    "320": {
        "name": "State-Core Based Statistical Area (CBSA)",
        "plural": "state CBSAs",
    },
    "321": {
        "name": "State-Core Based Statistical Area (CBSA)-Principal City",
        "plural": "",
    },
    "322": {
        "name": "State-Core Based Statistical Area (CBSA)-County",
        "plural": "",
    },
    "323": {
        "name": "State-Metropolitan Statistical Area (MSA)/Metropolitan Division",
        "plural": "",
    },
    "324": {
        "name": "State-Metropolitan Statistical Area (MSA)/Metropolitan Division-County",
        "plural": "",
    },
    "329": {
        "name": "Metropolitan Statistical Area (MSA) (no CMSAs)-State-County",
        "plural": "",
    },
    "330": {
        "name": "Combined Statistical Area",
        "plural": "CSAs",
    },
    "331": {
        "name": "Combined Statistical Area (CSA)-State",
        "plural": "",
    },
    "332": {
        "name": "Combined Statistical Area (CSA)-Core Based Statistical Area (CBSA)",
        "plural": "",
    },
    "333": {
        "name": "Combined Statistical Area (CSA)-Core Based Statistical Area (CBSA)-State",
        "plural": "",
    },
    "335": {
        "name": "Combined New England City and Town Area",
        "plural": "",
    },
    "336": {
        "name": "Combined New England City and Town Area-State",
        "plural": "",
    },
    "337": {
        "name": "Combined New England City and Town Area-New England City and Town Area (NECTA)",
        "plural": "",
    },
    "338": {
        "name": "Combined New England City and Town Area-New England City and Town Area (NECTA)-State",
        "plural": "",
    },
    "340": {
        "name": "State-Combined Statistical Area (CSA)",
        "plural": "",
    },
    "341": {
        "name": "State-Combined Statistical Area (CSA)-Core Based Statistical Area (CBSA)",
        "plural": "",
    },
    "345": {
        "name": "State-Combined New England City and Town Area",
        "plural": "",
    },
    "346": {
        "name": "State-Combined New England City and Town Area-New England City and Town Area",
        "plural": "",
    },
    "350": {
        "name": "New England City and Town Area",
        "plural": "NECTAs",
    },
    "351": {
        "name": "New England City and Town Area (NECTA)-State",
        "plural": "",
    },
    "352": {
        "name": "New England City and Town Area (NECTA)-State-Principal City",
        "plural": "",
    },
    "353": {
        "name": "New England City and Town Area (NECTA)-State-County",
        "plural": "",
    },
    "354": {
        "name": "New England City and Town Area (NECTA)-State-County-County Subdivision",
        "plural": "",
    },
    "355": {
        "name": "New England City and Town Area (NECTA)-NECTA Division",
        "plural": "",
    },
    "356": {
        "name": "New England City and Town Area (NECTA)-NECTA Division-State",
        "plural": "",
    },
    "357": {
        "name": "New England City and Town Area (NECTA)-NECTA Division-State-County",
        "plural": "",
    },
    "358": {
        "name": "New England City and Town Area (NECTA)-NECTA Division-State-County-County Subdivision",
        "plural": "",
    },
    "360": {
        "name": "State-New England City and Town Area (NECTA)",
        "plural": "state NECTAs",
    },
    "361": {
        "name": "State-New England City and Town Area (NECTA)-Principal City",
        "plural": "",
    },
    "362": {
        "name": "State-New England City and Town Area (NECTA)-County",
        "plural": "",
    },
    "363": {
        "name": "State-New England City and Town Area (NECTA)-County-County Subdivision",
        "plural": "",
    },
    "364": {
        "name": "State-New England City and Town Area (NECTA)-NECTA Division",
        "plural": "",
    },
    "365": {
        "name": "State-New England City and Town Area (NECTA)-NECTA Division-County",
        "plural": "",
    },
    "366": {
        "name": "State-New England City and Town Area (NECTA)-NECTA Division-County-County Subdivision",
        "plural": "",
    },
    "370": {
        "name": "New England County Metropolitan Area",
        "plural": "New England county metropolitan areas",
    },
    "371": {
        "name": "New England County Metropolitan Area-State",
        "plural": "",
    },
    "372": {
        "name": "New England County Metropolitan Area-State-Central City",
        "plural": "",
    },
    "373": {
        "name": "New England County Metropolitan Area-State-County",
        "plural": "",
    },
    "374": {
        "name": "State-New England County Metropolitan Area",
        "plural": "",
    },
    "375": {
        "name": "State-New England County Metropolitan Area-Central City",
        "plural": "",
    },
    "376": {
        "name": "State-New England County Metropolitan Area-County",
        "plural": "",
    },
    "380": {
        "name": "Metropolitan Statistical Area (MSA)/Consolidated Metropolitan Statistical Area (CMSA)",
        "plural": "CMSAs",
    },
    "381": {
        "name": "Metropolitan Statistical Area (MSA)/Consolidated Metropolitan Statistical Area (CMSA)-State",
        "plural": "",
    },
    "382": {
        "name": "Metropolitan Statistical Area (MSA)/Consolidated Metropolitan Statistical Area (CMSA)-State-Central City",
        "plural": "",
    },
    "383": {
        "name": "Metropolitan Statistical Area (MSA)/Consolidated Metropolitan Statistical Area (CMSA)-State-County",
        "plural": "",
    },
    "384": {
        "name": "Metropolitan Statistical Area (MSA)/Consolidated Metropolitan Statistical Area (CMSA)-State (New England only)-County-County Subdivision",
        "plural": "",
    },
    "385": {
        "name": "Consolidated Metropolitan Statistical Area (CMSA)-Primary Metropolitan Statistical Area",
        "plural": "",
    },
    "386": {
        "name": "Consolidated Metropolitan Statistical Area (CMSA)-Primary Metropolitan Statistical Area-State",
        "plural": "",
    },
    "387": {
        "name": "Consolidated Metropolitan Statistical Area (CMSA)-Primary Metropolitan Statistical Area-State-County",
        "plural": "",
    },
    "388": {
        "name": "Consolidated Metropolitan Statistical Area (CMSA)-Primary Metropolitan Statistical Area-State (New England only)-County-County Subdivision",
        "plural": "",
    },
    "390": {
        "name": "State-Metropolitan Statistical Area (MSA)/Consolidated Metropolitan Statistical Area (CMSA)",
        "plural": "",
    },
    "391": {
        "name": "State-Metropolitan Statistical Area (MSA)/Consolidated Metropolitan Statistical Area (CMSA)-Central City",
        "plural": "",
    },
    "392": {
        "name": "State-Metropolitan Statistical Area (MSA)/Consolidated Metropolitan Statistical Area (CMSA)-County",
        "plural": "",
    },
    "393": {
        "name": "State (New England only)-Metropolitan Statistical Area (MSA)/Consolidated Metropolitan Statistical Area (CMSA)-County-County Subdivision",
        "plural": "",
    },
    "395": {
        "name": "State-Consolidated Metropolitan Statistical Area (CMSA)-Primary Metropolitan Statistical Area",
        "plural": "",
    },
    "396": {
        "name": "State-Consolidated Metropolitan Statistical Area (CMSA)-Primary Metropolitan Statistical Area-County",
        "plural": "",
    },
    "397": {
        "name": "State (New England only)-Consolidated Metropolitan Statistical Area (CMSA)-Primary Metropolitan Statistical Area-County-County Subdivision",
        "plural": "",
    },
    "400": {
        "name": "Urban Area",
        "plural": "urban areas",
    },
    "410": {
        "name": "Urban Area-State",
        "plural": "",
    },
    "420": {
        "name": "State-Urban Area",
        "plural": "state urban areas",
    },
    "430": {
        "name": "Urban Area-State-County",
        "plural": "",
    },
    "431": {
        "name": "State-Urban Area-County",
        "plural": "",
    },
    "440": {
        "name": "Urban Area-State-County-County Subdivision",
        "plural": "",
    },
    "441": {
        "name": "State-Urban Area-County-County Subdivision",
        "plural": "",
    },
    "450": {
        "name": "Urban Area-State-County-County Subdivision-Place/Remainder",
        "plural": "",
    },
    "451": {
        "name": "State-Urban Area-County-County Subdivision-Place/Remainder",
        "plural": "",
    },
    "460": {
        "name": "Urban Area-State-Central Place",
        "plural": "",
    },
    "461": {
        "name": "State-Urban Area-Central Place",
        "plural": "",
    },
    "462": {
        "name": "Urban Area-State-Consolidated City",
        "plural": "",
    },
    "463": {
        "name": "State-Urban Area-Consolidated City",
        "plural": "",
    },
    "464": {
        "name": "Urban Area-State-Consolidated City-Place Within Consolidated City",
        "plural": "",
    },
    "465": {
        "name": "State-Urban Area-Consolidated City-Place Within Consolidated City",
        "plural": "",
    },
    "500": {
        "name": "Congressional District",
        "plural": "congressional districts",
    },
    "510": {
        "name": "Congressional District-County",
        "plural": "",
    },
    "511": {
        "name": "Congressional District-County-Census Tract",
        "plural": "",
    },
    "521": {
        "name": "Congressional District-County-County Subdivision",
        "plural": "",
    },
    "531": {
        "name": "Congressional District-Place/Remainder",
        "plural": "",
    },
    "541": {
        "name": "Congressional District-Consolidated City",
        "plural": "",
    },
    "542": {
        "name": "Congressional District-Consolidated City-Place Within Consolidated City",
        "plural": "",
    },
    "550": {
        "name": "Congressional District-American Indian Area/Alaska Native Area/Hawaiian Home Land",
        "plural": "",
    },
    "551": {
        "name": "Congressional District-American Indian Area/Alaska Native Area (Reservation or Statistical Entity Only)",
        "plural": "",
    },
    "552": {
        "name": "Congressional District-American Indian Area (Off-Reservation Trust Land Only)/Hawaiian Home Land",
        "plural": "",
    },
    "553": {
        "name": "Congressional District-American Indian Area/Alaska Native Area/Hawaiian Home Land-Tribal Subdivision/Remainder",
        "plural": "",
    },
    "554": {
        "name": "Congressional District-American Indian Area/Alaska Native Area (Reservation or Statistical Entity Only)-Tribal Subdivision/Remainder",
        "plural": "",
    },
    "555": {
        "name": "Congressional District-American Indian Area (Off-Reservation Trust Land Only)/Hawaiian Home Land-Tribal Subdivision/Remainder",
        "plural": "",
    },
    "560": {
        "name": "Congressional District-Alaska Native Regional Corporation",
        "plural": "",
    },
    "610": {
        "name": "State Senate District",
        "plural": "state senate districts",
    },
    "612": {
        "name": "State Senate District-County",
        "plural": "",
    },
    "613": {
        "name": "State Senate District-County-Minor Civil Division (MCD)-Place",
        "plural": "",
    },
    "614": {
        "name": "State Senate District-Place",
        "plural": "",
    },
    "620": {
        "name": "State House District",
        "plural": "state house districts",
    },
    "622": {
        "name": "State House District-County",
        "plural": "",
    },
    "623": {
        "name": "State House District-County-Minor Civil Division (MCD)-Place",
        "plural": "",
    },
    "624": {
        "name": "State House District-Place",
        "plural": "",
    },
    "700": {
        "name": "Voting Tabulation District",
        "plural": "VTDs",
    },
    "740": {
        "name": "Block Group [split by Voting Tabulation District (VTD), Minor Civil Division (MCD), and Place]",
        "plural": "",
    },
    "750": {
        "name": "Census Block (pl94 files)",
        "plural": "Census blocks (pl94 files)",
    },
    "795": {
        "name": "State-Public Use Microdata Sample Area (PUMA)",
        "plural": "",
    },
    "850": {
        "name": "3-digit ZIP Code Tabulation Area",
        "plural": "ZCTA3s",
    },
    "851": {
        "name": "State-3-digit ZIP Code Tabulation Area (ZCTA3)",
        "plural": "",
    },
    "852": {
        "name": "State-3-digit ZIP Code Tabulation Area (ZCTA3)-County",
        "plural": "",
    },
    "860": {
        "name": "ZIP Code Tabulation Area",
        "plural": "ZCTA5s",
    },
    "870": {
        "name": "5-digit ZIP Code Tabulation Area (ZCTA5)-State",
        "plural": "",
    },
    "871": {
        "name": "State-5-digit ZIP Code Tabulation Area (ZCTA5)",
        "plural": "",
    },
    "880": {
        "name": "5-digit ZIP Code Tabulation Area (ZCTA5)-County",
        "plural": "",
    },
    "881": {
        "name": "State-5-digit ZIP Code Tabulation Area (ZCTA5)-County",
        "plural": "",
    },
    "901": {
        "name": "County Set",
        "plural": "county sets",
    },
    "930": {
        "name": "Metropolitan Planning Organization Region (CTPP)",
        "plural": "",
    },
    "935": {
        "name": "State-County-Combined Zone (CTPP)",
        "plural": "",
    },
    "940": {
        "name": "State-County-Traffic Analysis Zone (CTPP)",
        "plural": "",
    },
    "950": {
        "name": "Elementary School District",
        "plural": "elementary school districts",
    },
    "960": {
        "name": "Secondary School District",
        "plural": "secondary school districts",
    },
    "970": {
        "name": "Unified School District",
        "plural": "unified school districts",
    },
}
