from django.conf.urls import url, patterns, include
from django.contrib import admin
from django.views.generic import TemplateView

from .views import (GeographyDetailView, PlaceSearchJson, LocateView,
                    WardSearchProxy)


admin.autodiscover()

geo_levels = 'ward|municipality|province'


urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),

    url(
        regex   = '^$',
        view    = TemplateView.as_view(template_name="homepage.html"),
        kwargs  = {},
        name    = 'homepage',
    ),

    url(
        regex   = '^how-to/$',
        view    = TemplateView.as_view(template_name="how_to.html"),
        kwargs  = {},
        name    = 'how-to',
    ),

    url(
        regex   = '^place-search/json/$',
        view    = PlaceSearchJson.as_view(),
        kwargs  = {},
        name    = 'place_search_json',
    ),

    url(
        regex   = '^ward-search/json/$',
        view    = WardSearchProxy.as_view(),
        kwargs  = {},
        name    = 'ward_search_json',
    ),

    url(
        regex   = '^locate/$',
        view    = LocateView.as_view(),
        kwargs  = {},
        name    = 'locate',
    ),

    # e.g. /profiles/16000US5367000/ (Spokane, WA)
    url(
        regex   = '^profiles/(?P<geo_level>%s)-(?P<geo_code>[\w]+)/$' % geo_levels,
        view    = GeographyDetailView.as_view(),
        kwargs  = {},
        name    = 'geography_detail',
    ),
)
