CREATE_WORK_REQUEST = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "atal_requester_id": {
            "description": "Numéro de l'utilisateur demandeur dans ATAL",
            "type": "integer",
        },
        "atal_contact_firstname": {
            "description": "Prénom du contact transmis vers ATAL",
            "type": "string",
        },
        "atal_contact_lastname": {
            "description": "Nom du contact transmis vers ATAL",
            "type": "string",
        },
        "atal_contact_email": {
            "description": "Adresse mail du contact transmis vers ATAL",
            "type": "string",
        },
        "atal_contact_phone": {
            "description": "Numéro de téléphone du contact transmis vers ATAL",
            "type": "string",
        },
        "atal_contact_mobile": {
            "description": "Numéro de mobile du contact transmis vers ATAL",
            "type": "string",
        },
        "atal_contact_address": {
            "description": "Adresse du contact transmis vers ATAL",
            "type": "string",
        },
        "atal_contact_zipcode": {
            "description": "Code postal du contact transmis vers ATAL",
            "type": "string",
        },
        "atal_contact_city": {
            "description": "Localité du contact transmis vers ATAL",
            "type": "string",
        },
        "atal_operator": {
            "description": "Nom de l'opérateur",
            "type": "string",
        },
        "atal_object": {
            "description": "Objet de la demande",
            "type": "string",
        },
        "atal_description": {
            "description": "Description de la demande",
            "type": "string",
        },
        "atal_desired_date": {
            "description": "Date désirée pour la demande (ex: 2021-06-16T13:30:25.365Z)",
            "type": "string",
        },
        "atal_recipient_id": {
            "description": "Numéro identifiant du destinataire",
            "type": "integer",
        },
        "atal_requesting_department_id": {
            "description": "Numéro identifiant du département demandeur",
            "type": "integer",
        },
        "atal_request_type": {
            "description": "Numéro identifiant du type de requête",
            "type": "integer",
        },
        "atal_request_date": {
            "description": "Date de la requête",
            "type": "string",
        },
        "atal_localization": {
            "description": "Lieu de l'intervention",
            "type": "string",
        },
        "atal_patrimony_id": {
            "description": "Numéro identifiant du patrimoine",
            "type": "integer",
        },
        "atal_longitude": {
            "description": "Coordonée longitude du lieu de l'intervention",
            "type": "integer",
        },
        "atal_latitude": {
            "description": "Coordonée latitude du lieu de l'intervention",
            "type": "integer",
        },
    },
    # TODO : define required fields
    # "required": [],
    # TODO : complete example
    # "example": {
    #     "atal_requester_id": 1,
    # }
}
# TODO : finalize this s
CREATE_ATTACHMENT = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "atal_work_request_uuid": {
            "description": "Numéro d'identification uuid de la demande dans ATAL.",
            "type": "string",
        },
        "atal_attachment1": {
            "description": "Fichier 1",
            "type": "object",
            "properties": {
                "content": {
                    "description": "base64 encoded file",
                    "type": "string",
            }
        },
    },
    "example": {
        "atal_work_request_uuid": "11865d87-336b-49b3-e181-08d76f93d6b4",
        "atal_attachment1": "Fichier 1",
    }, 
}