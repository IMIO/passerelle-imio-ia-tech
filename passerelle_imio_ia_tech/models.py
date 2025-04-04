import base64
import datetime
from datetime import tzinfo
from zoneinfo import ZoneInfo
import json
import time
import unicodedata
from io import BytesIO

import requests
from django.db import models
from django.conf import settings
from django.http import JsonResponse

# from django.utils.six.moves.urllib_parse import urljoin
from passerelle.base.models import BaseResource
from passerelle.base.signature import sign_url
from passerelle.utils.api import endpoint
from passerelle.utils.jsonresponse import APIError
from requests import RequestException


# TODO : we should rename this class name with something like AtalConnector
def string_to_datetime(date_string):
    """
    convertit les dates string de ATAL en datetime
    :param date_string: string d'une date au format 2000-12-31T23:59...
    :return: datetime(year, month, day, hour, minute)
    """
    # string de formatage pour strptime
    format_datetime = "%Y-%m-%dT%H:%M"

    return datetime.datetime.strptime(date_string[:16], format_datetime)


class imio_atal(BaseResource):
    """Connecteur permettant d'intéragir avec une instance d'ATAL V6"""

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
    api_description = "Connecteur permettant d'intéragir avec une instance d'ATAL V6"
    category = "Connecteurs iMio"

    class Meta:
        verbose_name = "Connecteur ATAL (iMio)"

    @endpoint(
        perm="can_access",
        description="Méthode de test",
        long_description="Requête sur le endpoint Test de ATAL.",
        display_order=0,
        display_category="Test",
    )
    def test(self, request=None):
        atal_response = requests.get(
            url=f"{self.base_url}/api/Test",
            headers={"Accept": "text/plain", "X-API-Key": self.api_key},
            verify=False,
        )
        atal_response_format = "{} - {}".format(
            atal_response.status_code, atal_response.text
        )
        return atal_response_format

    @endpoint(
        name="third-parties",
        perm="can_access",
        description="Récupère les third parties",
        long_description="Récupère les third parties, utile pour sélectionner parmi eux le bon service demandeur",
        display_category="Utilitaires",
    )
    def third_parties(self, request):
        response = requests.get(
            url=f"{self.base_url}/api/ThirdParties?type=2",
            headers={"Accept": "application/json", "X-API-Key": self.api_key},
            verify=False,
        )
        r_json = response.json()
        r_json = sorted(r_json, key=lambda i: i["Name"])
        return {"data": r_json}

    @endpoint(
        perm="can_access",
        description="Créer une demande de travaux dans ATAL",
        methods=["post"],
        long_description="Crée une demande de travaux dans ATAL.",
        display_category="Demandes de travaux",
    )
    def create_work_request(self, request):
        post_data = json.loads(request.body)
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
            "Object": post_data["atal_object"],
            "Description": post_data["atal_description"],
            "RecipientId": post_data["atal_recipient_id"],
            "RequestingDepartmentId": post_data["atal_requesting_department_id"],
            "RequestType": post_data["atal_request_type"],
            "Localization": post_data["atal_localization"],
            "Longitude": post_data["atal_longitude"],
            "Latitude": post_data["atal_latitude"],
        }
        # TODO : Use schemas as Entr'Ouvert does

        response = self.requests.post(
            f"{self.base_url}/api/WorksRequests",
            json=data_to_atal,
            headers={
                "accept": "application/json",
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            },
            verify=False,
        )

        return {"data": response.json()}

    @endpoint(
        perm="can_access",
        description="Attache des photos aux demandes de travaux dans ATAL.",
        methods=["post"],
        parameters={},
        long_description=("Envoie des photos aux demandes de travaux dans ATAL. "),
        display_category="Demandes de travaux",
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
        headers = {
            "X-API-Key": self.api_key,
        }
        # multipart/formdata http request specific syntax
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

    # TODO: Delete this one and use read_work_request_details instead
    @endpoint(
        perm="can_access",
        description="Récupère le détail d'une demande de travaux dans ATAL.",
        methods=["post"],
        parameters={
            "atal_work_request_uuid": {
                "description": "Numéro d'identification uuid de la demande dans ATAL.",
                "type": "string",
                "example_value": "11865d87-336b-49b3-e181-08d76f93d6b4",
            },
        },
        long_description=(
                "Actuellement employé dans Townstreet. Ce endpoint est plus "
                "complet, mais devrait être refactoré, néttoyé (code obsolète) et "
                "converti en GET"
        ),
        display_category="Demandes de travaux",
    )
    def get_work_request_details(self, request, *args, **kwargs):
        post_data = json.loads(request.body)  # http data from wcs webservice
        uuid = post_data["atal_work_request_uuid"]
        url = f"{self.base_url}/api/WorksRequests/{uuid}"
        headers = {
            "accept": "application/json",
            "X-API-Key": self.api_key,
        }

        params = {
            "$expand": "Responses",
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

        # Make it work anyway when ATAL isn't up to date (if Responses expand does not work)
        if response_json.get("detail") and "Responses" in response_json.get("detail"):
            response = self.requests.get(url, headers=headers, verify=False)
            response_json = response.json()

        return {"data": response_json}  # must return dict

    # TODO: Use this one instead of get_work_request_details (refactor needed)
    @endpoint(
        name="work-request-details",
        perm="can_access",
        description="Renvoie le détail d'une demande de travaux dans ATAL.",
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
        long_description=(
                "Pas employé dans Townstreet. Devrait être employé en mergeant "
                "avec get_work_request_details. L'améliorer pour gérer "
                "efficacement les exceptions (voir le code du endpoint) "
                "'get-natures'). Adapter le workflow de Townstreet."
        ),
        display_category="Demandes de travaux",
    )
    def read_work_request_details(self, request, uuid):
        url = f"{self.base_url}/api/WorksRequests/{uuid}"
        headers = {
            "accept": "application/json",
            "X-API-Key": self.api_key,
        }
        response = self.requests.get(
            url,
            headers=headers,
            verify=False,
        )

        return {"data": response.json()}  # must return dict

    #########################
    ### Location de Salles###
    #########################

    @endpoint(
        name="get-patrimoines-louable",
        perm="can_access",
        description="Cherche le patrimoine louable dans ATAL.",
        long_description="Cherche le patrimoine louable dans ATAL, utile pour chercher les salles louables.",
        display_category="Location de Salles",
        display_order=1,
        methods=["get"],
    )
    def read_patrimoines_louable(self, request, filters=None):
        url = f"{self.base_url}/api/Patrimonies"
        headers = {
            "accept": "application/json",
            "X-API-Key": self.api_key,
        }

        params = {"$filter": f"CanBeLoaned {filters}" if filters else "CanBeLoaned"}

        response = self.requests.get(
            url,
            headers=headers,
            params=params,
            verify=False,
        )
        response.raise_for_status()

        return response.json()  # must return dict

    @endpoint(
        name="get-rooms-name",
        perm="can_access",
        description="Get noms des salles louables dans ATAL.",
        long_description="Cherche les noms des salles louables dans ATAL.",
        display_category="Location de Salles",
        display_order=2,
        methods=["get"],
    )
    def read_rooms_name(self, request):
        # liste de tous le patrimoine louable
        patrimoines = self.read_patrimoines_louable(request)

        # tri en fonction du type 1 (salle)
        return {
            "data": [x for x in patrimoines if "Type" in x and x["Type"] == 1]
        }  # must return dict

    @endpoint(
        name="get-parents-rooms",
        perm="can_access",
        description="Get noms des salles parents dans ATAL.",
        long_description="Cherche les noms des salles parents dans ATAL.",
        display_category="Location de Salles",
        display_order=3,
        methods=["get"],
    )
    def read_parents_rooms(self, request):
        # liste des salles louables
        rooms_name = self.read_rooms_name(request)["data"]

        ids = {room["Id"] for room in rooms_name}  # Ensemble de tous les Ids
        parent_rooms = [room for room in rooms_name if "ParentId" not in room or room["ParentId"] not in ids]

        return {"data": parent_rooms}

    @endpoint(
        name="get-kids-rooms",
        perm="can_access",
        description="Get noms des salles enfants dans ATAL.",
        long_description="Cherche les noms des salles enfants dans ATAL par rapport à un parent donné.",
        display_category="Location de Salles",
        display_order=4,
        methods=["get"],
        parameters={
            "parent_id": {
                "description": "id du parent",
                "type": "int",
                "example_value": "552",
            },
        },
    )
    def read_kids_rooms(self, request, parent_id):
        # liste des salles louables
        rooms_name = self.read_rooms_name(request)["data"]
        kids_rooms = [room for room in rooms_name if room.get("ParentId") == parent_id]

        return {"data": kids_rooms}

    @endpoint(
        name="get-room",
        perm="can_access",
        description="Get infos salle dans ATAL.",
        long_description="Cherche les informations d'une salle dans ATAL.",
        display_category="Location de Salles",
        display_order=5,
        methods=["get"],
        parameters={
            "room_id": {
                "description": "id de la salle",
                "type": "int",
                "example_value": "3908",
            },
            "expands": {
                "description": "Liste des éléments à étendre",
                "type": "string",
                "example_value": "Addresses,Classifications,ControlAffectations,FeaturesValues($expand=FeatureLists,FeatureList),ThirdPartyAffectations",
            },
        },
    )
    def read_room(self, request, room_id, expands=None):
        url = f"{self.base_url}/api/Patrimonies/{room_id}"
        headers = {
            "accept": "application/json",
            "X-API-Key": self.api_key,
        }

        params = {
            "$expand": expands,
        } if expands else None

        response = self.requests.get(
            url,
            headers=headers,
            params=params,
            verify=False,
        )
        response.raise_for_status()

        return response.json()  # must return dict

    @endpoint(
        name="get-room-loans",
        perm="can_access",
        description="get Les locations de salles.",
        methods=["get"],
        long_description="Cherche les locations de salles dans ATAL.",
        display_category="Location de Salles",
        display_order=6,
    )
    def read_reservations_room(self, request):
        url = f"{self.base_url}/api/RoomLoans"
        headers = {
            "accept": "application/json",
            "X-API-Key": self.api_key,
        }

        response = self.requests.get(
            url,
            headers=headers,
            verify=False,
        )

        response.raise_for_status()

        return response.json()  # must return dict

    @endpoint(
        name="get-reservation-room",
        perm="can_access",
        description="Lis une réservation de salle",
        methods=["get"],
        long_description="Lis une réservation de salle dans ATAL.",
        display_category="Location de Salles",
        display_order=7,
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
            "X-API-Key": self.api_key,
        }
        response = self.requests.get(
            url,
            headers=headers,
            verify=False,
        )

        response.raise_for_status()

        return {"data": response.json()}  # must return dict

    @endpoint(
        name="get-reservation-room-detail",
        perm="can_access",
        description="get Les détails de locations de salles.",
        methods=["get"],
        long_description="Cherche les détails des réservations de salles dans ATAL.",
        display_category="Location de Salles",
        display_order=8,
    )
    def read_reservations_room_details(self, request, filters=None):
        url = f"{self.base_url}/api/RoomLoans/Lines"
        headers = {
            "accept": "application/json",
            "X-API-Key": self.api_key,
        }
        params = {"$filter": filters} if filters else None
        response = self.requests.get(
            url,
            headers=headers,
            params=params,
            verify=False,
        )
        response.raise_for_status()

        return response.json()  # must return dict

    @endpoint(
        name="get-rooms-dispo",
        perm="can_access",
        description="Cherche les salles disponible pour une date donnée.",
        long_description="Cherche les salles disponible pour une date donnée dans ATAL.",
        display_category="Location de Salles",
        display_order=9,
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
        # String datetime
        datetime_debut = f"{date_debut} {heure_debut}"
        datetime_fin = f"{date_fin} {heure_fin}"
        # format date
        format_date = "%Y-%m-%d %H:%M"
        datetime_debut = datetime.datetime.strptime(datetime_debut, format_date)
        datetime_fin = datetime.datetime.strptime(datetime_fin, format_date)
        # TimeZone
        timezone = ZoneInfo("Europe/Brussels")
        datetime_debut = datetime_debut.replace(tzinfo=timezone)
        datetime_fin = datetime_fin.replace(tzinfo=timezone)
        # ISO format
        datetime_debut = datetime_debut.isoformat()
        datetime_fin = datetime_fin.isoformat()

        # query pour les locations
        query = f"(StartDate lt {datetime_fin}) and (EndDate gt {datetime_debut})"

        # liste des locations
        liste_location = self.read_reservations_room_details(request, filters=query)

        # init liste rooms non dispo
        room_non_dispo = [location.get("RoomId") for location in liste_location]
        # suppression des doublons
        room_non_dispo = list(set(room_non_dispo))
        # Check parents/kids
        room_parents_kids_non_dispo = []
        for room in room_non_dispo:
            room = int(room)
            room_parents_kids_non_dispo.extend(self.get_rooms_for_indisponibilities(request, room))

        # suppression des doublons
        room_parents_kids_non_dispo = list(set(room_parents_kids_non_dispo))

        # liste des salles
        rooms = self.read_rooms_name(request)["data"]

        # tri des salles pour avoir les dispo
        return {
            "data": [x for x in rooms if int(x["Id"]) not in room_parents_kids_non_dispo]
        }  # must return dict

    @endpoint(
        name="get-dates-dispo",
        perm="can_access",
        description="Cherche les dates disponible pour une salle.",
        long_description="Cherche les dates disponible pour une salle dans ATAL.",
        display_category="Location de Salles",
        display_order=10,
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
    def read_dates_dispo(self, request, delai=0, filters=None):
        # définition de la date d'aujourd'hui en datetime
        today = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())

        start_date = today + datetime.timedelta(days=delai)

        query = filters if filters else None

        start_string = start_date.strftime("%Y-%m-%d")

        query = query + f" and StartDate ge {start_string}" if query else f"StartDate ge {start_string}"

        # liste des locations
        locations = self.read_reservations_room_details(request, filters=query)

        return {"data": locations}

    @endpoint(
        name="generate-day-availability",
        perm="can_access",
        description="Générer la source de données des jours de disponibilité",
        long_description="Générer la source de données des jours de disponibilité pour une salle donnée dans ATAL.",
        display_category="Location de Salles",
        display_order=11,
        methods=["get"],
        parameters={
            "room": {
                "description": "salle",
                "type": "int",
                "example_value": 2732,
            },
            "start": {
                "description": "délai minimum à l'introduction de la demande",
                "type": "int",
                "example_value": 90,
            },
            "end": {
                "description": "délai maximum à l'introduction de la demande",
                "type": "int",
                "example_value": 365,
            },
        },
    )
    def generate_day_availability(self, request, room, start=0, end=365):
        rooms = self.get_rooms_for_indisponibilities(request, room)

        indisponibilites = self.get_indisponibilities(request, rooms, start)

        start_date = datetime.date.today() + datetime.timedelta(days=start)
        end_date = datetime.date.today() + datetime.timedelta(days=end)
        delta = end_date - start_date
        days = [start_date + datetime.timedelta(days=x) for x in range(delta.days + 1)]
        free_days = []
        for day in days:
            text = day.strftime("%d/%m/%Y")
            id = day.strftime("%Y-%m-%d")
            start_date = day.strftime("%Y-%m-%d")
            end_date = day.strftime("%Y-%m-%d")
            start_time = "00:00"
            end_time = "23:59"
            disabled = True in [
                string_to_datetime(x["StartDate"]).date() <= day <= string_to_datetime(x["EndDate"]).date()
                for x in indisponibilites
            ]
            free_days.append(
                {"text": text, "id": id, "start_date": start_date, "end_date": end_date, "start_time": start_time,
                 "end_time": end_time, "disabled": disabled})
        return {"data": free_days}

    @endpoint(
        name="generate-hour-availability",
        perm="can_access",
        description="Générer la source de données des heures de disponibilité",
        long_description="Générer la source de données des heures de disponibilité pour une salle donnée dans ATAL.",
        display_category="Location de Salles",
        display_order=12,
        methods=["get"],
        parameters={
            "room": {
                "description": "salle",
                "type": "int",
                "example_value": 2732,
            },
            "start": {
                "description": "délai minimum à l'introduction de la demande",
                "type": "int",
                "example_value": 90,
            },
            "end": {
                "description": "délai maximum à l'introduction de la demande",
                "type": "int",
                "example_value": 365,
            },
        },
    )
    def generate_hour_availability(self, request, room, start=0, end=365):
        rooms = self.get_rooms_for_indisponibilities(request, room)

        indisponibilites = self.get_indisponibilities(request, rooms, start)

        start_datetime = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time()) + datetime.timedelta(days=start)
        end_datetime = datetime.datetime.combine(datetime.date.today(), datetime.time(23, 0)) + datetime.timedelta(days=end)
        delta = int((end_datetime - start_datetime).total_seconds() / 3600)
        hours = [start_datetime + datetime.timedelta(hours=x) for x in range(delta + 1)]
        free_hours = []
        for hour in hours:
            text = hour.strftime("%d/%m/%Y %H:%M")
            id = hour.strftime("%Y-%m-%dT%H:%M")
            start_date = hour.strftime("%Y-%m-%d")
            end_date = hour.strftime("%Y-%m-%d")
            start_time = hour.strftime("%H:%M")
            end_time = hour.strftime("%H:59")
            disabled = True in [
                string_to_datetime(x["StartDate"]).date() <= hour.date() <= string_to_datetime(x["EndDate"]).date() and
                string_to_datetime(x["StartDate"]).hour <= hour.hour <= string_to_datetime(x["EndDate"]).hour
                for x in indisponibilites
            ]
            free_hours.append(
                {"text": text, "id": id, "start_date": start_date, "end_date": end_date, "start_time": start_time,
                 "end_time": end_time, "disabled": disabled})
        return {"data": free_hours}

    @endpoint(
        name="bookings-room",
        perm="can_access",
        description="Réserver une salle",
        long_description="Réserver une salle dans ATAL avec plusieurs plages horaires.",
        display_category="Location de Salles",
        display_order=13,
        methods=["post"],
        parameters={
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
        }
    )
    def bookings_room(self, request, room, nombre_personne_prevue=0, nombre_personne_reel=0, id_tier=63):
        post_data = json.loads(request.body)
        booking_dates = post_data.get("booking_dates", [])
        delta = datetime.timedelta(minutes=1)
        merged_intervals = []
        current_interval = booking_dates[0]

        for i in range(1, len(booking_dates)):
            current_end = string_to_datetime(f'{current_interval["end_date"]}T{current_interval["end_time"]}')
            next_start = string_to_datetime(f'{booking_dates[i]["start_date"]}T{booking_dates[i]["start_time"]}')

            # Vérifier s'il n'y a qu'une minute d'écart
            if next_start == current_end + delta:
                current_interval["end_date"] = booking_dates[i]["end_date"]
                current_interval["end_time"] = booking_dates[i]["end_time"]
            else:
                merged_intervals.append(current_interval)
                current_interval = booking_dates[i]

        # Ajouter le dernier intervalle
        merged_intervals.append(current_interval)

        responses = {"data": []}

        for interval in merged_intervals:
            response = self.write_reservation_room(request, interval["start_date"], interval["end_date"], interval["start_time"],
                                        interval["end_time"], room, nombre_personne_prevue, nombre_personne_reel,
                                        id_tier)
            responses["data"].append(response)

        return responses

    @endpoint(
        name="post-reservation-room",
        perm="can_access",
        description="Inscrit une réservation de salle.",
        long_description="Inscrit une réservation de salle dans ATAL.",
        display_category="Location de Salles",
        display_order=14,
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

        response = self.requests.post(
            url,
            headers=headers,
            data=payload,
            verify=False,
        )

        response.raise_for_status()

        return response.json()

    @endpoint(
        name="patch-booking-room",
        perm="can_access",
        description="Modifie le statut d'une réservation de salle.",
        long_description="Modifie le statut d'une réservation de salle dans ATAL.",
        display_category="Location de Salles",
        display_order=15,
        methods=["get"],
        parameters={
            "room_loan_id": {
                "description": "id de la réservation de salle",
                "type": "int",
                "example_value": 2573,
            },
            "request_state": {
                "description": "statut de la réservation : 0 = Pending, 2 = Accepted, 3 = Refused, 4 = Cancelled",
                "type": "int",
                "example_value": 0,
            },
        },
    )
    def update_booking_room(
            self,
            request,
            room_loan_id,
            request_state,
    ):
        url = f"{self.base_url}/api/RoomLoans?id={room_loan_id}"
        headers = {
            "accept": "*/*",
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = json.dumps({"RequestState": int(request_state)})

        try:
            response = requests.patch(
                url,
                headers=headers,
                data=payload,
                verify=False,
            )
        except RequestException as e:
            self.logger.warning(f'ATAL Error: {e}')
            raise APIError(f'ATAL Error: {e}')

        if response.headers.get('Content-Type') == 'application/json':
            json_response = None
            try:
                json_response = response.json()
            except ValueError:
                self.logger.warning('ATAL Error: bad JSON response')
                raise APIError('ATAL Error: bad JSON response')

            return json_response

        try:
            response.raise_for_status()
        except RequestException as e:
            self.logger.warning(f'ATAL Error: {e}')
            raise APIError(f'ATAL Error: {e}')
        self.logger.info(f'ATAL PATCH Booking Room {room_loan_id} successful')
        return

    #############################
    ### Location de matériels ###
    #############################

    @endpoint(
        name="get-loanable-items",
        perm="can_access",
        description="Cherches les Items louables.",
        long_description="Cherches les Items louables dans ATAL, utile pour savoir quel matériel est louable",
        display_category="Location de Matériels",
        display_order=1,
        methods=["get"],
    )
    def get_loanable_items(self, request):
        url = f"{self.base_url}/api/InventoriedItems"
        headers = {
            "accept": "application/json",
            "X-API-Key": self.api_key,
        }
        response = self.requests.get(
            url,
            headers=headers,
            verify=False,
        )

        response.raise_for_status()

        response = [x for x in response if x["Item"]["ItemTemplate"]["CanBeLoaned"]]

        # Suppression des doublons
        loanable_items = []
        for i in response:
            if i["ItemId"] not in [x["ItemId"] for x in loanable_items]:
                loanable_items.append(i)

        return {"datas": loanable_items}

    @endpoint(
        name="get-materiel-list",
        perm="can_access",
        description="Cherche le materiel louable dans ATAL.",
        long_description="Cherche le materiel louable dans ATAL.",
        display_category="Location de Matériels",
        display_order=2,
        methods=["get"],
    )
    def read_materiel_list(self, request):
        url = f"{self.base_url}/api/Patrimonies"
        headers = {
            "accept": "application/json",
            "X-API-Key": self.api_key,
        }

        # pour avoir le patrimoine louable
        params = {
            "$filter": "CanBeLoaned",
        }
        response = self.requests.get(
            url,
            headers=headers,
            params=params,
            verify=False,
        )

        response.raise_for_status()

        # retourne tout le patrimoine louable sauf les salles
        return {
            "data": [x for x in response.json() if "Type" in x and x["Type"] != 1]
        }  # must return dict

    @endpoint(
        name="get-materiel-loans",
        perm="can_access",
        description="Get les locations de materiel",
        long_description="Lis les locations de matériel dans ATAL.",
        display_category="Location de Matériels",
        display_order=3,
        methods=["get"],
    )
    def read_reservations_materiel(self, request):
        url = f"{self.base_url}/api/MaterialLoans"
        headers = {
            "accept": "application/json",
            "X-API-Key": self.api_key,
        }
        response = self.requests.get(
            url,
            headers=headers,
            verify=False,
        )

        response.raise_for_status()

        return response.json()  # must return dict

    @endpoint(
        name="get-reservation-materiel",
        perm="can_access",
        description="Get réservation de materiel dans ATAL.",
        long_description="Lis une réservation de matériel dans ATAL",
        display_category="Location de Matériels",
        display_order=4,
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
            "X-API-Key": self.api_key,
        }
        response = self.requests.get(
            url,
            headers=headers,
            verify=False,
        )

        response.raise_for_status()

        return response.json()  # must return dict

    @endpoint(
        name="get-materiel-loans-details",
        perm="can_access",
        description="Get détails des locations de materiel.",
        long_description="Cherche les détails des locations de materiel dans ATAL.",
        display_category="Location de Matériels",
        display_order=5,
        methods=["get"],
    )
    def read_materiel_loans_details(self, request):
        url = f"{self.base_url}/api/MaterialLoans/Lines"
        headers = {
            "accept": "application/json",
            "X-API-Key": self.api_key,
        }
        response = self.requests.get(
            url,
            headers=headers,
            verify=False,
        )

        response.raise_for_status()

        return response.json()  # must return dict

    @endpoint(
        name="post-reservation-materiel",
        perm="can_access",
        description="Inscrit une réservation de matériel.",
        long_description="Inscrit une réservation de matériel dans ATAL.",
        display_category="Location de Matériels",
        display_order=6,
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
            id_tier,
    ):
        url = f"{self.base_url}/api/MaterialLoans"
        headers = {
            "accept": "application/json",
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

        response = self.requests.post(
            url,
            headers=headers,
            data=payload,
            verify=False,
        )

        response.raise_for_status()

        return response.json()

    @endpoint(
        name="get-natures",
        perm="can_access",
        description="Cherche les thématiques dans ATAL.",
        methods=["get"],
        parameters={
            "primary_only": {
                "description": "Si True, retourne les natures primaires",
                "type": "boolean",
                "example_value": True,
            },
            "secondary_only": {
                "description": "Si True, retourne les natures secondaires",
                "type": "boolean",
                "example_value": True,
            },
            "parent_id": {
                "description": "Si renseigné, retourne les natures secondaires de la nature parent_id",
                "type": "int",
                "example_value": 1744,
            },
        },
        long_description="Récupère les thématiques (appellées aussi natures) dans ATAL.",
        display_category="Utilitaires",
    )
    def get_atal_thematics(
            self, request=None, primary_only=False, secondary_only=False, parent_id=None
    ):
        url = f"{self.base_url}/api/Thematics"
        headers = {
            "accept": "application/json",
            "X-API-Key": self.api_key,
        }

        try:
            response = self.requests.get(
                url,
                headers=headers,
            )
        except (requests.Timeout, requests.RequestException) as exc:
            raise APIError(str(exc))
        try:
            response.raise_for_status()
        except requests.RequestException as main_exc:
            try:
                err_data = response.json()
            except (json.JSONDecodeError, requests.exceptions.RequestException):
                err_data = {"response_text": response.text}
            raise APIError(str(main_exc), data=err_data)

        try:
            json_response = response.json()
        except (json.JSONDecodeError, requests.exceptions.RequestException) as exc:
            raise APIError(str(exc))

        parsed_thematics = [
            {
                "id": item["Id"],
                "label": item["Label"],
                "complete_label": item["CompleteLabel"],
                "parent_id": item.get("ParentThematicId", None),
            }
            for item in json_response
            if not item["Archived"]
        ]

        if primary_only:
            parsed_thematics = [
                item for item in parsed_thematics if item["parent_id"] is None
            ]

        if secondary_only:
            parsed_thematics = [
                item for item in parsed_thematics if item["parent_id"] is not None
            ]

        if parent_id:
            parsed_thematics = [
                item for item in parsed_thematics if item["parent_id"] == parent_id
            ]

        sorted_parsed_thematics = sorted(
            parsed_thematics,
            key=lambda x: unicodedata.normalize("NFC", x["complete_label"]),
        )

        return {"data": sorted_parsed_thematics}

############
# Fichiers #
############

    @endpoint(
        name="get-attachments",
        perm="can_access",
        description="Get fichier.",
        long_description="Télécharge un fichier dans ATAL.",
        display_category="Fichiers",
        display_order=1,
        methods=["get"],
        parameters={
            "attachments_id": {
                "description": "id du fichier",
                "type": "int",
                "example_value": "3000",
            },
        },
    )
    def get_attachments(self, request, attachments_id):

        url_attachments = f"{self.base_url}/api/Attachments/{attachments_id}"
        headers = {
            "accept": "application/json",
            "X-API-Key": self.api_key,
        }

        response_attachments = self.requests.get(
            url_attachments,
            headers=headers,
            verify=False,
        )
        response_attachments.raise_for_status()

        response_attachments_json = response_attachments.json()
        key = response_attachments_json.get("Key")
        if not key:
            raise APIError("Key not found in response")

        url_download = f"{self.base_url}/api/Attachments/Download/{key}"
        response_download = self.requests.get(
            url_download,
            headers=headers,
            verify=False,
        )
        response_download.raise_for_status()

        response = {
            "content": base64.b64encode(response_download.content).decode("utf-8"),
            "filename": response_attachments_json.get("FileName"),
            "content_is_base64": True,
            "id": response_attachments_json.get("Id"),
        }

        return response

    @endpoint(
        name="get-attachments-list",
        perm="can_access",
        description="Get fichiers.",
        long_description="Télécharge des fichiers dans ATAL.",
        display_category="Fichiers",
        display_order=2,
        methods=["get"],
        parameters={
            "room_id": {
                "description": "id de la salle",
                "type": "int",
                "example_value": "11644",
            },
            "exclude": {
                "description": "Liste des éléments à exclure",
                "type": "list",
                "example_value": "[18249, 18250]",
            },
        },
    )
    def get_attachments_list(self, request, room_id, exclude=None):

        if exclude is None:
            exclude = []
        else:
            exclude = json.loads(exclude)

        room_info = self.read_room(request, room_id, "FeaturesValues")

        features_value = room_info.get("FeaturesValues", [])

        response = []
        combos = self.get_service("combo")
        combo = [combo for combo in combos if not combo.get("is-portal-agent")][0]

        for feature in features_value:
            if feature.get("AttachmentId") and feature.get("AttachmentId") not in exclude:
                try:
                    attachment = self.get_attachments(request, feature.get("AttachmentId"))
                except Exception as e:
                    self.logger.warning(f"Error while getting attachment {feature.get('AttachmentId')}: {e}")
                    continue
                signed_url = sign_url(
                    url=f"{combo['url']}api/assets/set/salle:{feature.get('AttachmentId')}/?orig={combo.get('orig')}",
                    key=combo.get("secret"),
                )
                combo_response = self.requests.post(signed_url, json={"asset": attachment})
                combo_response.raise_for_status()
                response.append(combo_response.json())

        return response

############
# Features #
############

    @endpoint(
        name="get-features",
        perm="can_access",
        description="Get Features.",
        long_description="Récupère la liste des Features dans ATAL.",
        display_category="Features",
        display_order=1,
        methods=["get"],
        parameters={
            "expands": {
                "description": "Liste à étendre dans le résultat retourné (valeurs séparées par une virgule)",
                "type": "str",
                "example_value": "FeatureCategory",
            },
            "filters": {
                "description": "Filtre en query string",
                "type": "str",
                "example_value": "Id eq 177",
            },
        },
    )
    def get_features(self, request, expands=None, filters=None):
        url = f"{self.base_url}/api/Features"
        headers = {
            "accept": "application/json",
            "X-API-Key": self.api_key,
        }

        params = {}
        if expands:
            params["$expand"] = expands
        if filters:
            params["$filter"] = filters

        if not params:
            params["$top"] = 100

        response = self.requests.get(
            url,
            headers=headers,
            params=params,
            verify=False,
        )
        response.raise_for_status()

        return {"data": response.json()}

################
# Utilitaires #
################

    def get_service(self, service_id):
        if not getattr(settings, "KNOWN_SERVICES", {}).get(service_id):
            return
        services = list(settings.KNOWN_SERVICES[service_id].values())
        return services

    def get_rooms_for_indisponibilities(self, request, room):
        rooms = [room,]
        # Get infos salle pour récupérer le parent s'il existe
        infos_salle = self.read_room(request, room)
        parent_id = infos_salle.get("ParentId")
        # Vérification si le parent est louable
        if parent_id:
            parent_room = self.read_patrimoines_louable(request, f"and Id eq {parent_id}")
            if parent_room:
                rooms.append(parent_id)
        # Vérification s'il y a des enfants louable
        kids_rooms = self.read_kids_rooms(request, room)["data"]
        if kids_rooms:
            rooms.extend([x["Id"] for x in kids_rooms])

        return rooms

    def get_indisponibilities(self, request, rooms, start):
        query = ""
        for room in rooms:
            query += f" or RoomId eq {room}" if query else f"RoomId eq {room}"
        indisponibilites = self.read_dates_dispo(request, start, filters=query)["data"]
        return indisponibilites
