# Copyright 2014 VMware.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.admin.policies.policies \
    import urls as policies_urls
from openstack_dashboard.dashboards.admin.policies import views

urlpatterns = patterns(
    '',
    url(r'^$',
        views.IndexView.as_view(),
        name='index'),
    url(r'^\?tab=policies_group_tabs__policies_tab$',
        views.IndexView.as_view(),
        name='policies_tab'),
    url(r'^\?tab=policies_group_tabs__datasources_tab$',
        views.IndexView.as_view(),
        name='datasources_tab'),
    url(r'', include(policies_urls, namespace='policies')),
)
