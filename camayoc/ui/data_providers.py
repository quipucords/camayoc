import time
from collections import defaultdict
from copy import deepcopy
from urllib.parse import urljoin

import factory

from camayoc.api import Client as APIClient
from camayoc.exceptions import APIResultsEmpty
from camayoc.exceptions import FilteredAPIResultsEmpty

_global_db = defaultdict(list)
_global_client = APIClient()


class AbstractDataProvider:
    def __init__(self):
        self.db = _global_db
        self.api_client = _global_client
        self.last_refresh_timestamp = 0
        self.timeout = 60

    def get_field_name(self):
        field_name = getattr(self, "ENDPOINT", None)
        return field_name.rstrip("/")

    def set_db_table(self, new_values):
        field_name = self.get_field_name()
        self.db[field_name] = new_values

    def get_db_table(self):
        field_name = self.get_field_name()
        return self.db[field_name]

    def get_paged_api_response(self):
        obtained_values = []
        endpoint = getattr(self, "ENDPOINT", None)
        endpoint = endpoint.rstrip("/") + "/"
        next_page_url = urljoin(self.api_client.url, endpoint)

        while next_page_url:
            response = self.api_client.get(next_page_url).json()
            next_page_url = response.get("next")
            obtained_values.extend(response.get("results"))

        return obtained_values

    def transform_raw_value(self, raw_value):
        return raw_value

    def reconcile_db(self):
        raw_new_values = self.get_paged_api_response()
        new_values = [self.transform_raw_value(val) for val in raw_new_values]
        self.set_db_table(new_values)
        self.last_refresh_timestamp = time.monotonic()

    def db_needs_refresh(self):
        will_need_refresh = self.last_refresh_timestamp + self.timeout
        return time.monotonic() > will_need_refresh

    def yield_random_value(self, **kwargs):
        if self.db_needs_refresh():
            self.reconcile_db()

        all_values = self.get_db_table()

        if not all_values:
            msg = "'{}' endpoint did not return any results"
            raise APIResultsEmpty(msg.format(getattr(self, "ENDPOINT")))

        filtered_values = deepcopy(all_values)

        for key, value in kwargs.items():
            filtered_values = [item for item in filtered_values if item.get(key) == value]

        if not filtered_values:
            msg = "'{}' endpoint returned results, but none that match {}"
            raise FilteredAPIResultsEmpty(msg.format(getattr(self, "ENDPOINT"), kwargs))

        return factory.Faker._get_faker().random_element(filtered_values)


class SourceDataProvider(AbstractDataProvider):
    ENDPOINT = "sources"


class CredentialDataProvider(AbstractDataProvider):
    ENDPOINT = "credentials"


_source_data_provider = SourceDataProvider()
_credential_data_provider = CredentialDataProvider()


class APIDataProvider:
    @classmethod
    def get_source(cls, **kwargs):
        while True:
            value = _source_data_provider.yield_random_value(**kwargs)
            yield value.get("name")

    @classmethod
    def get_credential(cls, **kwargs):
        while True:
            value = _credential_data_provider.yield_random_value(**kwargs)
            yield value.get("name")
