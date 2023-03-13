import base64
import datetime
import json
import time
from io import BytesIO

import requests
from django.db import models
from django.http import JsonResponse

# from django.utils.six.moves.urllib_parse import urljoin
from passerelle.base.models import BaseResource
from passerelle.utils.api import endpoint
from passerelle.utils.jsonresponse import APIError


# TODO : we should rename this class name with something like AtalConnector
def string_to_datetime(date_string):
    """
    convertit les dates string de Atal en datetime
    :param date_string: string d'une date au format 2000-12-31T23:59...
    :return: datetime(year, month, day, hour, minute)
    """
    # string de formatage pour strptime
    format_datetime = "%Y-%m-%dT%H:%M"

    return datetime.datetime.strptime(date_string[:16], format_datetime)


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

    def check_status(self):
        response = requests.get(
            url=f"{self.base_url}/api/Test",
            headers={"Accept": "text/plain", "X-API-Key": self.api_key},
            verify=False,
        )
        response.raise_for_status()

    @endpoint(
        perm="can_access",
        description="Test methods",
        long_description="Requête sur le endpoint Test de Atal",
        display_order=0,
        display_category="Test",
    )
    def test(self, request):
        atal_response = requests.get(
            url=f"{self.base_url}/api/Test",
            headers={"Accept": "text/plain", "X-API-Key": self.api_key},
            verify=False,
        )
        atal_response_format = "{} - {}".format(atal_response.status_code, atal_response.text)
        return atal_response_format

    @endpoint(
        name="third-parties",
        perm="can_access",
        description="Récupère les third parties, utile pour sélectionner parmi eux le bon service demandeur",
    )
    def third_parties(self, request):
        response = requests.get(
            url=f"{self.base_url}/api/ThirdParties?type=2",
            headers={"Accept": "application/json", "X-API-Key": self.api_key},
            verify=False,
        )
        r_json = response.json()
        r_json = sorted(r_json, key = lambda i: i['Name'])
        return {"data": r_json}

    @endpoint(
        perm="can_access",
        description="Créer une demande de travaux dans Atal",
        methods=["post"],
    )
    def create_work_request(self, request):
        post_data = json.loads(request.body)
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
            # Endpoints are described in ATAl Swagger
            f"{self.base_url}/api/WorksRequests",
            json=data_to_atal,
            headers={
                "accept": "application/json",
                # X-API-KEY is visible in ATAL admin panel
                # and set in the passerelle connector settings.
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            },
            verify=False,
        )

        return {"data": response.json()}

    @endpoint(
        perm="can_access",
        description="Post files and join them to and ATAL work request.",
        methods=["post"],
        parameters={},
    )
    def post_attachment(self, request):
        post_data = json.loads(request.body)
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
            f"{self.base_url}/api/WorksRequests/{work_request_uuid}/Attachments",
            headers=headers,
            files=files,
            verify=False,
        )

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
        post_data = json.loads(request.body)  # http data from wcs webservice

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

        params = {
            '$expand': 'Responses',
        }

        log_requests_errors = False
        response = self.requests.get(
            url,
            params=params,
            headers=headers,
            verify=False,
        )

        response_json = response.json()
        log_requests_errors = True

        # Make it work anyway when Atal isn't up to date (if Responses expand does not work)
        if response_json.get('detail') and 'Responses' in response_json.get('detail'):
            response = self.requests.get(
                url,
                headers=headers,
                verify=False
            )
            response_json = response.json()

        return {"data": response_json}  # must return dict

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
            verify=False,
        )

        return {"data": response.json()}  # must return dict

    @endpoint(
        name="get-room-loans",
        perm="can_access",
        description="Cherche les locations de salles dans ATAL.",
        methods=["get"],
    )
    def read_reservations_room(self, request):
        url = f"{self.base_url}/api/RoomLoans"
        headers = {
            "accept": "application/json",
            # X-API-KEY is visible in ATAL admin panel
            # and set in the passerelle connector settings.
            "X-API-Key": self.api_key,
        }

        try:
            response = self.requests.get(
                url,
                headers=headers,
            ).json()
        except Exception as e:
            raise APIError(
                str(e),
                http_status=405,
            )

        return response  # must return dict

    @endpoint(
        name="get-reservation-room-detail",
        perm="can_access",
        description="Cherche les détails des réservations de salles dans ATAL.",
        methods=["get"],
    )
    def read_reservations_room_details(self, request):
        url = f"{self.base_url}/api/RoomLoans/Lines"
        headers = {
            "accept": "application/json",
            # X-API-KEY is visible in ATAL admin panel
            # and set in the passerelle connector settings.
            "X-API-Key": self.api_key,
        }

        try:
            response = self.requests.get(
                url,
                headers=headers,
            ).json()
        except Exception as e:
            raise APIError(
                str(e),
                http_status=405,
            )

        return response  # must return dict

    @endpoint(
        name="get-reservation-room",
        perm="can_access",
        description="Lis une réservation de salle dans ATAL.",
        methods=["get"],
        parameters={
            "id": {
                "description": "id de la réservation",
                "type": "int",
                "example_value": "2",
            },
        },
    )
    def read_reservation_room(self, request, id):
        url = f"{self.base_url}/api/RoomLoans/{id}"
        headers = {
            "accept": "application/json",
            # X-API-KEY is visible in ATAL admin panel
            # and set in the passerelle connector settings.
            "X-API-Key": self.api_key,
        }

        try:
            response = self.requests.get(
                url,
                headers=headers,
            ).json()
        except Exception as e:
            raise APIError(
                str(e),
                http_status=405,
            )

        return response  # must return dict

    @endpoint(
        name="get-materiel-loans",
        perm="can_access",
        description="Cherche les locations de materiel dans ATAL.",
        methods=["get"],
    )
    def read_reservations_materiel(self, request):
        url = f"{self.base_url}/api/MaterialLoans"
        headers = {
            "accept": "application/json",
            # X-API-KEY is visible in ATAL admin panel
            # and set in the passerelle connector settings.
            "X-API-Key": self.api_key,
        }

        try:
            response = self.requests.get(
                url,
                headers=headers,
            ).json()
        except Exception as e:
            raise APIError(
                str(e),
                http_status=405,
            )

        return response  # must return dict

    @endpoint(
        name="get-materiel-loans-details",
        perm="can_access",
        description="Cherche les détails des locations de materiel dans ATAL.",
        methods=["get"],
    )
    def read_materiel_loans_details(self, request):
        url = f"{self.base_url}/api/MaterialLoans/Lines"
        headers = {
            "accept": "application/json",
            # X-API-KEY is visible in ATAL admin panel
            # and set in the passerelle connector settings.
            "X-API-Key": self.api_key,
        }

        try:
            response = self.requests.get(
                url,
                headers=headers,
            ).json()
        except Exception as e:
            raise APIError(
                str(e),
                http_status=405,
            )

        return response  # must return dict

    @endpoint(
        name="get-materiel-list",
        perm="can_access",
        description="Cherche le materiel louable dans ATAL.",
        methods=["get"],
    )
    def read_materiel_list(self, request):
        url = f"{self.base_url}/api/Patrimonies"
        headers = {
            "accept": "application/json",
            # X-API-KEY is visible in ATAL admin panel
            # and set in the passerelle connector settings.
            "X-API-Key": self.api_key,
        }

        # pour avoir le patrimoine louable
        params = {
            "$filter": "CanBeLoaned",
        }

        try:
            response = self.requests.get(
                url,
                headers=headers,
                params=params,
            ).json()
        except Exception as e:
            raise APIError(
                str(e),
                http_status=405,
            )

        # retourne tout le patrimoine louable sauf les salles
        return {"data": [x for x in response if "Type" in x and x["Type"] != 1]}  # must return dict

    @endpoint(
        name="get-reservation-materiel",
        perm="can_access",
        description="Lis une réservation de materiel dans ATAL.",
        methods=["get"],
        parameters={
            "id": {
                "description": "id de la réservation",
                "type": "int",
                "example_value": "2",
            },
        },
    )
    def read_reservation_materiel(self, request, id):
        url = f"{self.base_url}/api/MaterialLoans/{id}"
        headers = {
            "accept": "application/json",
            # X-API-KEY is visible in ATAL admin panel
            # and set in the passerelle connector settings.
            "X-API-Key": self.api_key,
        }

        try:
            response = self.requests.get(
                url,
                headers=headers,
            ).json()
        except Exception as e:
            raise APIError(
                str(e),
                http_status=405,
            )

        return response  # must return dict

    @endpoint(
        name="get-patrimoines-louable",
        perm="can_access",
        description="Cherche le patrimoine louable dans ATAL.",
        methods=["get"],
    )
    def read_patrimoines_louable(self, request):
        url = f"{self.base_url}/api/Patrimonies"
        headers = {
            "accept": "application/json",
            # X-API-KEY is visible in ATAL admin panel
            # and set in the passerelle connector settings.
            "X-API-Key": self.api_key,
        }

        params = {
            "$filter": "CanBeLoaned",
        }

        try:
            response = self.requests.get(
                url,
                headers=headers,
                params=params,
            ).json()
        except Exception as e:
            raise APIError(
                str(e),
                http_status=405,
            )

        return response  # must return dict

    @endpoint(
        name="get-rooms-name",
        perm="can_access",
        description="Cherche les noms des salles louables dans ATAL.",
        methods=["get"],
    )
    def read_rooms_name(self, request):
        # liste de tous le patrimoine louable
        patrimoines = self.read_patrimoines_louable(request)

        # tri en fonction du type 1 (salle)
        return {"data": [x for x in patrimoines if "Type" in x and x["Type"] == 1]}  # must return dict

    @endpoint(
        name="get-rooms-dispo",
        perm="can_access",
        description="Cherche les salles disponible pour une date donnée dans ATAL.",
        methods=["get"],
        parameters={
            "date_debut": {
                "description": "date de debut de la location",
                "type": "datetime.date",
                "example_value": "2008-11-25",
            },
            "date_fin": {
                "description": "date de fin de la location",
                "type": "datetime.date",
                "example_value": "2008-11-25",
            },
            "heure_debut": {
                "description": "date de fin de la location",
                "type": "datetime.time",
                "example_value": "11:15",
            },
            "heure_fin": {
                "description": "date de fin de la location",
                "type": "datetime.time",
                "example_value": "20:20",
            },
        },
    )
    def read_rooms_dispo(self, request, date_debut, date_fin, heure_debut, heure_fin):
        # format date
        date_debut = datetime.date(
            int(date_debut.split("-")[0]), int(date_debut.split("-")[1]), int(date_debut.split("-")[2])
        )
        date_fin = datetime.date(int(date_fin.split("-")[0]), int(date_fin.split("-")[1]), int(date_fin.split("-")[2]))
        # format heure
        heure_debut = time.strptime(heure_debut, "%H:%M")
        heure_debut = datetime.time(heure_debut.tm_hour, heure_debut.tm_min)
        heure_fin = time.strptime(heure_fin, "%H:%M")
        heure_fin = datetime.time(heure_fin.tm_hour, heure_fin.tm_min)

        # datetime debut demande location
        datetime_debut = datetime.datetime.combine(date_debut, heure_debut)
        # datetime fin demande location
        datetime_fin = datetime.datetime.combine(date_fin, heure_fin)

        # liste des locations
        liste_location = self.read_reservations_room_details(request)

        # init liste rooms non dispo
        room_non_dispo = []

        # parcours des locations
        for location in liste_location:
            # transformation des dates de location en datetime
            debut_location = string_to_datetime(location["StartDate"])
            fin_location = string_to_datetime(location["EndDate"])

            # tri des salles en fonction des dates de locations
            if debut_location < datetime_debut < fin_location or debut_location < datetime_fin < fin_location:
                room_non_dispo.append(location["RoomId"])

        # liste des salles
        rooms = self.read_rooms_name(request)["data"]

        # tri des salles pour avoir les dispo
        return {"data": [x for x in rooms if x["Id"] not in room_non_dispo]}  # must return dict

    @endpoint(
        name="get-dates-dispo",
        perm="can_access",
        description="Cherche les dates disponible pour une salle dans ATAL.",
        methods=["get"],
        parameters={
            "room": {
                "description": "salle",
                "type": "int",
                "example_value": 2732,
            },
            "delai": {
                "description": "délai minimum à l'introduction de la demande",
                "type": "int",
                "example_value": 90,
            },
        },
    )
    def read_dates_dispo(self, request, room, delai=0):
        # liste des locations
        locations = self.read_reservations_room_details(request)

        # définition de la date d'aujourd'hui en datetime
        now = datetime.datetime.now()
        today = datetime.datetime(now.year, now.month, now.day)

        # convert string to dict
        # room = ast.literal_eval(room)

        # tri des locations par rapport à une salle
        locations = [
            x
            for x in locations
            if "RoomId" in x
               and x["RoomId"] == int(room)
               and (today + datetime.timedelta(days=delai)) < string_to_datetime(x["StartDate"])
        ]

        return {"data": locations}

    @endpoint(
        name="post-reservation-room",
        perm="can_access",
        description="Inscrit une réservation de salle dans Atal.",
        methods=["get"],
        parameters={
            "date_debut": {
                "description": "date de debut de la location",
                "type": "datetime.date",
                "example_value": "2022-12-01",
            },
            "date_fin": {
                "description": "date de fin de la location",
                "type": "datetime.date",
                "example_value": "2022-12-02",
            },
            "heure_debut": {
                "description": "date de fin de la location",
                "type": "datetime.time",
                "example_value": "11:15",
            },
            "heure_fin": {
                "description": "date de fin de la location",
                "type": "datetime.time",
                "example_value": "20:20",
            },
            "room": {
                "description": "salle",
                "type": "int",
                "example_value": 2732,
            },
            "nombre_personne_prevue": {
                "description": "Nombre de personne prévue",
                "type": "int",
                "example_value": 0,
            },
            "nombre_personne_reel": {
                "description": "Nombre de personne réel",
                "type": "int",
                "example_value": 0,
            },
            "id_tier": {
                "description": "Aucune idée",
                "type": "int",
                "example_value": 63,
            },
        },
    )
    def write_reservation_room(
            self,
            request,
            date_debut,
            date_fin,
            heure_debut,
            heure_fin,
            room,
            nombre_personne_prevue=0,
            nombre_personne_reel=0,
            id_tier=63,
    ):
        url = f"{self.base_url}/api/RoomLoans"
        headers = {
            "accept": "application/json",
            # X-API-KEY is visible in ATAL admin panel
            # and set in the passerelle connector settings.
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

        datetime_debut = f"{date_debut}T{heure_debut}"
        datetime_fin = f"{date_fin}T{heure_fin}"
        # room = ast.literal_eval(room)

        payload = json.dumps(
            {
                "EndDate": datetime_fin,
                "PlannedPeopleNumber": nombre_personne_prevue,
                "RealPeopleNumber": nombre_personne_reel,
                "RequesterThirdPartyId": id_tier,
                "Rooms": [
                    {
                        "EndDate": datetime_fin,
                        "Pricing": {
                            "AdditionalQuantity": 0,
                            "AppliedPricingId": 0,
                            "BaseQuantity": 0,
                            "SquareMetersNumber": 0,
                        },
                        "RoomId": room,
                        "StartDate": datetime_debut,
                    }
                ],
                "StartDate": datetime_debut,
            }
        )

        response = self.requests.post(url, headers=headers, data=payload)

        return response.json()

    @endpoint(
        name="get-loanable-items",
        perm="can_access",
        description="Item louable",
        methods=["get"],
    )
    def get_loanable_items(self, request):
        url = f"{self.base_url}/api/InventoriedItems"
        headers = {
            "accept": "application/json",
            # X-API-KEY is visible in ATAL admin panel
            # and set in the passerelle connector settings.
            "X-API-Key": self.api_key,
        }

        try:
            response = self.requests.get(
                url,
                headers=headers,
            ).json()
        except Exception as e:
            raise APIError(
                str(e),
                http_status=405,
            )

        response = [
            x
            for x in response
            if x["Item"]["ItemTemplate"]["CanBeLoaned"]
        ]

        # Suppression des doublons
        loanable_items = []
        for i in response:
            if i["ItemId"] not in [x["ItemId"] for x in loanable_items]:
                loanable_items.append(i)

        return {"datas": loanable_items}

    @endpoint(
        name="post-reservation-materiel",
        perm="can_access",
        description="Inscrit une réservation de matériel dans Atal.",
        methods=["get"],
        parameters={
            "date_debut": {
                "description": "date de debut de la location",
                "type": "datetime.date",
                "example_value": "2022-12-01",
            },
            "date_fin": {
                "description": "date de fin de la location",
                "type": "datetime.date",
                "example_value": "2022-12-02",
            },
            "heure_debut": {
                "description": "date de fin de la location",
                "type": "datetime.time",
                "example_value": "11:15",
            },
            "heure_fin": {
                "description": "date de fin de la location",
                "type": "datetime.time",
                "example_value": "20:20",
            },
            "material": {
                "description": "matériel",
                "type": "int",
                "example_value": 3258,
            },
            "quantity": {
                "description": "Quantité demandée",
                "type": "int",
                "example_value": 0,
            },
            "id_tier": {
                "description": "Aucune idée",
                "type": "int",
                "example_value": 63,
            },
        },
    )
    def post_material_location(
            self,
            request,
            date_debut,
            date_fin,
            heure_debut,
            heure_fin,
            material,
            quantity,
            id_tier):

        url = f"{self.base_url}/api/MaterialLoans"
        headers = {
            "accept": "application/json",
            # X-API-KEY is visible in ATAL admin panel
            # and set in the passerelle connector settings.
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

        datetime_debut = f"{date_debut}T{heure_debut}Z"
        datetime_fin = f"{date_fin}T{heure_fin}Z"

        payload = json.dumps(
            {
                "EndDate": datetime_fin,
                "RequesterThirdPartyId": id_tier,
                "Material": [
                    {
                        "EndDate": datetime_fin,
                        "ItemId": material,
                        "StartDate": datetime_debut,
                        "RequestedQuantity": quantity,
                    }
                ],
                "StartDate": datetime_debut,
            }
        )

        response = self.requests.post(url, headers=headers, data=payload)

        return response.json()
