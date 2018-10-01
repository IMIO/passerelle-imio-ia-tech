#!/usr/bin/env python
# -*- coding: utf-8 -*-
# passerelle-imio-ts-atal - passerelle connector to ATAL.
# Copyright (C) 2016  Entr'ouvert
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# https://demo-pm.imio.be/ws4pm.wsdl
# https://demo-pm.imio.be/
# http://trac.imio.be/trac/browser/communesplone/imio.pm.wsclient/trunk/src/imio/pm/wsclient/browser/settings.py#L211
# http://svn.communesplone.org/svn/communesplone/imio.pm.ws/trunk/docs/README.txt

# Decorateurs des endpoints:
# serializer_type='json-api' : Permet de serializer la reponse directement dans un data + format automatique pour un raise exception.
import base64
import json
import magic
import suds

from requests.exceptions import ConnectionError
from django.db import models
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse, Http404

from passerelle.base.models import BaseResource
from passerelle.utils.api import endpoint
from passerelle.utils.jsonresponse import APIError
from .soap import get_client as soap_get_client

from suds.xsd.doctor import ImportDoctor, Import
from suds.transport.http import HttpAuthenticated

def get_client(model):
    try:
        return soap_get_client(model)
    except ConnectionError as e:
        raise APIError('i-ImioAtal error: %s' % e)


def format_type(t):
    return {'id': unicode(t), 'text': unicode(t)}


def format_file(f):
    return {'status': f.status, 'id': f.nom, 'timestamp': f.timestamp}


class FileError(Exception):
    pass


class FileNotFoundError(Exception):
    http_status = 404


class IImioAtal(BaseResource):
    wsdl_url = models.CharField(max_length=128, blank=False,
            verbose_name=_('WSDL URL'),
            help_text=_('WSDL URL'))
    verify_cert = models.BooleanField(default=True,
            verbose_name=_('Check HTTPS Certificate validity'))
    username = models.CharField(max_length=128, blank=True,
            verbose_name=_('Username'))
    password = models.CharField(max_length=128, blank=True,
            verbose_name=_('Password'))
    keystore = models.FileField(upload_to='iparapheur', null=True, blank=True,
            verbose_name=_('Keystore'),
            help_text=_('Certificate and private key in PEM format'))

    category = _('Business Process Connectors')

    class Meta:
        verbose_name = _('i-ImioAtal')

    @classmethod
    def get_verbose_name(cls):
        return cls._meta.verbose_name

    @endpoint()
    def test(self):
        return 'True'

    @endpoint(serializer_type='json-api', perm='can_access')
    def testConnection(self, request):
        client = get_client(self)
        return dict(client.service.testConnection(''))

    # https://demo-atal.imio-app.be/awa/services/DemandeService?wsdl    
    @endpoint(serializer_type='json-api', perm='can_access', methods=['post'])
    def insertDemande(self, request):
        data = dict([(x, request.GET[x]) for x in request.GET.keys()])
        if request.body:
            load = json.loads(request.body)
            # get fields from form.
            data.update(load.get("fields"))
            ws_params = load['extra']
            client = get_client(self)
            if ws_params['coordX'] is None or ws_params['coordY'] is None:
                return client.service.insertDemande(ws_params['contactNom'],
                                                 ws_params['contactTelephone'],
                                                 ws_params['contactCourriel'],
                                                 ws_params['contactAdresse'],
                                                 ws_params['demandeObjet'],
                                                 ws_params['demandeLieu'],
                                                 ws_params['demandeDescription'],
                                                 ws_params['remoteAddress'],
                                                 ws_params['codeEquipement'],
                                                 ws_params['codeServiceDemandeur'],
                                                 ws_params['dateSouhaitee'])
            else:
                return self.insertDemandeXYByType(ws_params['contactNom'], 
                                                 ws_params['contactTelephone'],
                                                 ws_params['contactCourriel'],
                                                 ws_params['contactAdresse'],
                                                 ws_params['demandeObjet'],
                                                 ws_params['demandeLieu'],
                                                 ws_params['demandeDescription'],
                                                 ws_params['remoteAddress'],
                                                 ws_params['codeEquipement'],
                                                 ws_params['codeServiceDemandeur'],
                                                 ws_params['dateSouhaitee'],
                                                 ws_params['typeDemande'],
                                                 ws_params['coordX'],
                                                 ws_params['coordY'])
        else:
            return False

    @endpoint(serializer_type='json-api', perm='can_access', methods=['post'])
    def upload(self, request):
        data = dict([(x, request.GET[x]) for x in request.GET.keys()])
        extraAttrs = {}
        if request.body:
            load = json.loads(request.body)
            # get fields from form.
            data.update(load.get("fields"))
            ws_params = load['extra']
            client = get_client(self)
            client.service.upload(ws_params['numeroDemande'],
                                ws_params['fileName'],
                                ws_params['fileContent'])
            return True
        else:
            return False
