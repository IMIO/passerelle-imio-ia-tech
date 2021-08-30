import base64
from io import BytesIO

import requests
from django.db import models
from django.http import JsonResponse
from django.utils.six.moves.urllib_parse import urljoin
from passerelle.base.models import BaseResource
from passerelle.compat import json_loads
from passerelle.utils.api import endpoint
from passerelle.utils.jsonresponse import APIError


# TODO : we should rename this class name with something like AtalConnector
class imio_atal(BaseResource):
    base_url = models.URLField(
        max_length=256,
        blank=False,
        verbose_name="Base URL",
        help_text="Base URL sans slash à la fin, comme ceci : https://example.net",
    )
    api_key = models.CharField(
        max_length=128,
        verbose_name="API Key",
    )
    api_description = "Connecteur permettant d'intéragir avec une instance d'Atal V6"
    category = "Connecteurs iMio"

    class Meta:
        verbose_name = "Connecteur Atal (iMio)"

    @endpoint(
        perm="can_access",
        description="Test methods",
    )
    def test(self, request):
        atal_response = requests.get(
            url=f"{self.base_url}/api/Test",
            headers={"Accept": "text/plain", "X-API-Key": self.api_key},
        )
        atal_response_format = "{} - {}".format(atal_response.status_code, atal_response.text)
        return atal_response_format

    @endpoint(
        perm="can_access",
        description="Créer une demande de travaux dans Atal",
        methods=["post"],
    )
    def create_work_request(self, request):
        post_data = json_loads(request.body)
        # commented parameters below are not required
        # TODO : use post_data.get('mavar', '') if MaVar is optionnal
        data_to_atal = {
            "Contact": {
                "FirstName": post_data["atal_contact_firstname"],
                "LastName": post_data["atal_contact_lastname"],
                "Email": post_data["atal_contact_email"],
                "Phone": post_data["atal_contact_phone"],
                "Mobile": post_data["atal_contact_mobile"],
                "Address1": post_data["atal_contact_address"],
                "ZipCode": post_data["atal_contact_zipcode"],
                "City": post_data["atal_contact_city"],
            },
            "RequesterId": post_data["atal_requester_id"],
            # "Operator": post_data["atal_operator"],
            "Object": post_data["atal_object"],
            "Description": post_data["atal_description"],
            # "DesiredDate": post_data["atal_desired_date"],
            "RecipientId": post_data["atal_recipient_id"],
            "RequestingDepartmentId": post_data["atal_requesting_department_id"],
            "RequestType": post_data["atal_request_type"],
            # "RequestDate": post_data["atal_request_date"],
            "Localization": post_data["atal_localization"],
            # "PatrimonyId": post_data["atal_patrimony_id"],
            "Longitude": post_data["atal_longitude"],
            "Latitude": post_data["atal_latitude"],
        }
        # Raw data that works locally with Postman or Python request on atal demo
        # TODO : adapt and move them to schema
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
            f"{self.base_url}/api/WorksRequests",  # Endpoints are described in ATAl Swagger
            json=data_to_atal,
            headers={
                "accept": "application/json",
                # X-API-KEY is visible in ATAL admin panel
                # and set in the passerelle connector settings.
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            },
        )

        # TODO : create an utilitary method to handle status_code >= 400
        if response.status_code >= 400:
            data = {
                "error": "Bad Gateway or Proxy error",
                "message": f"Erreur Atal {response.status_code} {response.reason}",
                "url": f"{self.base_url}",
            }
            return JsonResponse(data, status=502)

        return {"data": response.json()}

    @endpoint(
        perm="can_access",
        description="Post files and join them to and ATAL work request.",
        methods=["post"],
        parameters={},
    )
    def post_attachment(self, request):
        post_data = json_loads(request.body)
        # ATAL 6 require a multipart/formdata request
        # with a bytes encoded file. That's why we use
        # BytesIO here to convert Base64 image from wcs to bytes
        decoded_image = base64.b64decode(post_data["atal_attachment1"]["content"])
        image_for_atal = BytesIO(decoded_image)
        # uuid is fetched from ATAL work request creation response in wcs vars
        work_request_uuid = post_data["atal_work_request_uuid"]
        # X-API-KEY is visible in ATAL admin panel
        # and set in the passerelle connector settings.
        headers = {
            "X-API-Key": self.api_key,
        }
        # This is multipart/formdata http request file syntax
        files = {
            "file": (
                post_data["atal_attachment1"]["filename"],
                image_for_atal,
                post_data["atal_attachment1"]["content_type"],
            )
        }
        response = self.requests.post(
            f"{self.base_url}/api/WorksRequests/{work_request_uuid}/Attachments", headers=headers, files=files
        )

        # TODO : create an utilitary method to handle status_code >= 400
        if response.status_code >= 400:
            data = {
                "error": "Bad Gateway or Proxy error",
                "message": f"Erreur Atal {response.status_code} {response.reason}",
                "url": f"{self.base_url}",
            }
            return JsonResponse(data, status=502)

        return {"data": response.json()}  # must return dict

    @endpoint(
        perm="can_access",
        description="Return work request details from ATAL.",
        methods=["post"],
        parameters={
            "atal_work_request_uuid": {
                "description": "Numéro d'identification uuid de la demande dans ATAL.",
                "type": "string",
                "example_value": "11865d87-336b-49b3-e181-08d76f93d6b4",
            },
        },
    )
    def get_work_request_details(self, request, *args, **kwargs):
        post_data = json_loads(request.body)  # http data from wcs webservice

        # ATAL 6 require uuid in the url as an endpoint
        # for example :
        # https://demov6.imio-app.be/api/WorksRequests/11865d87-336b-49b3-e181-08d76f93d6b4
        uuid = post_data["atal_work_request_uuid"]
        url = f"{self.base_url}/api/WorksRequests/{uuid}"
        headers = {
            "accept": "application/json",
            # X-API-KEY is visible in ATAL admin panel
            # and set in the passerelle connector settings.
            "X-API-Key": self.api_key,
        }
        response = self.requests.get(url, headers=headers)

        # TODO : create an utilitary method to handle status_code >= 400
        if response.status_code >= 400:
            data = {
                "error": "Bad Gateway or Proxy error",
                "message": f"Erreur Atal {response.status_code} {response.reason}",
                "url": f"{self.base_url}",
            }
            return JsonResponse(data, status=502)

        return {"data": response.json()}  # must return dict

    @endpoint(
        name="work-request-details",
        perm="can_access",
        description="Return work request details from ATAL.",
        methods=["get"],
        pattern=r"^(?P<uuid>[\w-]+)/$",
        example_pattern="{uuid}/",
        parameters={
            "uuid": {
                "description": "Numéro d'identification uuid de la demande dans ATAL.",
                "type": "string",
                "example_value": "11865d87-336b-49b3-e181-08d76f93d6b4",
            },
        },
    )
    def read_work_request_details(self, request, uuid):
        url = f"{self.base_url}/api/WorksRequests/{uuid}"
        headers = {
            "accept": "application/json",
            # X-API-KEY is visible in ATAL admin panel
            # and set in the passerelle connector settings.
            "X-API-Key": self.api_key,
        }
        response = self.requests.get(
            url,
            headers=headers,
        )

        return {"data": response.json()}  # must return dict
