#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
from io import BytesIO
import requests

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.six.moves.urllib_parse import urljoin
from passerelle.compat import json_loads
from passerelle.base.models import BaseResource
from passerelle.utils.api import endpoint
from passerelle.utils.jsonresponse import APIError


class imio_atal(BaseResource):
    base_url = models.URLField(
        max_length=256,
        blank=False,
        verbose_name=_("Base URL"),
        help_text=_("API base URL"),
    )
    api_key = models.CharField(max_length=128, verbose_name=_("API Key"))

    category = _("Business Process Connectors")

    class Meta:
        verbose_name = "Connecteur Atal (iMio)"

    @classmethod
    def get_verbose_name(cls):
        return cls._meta.verbose_name

    @endpoint(perm='can_access', description=_('Test methods'))
    def Test(self, request):
        atal_response = requests.get(
            url=self.base_url + "api/Test",
            headers={"Accept": "text/plain", "X-API-Key": self.api_key},
        )
        atal_response_format = "{} - {}".format(
            atal_response.status_code, atal_response.text
        )
        return atal_response_format

    @endpoint(
        perm='can_access',
        description=_('Post '),
        methods=['post'],
        parameters={
            'atal_requester_id': {
                'description': "Numéro de l'utilisateur demandeur dans ATAL",
                'type': 'integer',
            },
            'atal_contact_firstname': {
                'description': "Prénom du contact transmis vers ATAL",
                'type': 'string',
            },
            'atal_contact_lastname': {
                'description': "Nom du contact transmis vers ATAL",
                'type': 'string',
            },
            'atal_contact_email': {
                'description': "Adresse mail du contact transmis vers ATAL",
                'type': 'string',
            },
            'atal_contact_phone': {
                'description': "Numéro de téléphone du contact transmis vers ATAL",
                'type': 'string',
            },
            'atal_contact_mobile': {
                'description': "Numéro de mobile du contact transmis vers ATAL",
                'type': 'string',
            },
            'atal_contact_address': {
                'description': "Adresse du contact transmis vers ATAL",
                'type': 'string',
            },
            'atal_contact_zipcode': {
                'description': "Code postal du contact transmis vers ATAL",
                'type': 'string',
            },
            'atal_contact_city': {
                'description': "Localité du contact transmis vers ATAL",
                'type': 'string',
            },
            "atal_operator": {
                'description': "Nom de l'opérateur",
                'type': "string",
            },
            "atal_object": {
                'description': "Objet de la demande",
                'type': "string",
            },
            "atal_description": {
                'description': "Description de la demande",
                'type': "string",
            },
            "atal_desired_date": {
                'description': "Date désirée pour la demande (ex: 2021-06-16T13:30:25.365Z)",
                'type': "string",
            },
            "atal_recipient_id": {
                'description': "Numéro identifiant du destinataire",
                'type': "integer",
            },
            "atal_requesting_department_id": {
                'description': "Numéro identifiant du département demandeur",
                'type': "integer",
            },
            "atal_request_type": {
                'description': "Numéro identifiant du type de requête",
                'type': "integer",
            },
            "atal_request_date": {
                'description': "Date de la requête",
                'type': "string",
            },
            "atal_localization": {
                'description': "Lieu de l'intervention",
                'type': "string",
            },
            "atal_patrimony_id": {
                'description': "Numéro identifiant du patrimoine",
                'type': "integer",
            },
            "atal_longitude": {
                'description': "Coordonée longitude du lieu de l'intervention",
                'type': "integer",
            },
            "atal_latitude": {
                'description': "Coordonée latitude du lieu de l'intervention",
                'type': "integer",
            },
        },
    )
    def create_work_request(self, request, *args, **kwargs):
        data_from_publik = json_loads(request.body)
        # commented parameters below are not required
        data_to_atal = {
            "RequesterId": data_from_publik["atal_requester_id"],
            # "Operator": data_from_publik["atal_operator"],
            "Object": data_from_publik["atal_object"],
            "Description": data_from_publik["atal_description"],
            # "DesiredDate": data_from_publik["atal_desired_date"],
            "RecipientId": data_from_publik["atal_recipient_id"],
            "RequestingDepartmentId": data_from_publik["atal_requesting_department_id"],
            "RequestType": data_from_publik["atal_request_type"],
            # "RequestDate": data_from_publik["atal_request_date"],
            "Localization": data_from_publik["atal_localization"],
            # "PatrimonyId": data_from_publik["atal_patrimony_id"],
            "Longitude": data_from_publik["atal_longitude"],
            "Latitude": data_from_publik["atal_latitude"],
        }
        # Raw data that works locally with Postman or Python request
        """
        data_to_atal = {
            "RequesterId": 13,
            "RecipientId": 1004,
            "RequestingDepartmentId": 690,
            "Localization": "Bruxelles",
            "latitude": 50.844998072856825,
            "longitude": 4.349986346839887,
            "Object": "Test via Python request (objet)",
            "Description": "Test via Python request (description)",
            "RequestType": 1001,
        }
        """
        response = self.requests.post(
            urljoin(self.base_url, '/api/WorksRequests'),
            json=data_to_atal,
            headers={
                "accept": "application/json",
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            },
        )
        # Error handling (WIP)
        """
        if response.raise_for_status():
            error_desc = {'message': response.text}
            raise APIError(
                '{} (HTTP error {})'.format(response.text, response.status_code),
                data=error_desc,
            )
        else:
        """
        response_json = response.json()
        return {'data': response_json}

    @endpoint(
        perm='can_access',
        description=_('Post '),
        methods=['post'],
        parameters={
            "atal_work_request_uuid": {
                "description": "Numéro d'identification uuid de la demande dans ATAL.",
                "type": "string",
                # "example_value": "11865d87-336b-49b3-e181-08d76f93d6b4",
            },
            "atal_attachment1": {
                "description": "Fichier 1",
            },
        },
    )
    def post_attachment(self, request, *args, **kwargs):
        data_from_publik = json_loads(request.body)

        decoded_image = base64.b64decode(
            data_from_publik["atal_attachment1"]["content"]
        )
        image_for_atal = BytesIO(decoded_image)

        response = self.requests.post(
            urljoin(
                self.base_url,
                '/api/WorksRequests/'
                + data_from_publik["atal_work_request_uuid"]
                + '/Attachments',
            ),
            headers={
                "X-API-Key": self.api_key,
            },
            files={
                'file': (
                    data_from_publik["atal_attachment1"]["filename"],
                    image_for_atal,
                    data_from_publik["atal_attachment1"]["content_type"],
                )
            },
        )

        if response.raise_for_status():
            error_desc = {'message': response.text}
            raise APIError(
                '{} (HTTP error {})'.format(response.text, response.status_code),
                data=error_desc,
            )
        else:
            response = response.json()

        return {'data': response}
