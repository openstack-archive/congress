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

from django.conf.urls import patterns
from django.conf.urls import url

from congress_dashboard.datasources import views as data_views
from congress_dashboard.policies.rules import views as rule_views
from congress_dashboard.policies import views


POLICY = r'^(?P<policy_name>[^/]+)/%s$'
POLICYTABLE = r'^(?P<datasource_id>[^/]+)/(?P<policy_table_name>[^/]+)/%s$'


urlpatterns = patterns(
    '',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(POLICY % 'detail', views.DetailView.as_view(), name='detail'),
    url(POLICYTABLE % 'detail', data_views.DetailView.as_view(),
        name='policy_table_detail'),
    url(POLICY % 'rules/create',
        rule_views.CreateView.as_view(), name='create_rule'),
)
