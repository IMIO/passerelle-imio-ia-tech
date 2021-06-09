#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests


from django.db import models
from django.utils.translation import ugettext_lazy as _
from passerelle.base.models import BaseResource
from passerelle.compat import json_loads
from passerelle.utils.api import endpoint
from passerelle.utils.jsonresponse import APIError


class imio_atal(BaseResource):
    base_url = models.URLField(
        max_length=256,
        blank=False,
        verbose_name=_("Base URL"),
        help_text=_("API base URL"),
    )
    verify_cert = models.BooleanField(default=True, verbose_name=_("Check HTTPS Certificate validity"))
    api_key = models.CharField(max_length=128, verbose_name=_("API Key"))

    category = _("Business Process Connectors")

    class Meta:
        verbose_name = _("Connecteur Atal (iMio)")

    @classmethod
    def get_verbose_name(cls):
        return cls._meta.verbose_name

    @endpoint()
    def test(self):
        response = requests.get(
            url=self.base_url,
            headers={"Accept": "text/plain", "X-API-Key": self.api_key},
        )

        return "True"
