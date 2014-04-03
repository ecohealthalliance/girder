#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import cherrypy
import os

from girder.constants import ROOT_DIR
from . import docs
from .rest import Resource, RestException

"""
Whenever we add new return values or new options we should increment the
maintenance value. Whenever we add new endpoints, we should increment the minor
version. If we break backward compatibility in any way, we should increment the
major version.
"""
API_VERSION = "1.0.0"


class Description(object):
    """
    This class provides convenient chainable semantics to allow api route
    handlers to describe themselves to the documentation. A route handler
    function can set a description property on itself to an instance of this
    class in order to describe itself.
    """
    def __init__(self, summary):
        self._summary = summary
        self._params = []
        self._errorResponses = []
        self._responseClass = None
        self._notes = None

    def asDict(self):
        """
        Returns this description object as an appropriately formatted dict
        """
        return {
            'summary': self._summary,
            'notes': self._notes,
            'parameters': self._params,
            'errorResponses': self._errorResponses,
            'responseClass': self._responseClass
        }

    def responseClass(self, obj):
        self._responseClass = obj
        return self

    def param(self, name, description, paramType='query', dataType='string',
              required=True):
        """
        This helper will build a parameter declaration for you. It has the most
        common options as defaults, so you won't have to repeat yourself as much
        when declaring the APIs.
        """
        self._params.append({
            'name': name,
            'description': description,
            'paramType': paramType,
            'dataType': dataType,
            'allowMultiple': False,
            'required': required
        })
        return self

    def notes(self, notes):
        self._notes = notes
        return self

    def errorResponse(self, reason='A parameter was invalid.', code=400):
        """
        This helper will build an errorResponse declaration for you. Many
        endpoints will be able to use the default parameter values for one of
        their responses.
        """
        self._errorResponses.append({
            'message': reason,
            'code': code
        })
        return self


class ApiDocs(object):
    exposed = True

    def GET(self, **params):
        return cherrypy.lib.static.serve_file(os.path.join(
            ROOT_DIR, 'clients', 'web', 'static', 'built', 'swagger',
            'swagger.html'), content_type='text/html')


class Describe(Resource):
    def __init__(self):
        self.route('GET', (), self.listResources, nodoc=True)
        self.route('GET', (':resource',), self.describeResource, nodoc=True)

    def listResources(self, params):
        protocol = cherrypy.url().split(':')[0]
        return {
            'apiVersion': API_VERSION,
            'swaggerVersion': '1.2',
            'basePath': "%s://%s/describe" % (protocol, cherrypy.config['server']['api_root']),
            'apis': [{'path': '/{}'.format(resource)}
                     for resource in sorted(docs.discovery)]
        }

    def describeResource(self, resource, params):
        if not resource in docs.routes:
            raise RestException('Invalid resource: {}'.format(resource))

        protocol = cherrypy.url().split(':')[0]
        return {
            'apiVersion': API_VERSION,
            'swaggerVersion': '1.2',
            'basePath': "%s://%s" % (protocol, cherrypy.config['server']['api_root']),
            'apis': [{'path': route, 'operations': ops}
                     for route, ops in docs.routes[resource].iteritems()]
        }
