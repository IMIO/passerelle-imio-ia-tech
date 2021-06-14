#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests

from django.db import models
from django.utils.translation import ugettext_lazy as _
from passerelle.base.models import BaseResource
from passerelle.utils.api import endpoint


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
        verbose_name = _("Connecteur Atal (iMio)")

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
