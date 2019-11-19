#!/home/vlt-os/env/bin/python
"""This file is part of Vulture OS.

Vulture OS is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Vulture OS is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Vulture OS.  If not, see http://www.gnu.org/licenses/.
"""
__author__ = "Kevin GUILLEMOT"
__credits__ = []
__license__ = "GPLv3"
__version__ = "4.0.0"
__maintainer__ = "Vulture OS"
__email__ = "contact@vultureproject.org"
__doc__ = 'Listeners URLS'

# Django system imports
from django.urls import path, re_path

# Django project imports
from services.frontend import views, api
from services.generic_list import ListFrontend


urlpatterns = [
    path('services/frontend/', ListFrontend.as_view(), name="services.frontend.list"),

    re_path('^services/frontend/delete/(?P<object_id>[A-Fa-f0-9]+)$',
            views.frontend_delete,
            name="services.frontend.delete"),

    re_path('^services/frontend/edit/(?P<object_id>[A-Fa-f0-9]+)?$',
            views.frontend_edit,
            name="services.frontend.edit"),

    re_path('^services/frontend/clone/(?P<object_id>[A-Fa-f0-9]+)$',
            views.frontend_clone,
            name="services.frontend.clone"),

    re_path('^services/frontend/start/(?P<object_id>[A-Fa-f0-9]+)$',
            views.frontend_start,
            name="services.frontend.start"),

    re_path('^services/frontend/pause/(?P<object_id>[A-Fa-f0-9]+)$',
            views.frontend_pause,
            name="services.frontend.pause"),

    re_path('^services/frontend/test_apiparser/',
            views.frontend_test_apiparser,
            name="services.frontend.test_apiparser"),

    path('api/services/frontend/test_conf/', api.frontend_test_conf, name="services.frontend.test_conf"),

    path('api/v1/services/frontend/', api.FrontendAPIv1.as_view(), name="services.frontend.api"),

    path('api/v1/services/frontend/<int:object_id>/', api.FrontendAPIv1.as_view(), name="services.frontend.api"),

    path('api/v1/services/frontend/<int:object_id>/<str:action>/',
         api.FrontendAPIv1.as_view(),
         name="services.frontend.api"),
]
