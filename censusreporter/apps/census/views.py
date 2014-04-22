from __future__ import division
import requests
from collections import OrderedDict
from urllib2 import unquote

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.utils import simplejson
from django.utils.safestring import SafeString
from django.views.generic import View, TemplateView

from api import LocationNotFound
from api.controller import (get_census_profile, get_geography, get_locations,
                            get_elections_profile)

from .utils import (LazyEncoder, get_ratio, SUMMARY_LEVEL_DICT)

import logging
logger = logging.getLogger(__name__)


### UTILS ###

def render_json_to_response(context):
    '''
    Utility method for rendering a view's data to JSON response.
    '''
    result = simplejson.dumps(context, sort_keys=False, indent=4)
    return HttpResponse(result, mimetype='application/javascript')

def find_key(dictionary, searchkey):
    stack = [dictionary]
    while stack:
        d = stack.pop()
        if searchkey in d:
            return d[searchkey]
        for key, value in d.iteritems():
            if isinstance(value, dict) or isinstance(value, OrderedDict):
                stack.append(value)

def find_keys(dictionary, searchkey):
    stack = [dictionary]
    values_list = []
    while stack:
        d = stack.pop()
        if searchkey in d:
            values_list.append(d[searchkey])
        for key, value in d.iteritems():
            if isinstance(value, dict) or isinstance(value, OrderedDict):
                stack.append(value)

    return values_list

def find_dicts_with_key(dictionary, searchkey):
    stack = [dictionary]
    dict_list = []
    while stack:
        d = stack.pop()
        if searchkey in d:
            dict_list.append(d)
        for key, value in d.iteritems():
            if isinstance(value, dict) or isinstance(value, OrderedDict):
                stack.append(value)

    return dict_list


### DETAIL ###

class GeographyDetailView(TemplateView):
    template_name = 'profile/profile.html'

    def enhance_api_data(self, api_data):
        dict_list = find_dicts_with_key(api_data, 'values')
        
        for d in dict_list:
            values = d['values']
            geo_value = values['this']

            # add the context value to `values` dict
            for sumlevel in ['province', 'country']:
                if sumlevel in values:
                    values[sumlevel+'_index'] = get_ratio(geo_value, values[sumlevel])

        return api_data

    def get_context_data(self, *args, **kwargs):
        geo_level = kwargs['geo_level']
        geo_code = kwargs['geo_code']

        try:
            geo = get_geography(geo_code, geo_level)
            profile_data = get_census_profile(geo_code, geo_level)
            profile_data['elections'] = get_elections_profile(geo_code, geo_level)
        except (ValueError, LocationNotFound):
            raise Http404

        profile_data = self.enhance_api_data(profile_data)
        page_context = {
            'geography': geo,
            'geo_code': geo_code,
            'geo_level': geo_level,
        }
        page_context.update(profile_data)
        page_context.update({
            'profile_data_json': SafeString(simplejson.dumps(profile_data, cls=LazyEncoder))
        })

        return page_context


class PlaceSearchJson(View):
    def get(self, request, *args, **kwargs):
        if 'q' in request.GET:
            search_term = request.GET['q']
            geo_level = request.GET.get('geolevel', None)
            return render_json_to_response(
                {'results': get_locations(search_term, geo_level)}
            )

        return HttpResponseBadRequest('"q" parameter is required')


class WardSearchProxy(View):

    def get(self, request, *args, **kwargs):
        try:
            resp = requests.get('http://wards.code4sa.org',
                                params={'address': request.GET['address'],
                                        'database': 'wards_2011'})
            if resp.status_code != 200:
                return HttpResponseBadRequest()
            elif resp.text.strip().startswith('{'):
                return HttpResponse(self.pad_content(request, '[]'),
                                    mimetype='application/javascript')
            return HttpResponse(self.pad_content(request, resp.text),
                                mimetype='application/javascript')
        except (KeyError, AttributeError):
            return HttpResponseBadRequest()

    def pad_content(self, request, content):
        if 'callback' in request.GET:
            return '%s(%s);' % (request.GET['callback'], content)
        return content


class LocateView(TemplateView):
    template_name = 'locate/locate.html'

    def get_api_data(self, lat, lon):
        '''
        Retrieves data from the comparison endpoint at api.censusreporter.org.
        '''
        API_ENDPOINT = settings.API_URL + '/1.0/geo/search'
        API_PARAMS = {
            'lat': lat,
            'lon': lon,
            'sumlevs': '010,020,030,040,050,060,140,160,250,310,400,500,610,620,860,950,960,970'
        }

        r = requests.get(API_ENDPOINT, params=API_PARAMS)

        if r.status_code == 200:
            data = simplejson.loads(r.text, object_pairs_hook=OrderedDict)
        else:
            raise Http404

        return data['results']

    def get_context_data(self, *args, **kwargs):
        page_context = {}
        lat = self.request.GET.get('lat', None)
        lon = self.request.GET.get('lon', None)

        if lat and lon:
            places = self.get_api_data(lat, lon)
            for place in places:
                place['sumlev_name'] = SUMMARY_LEVEL_DICT[place['sumlevel']]['name']

            page_context.update({
                'location': {
                    'lat': lat,
                    'lon': lon
                },
                'places': places
            })

        return page_context
