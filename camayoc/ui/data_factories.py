import tempfile
from collections import OrderedDict
from typing import Union
from typing import get_args
from typing import get_origin

import factory

from camayoc.config import get_config
from camayoc.data_provider import DataProvider
from camayoc.types.ui import AddCredentialDTO
from camayoc.types.ui import AddSourceDTO
from camayoc.types.ui import CredentialFormDTO
from camayoc.types.ui import LoginFormDTO
from camayoc.types.ui import NetworkCredentialFormDTO
from camayoc.types.ui import NetworkSourceFormDTO
from camayoc.types.ui import NewScanFormDTO
from camayoc.types.ui import PlainNetworkCredentialFormDTO
from camayoc.types.ui import SatelliteCredentialFormDTO
from camayoc.types.ui import SatelliteSourceFormDTO
from camayoc.types.ui import SelectSourceDTO
from camayoc.types.ui import SourceFormDTO
from camayoc.types.ui import SSHNetworkCredentialFormDTO
from camayoc.types.ui import TriggerScanDTO
from camayoc.types.ui import VCenterCredentialFormDTO
from camayoc.types.ui import VCenterSourceFormDTO

from .enums import CredentialTypes
from .enums import NetworkCredentialAuthenticationTypes
from .enums import NetworkCredentialBecomeMethods
from .enums import SourceConnectionTypes
from .enums import SourceTypes

optional_bool = OrderedDict([(None, 0.5), (True, 0.25), (False, 0.25)])


class UnionDTOFactoryOptions(factory.base.FactoryOptions):
    def get_model_class(self):
        original_model = getattr(self, "original_model", None)
        if original_model is None:
            setattr(self, "original_model", self.model)

        if get_origin(self.original_model) != Union:
            msg = "Meta.model must be an Union in Factory inheriting from " "UnionDTOFactory"
            raise factory.errors.FactoryError(msg)

        faker = factory.Faker._get_faker()
        new_class = faker.random_element(get_args(self.original_model))
        factory_class_name = f"{new_class.__name__}Factory"
        factory_class = globals().get(factory_class_name, None)
        if not factory_class:
            msg = f"{factory_class_name} definition not found"
            raise factory.errors.FactoryError(msg)
        return factory_class


class UnionDTOFactory(factory.Factory):
    _options_class = UnionDTOFactoryOptions


class LazyAttributeSubfactory(factory.SubFactory):
    def __init__(self, function, **kwargs):
        super().__init__(".", **kwargs)
        self.function = function
        self._logger = factory.declarations.logger

    def get_factory(self):
        return self.subfactory

    def evaluate(self, instance, step, extra):
        subfactory = self.function(instance)
        self.subfactory = subfactory
        return super().evaluate(instance, step, extra)


class LoginFormDTOFactory(factory.Factory):
    class Meta:
        model = LoginFormDTO

    username = get_config().get("qpc", {}).get("username")
    password = get_config().get("qpc", {}).get("password")


class PlainNetworkCredentialFormDTOFactory(factory.Factory):
    class Meta:
        model = PlainNetworkCredentialFormDTO

    credential_name = factory.Faker("text", max_nb_chars=56)
    authentication_type = NetworkCredentialAuthenticationTypes.USERNAME_AND_PASSWORD
    username = factory.Faker("user_name")
    password = factory.Faker("password")
    become_method = factory.Faker("random_element", elements=list(NetworkCredentialBecomeMethods))
    become_user = factory.Faker("user_name")
    become_password = factory.Faker("password")


def _existing_ssh_key_file():
    _, filename = tempfile.mkstemp()
    return filename


class SSHNetworkCredentialFormDTOFactory(factory.Factory):
    class Meta:
        model = SSHNetworkCredentialFormDTO

    credential_name = factory.Faker("text", max_nb_chars=56)
    authentication_type = NetworkCredentialAuthenticationTypes.SSH_KEY
    username = factory.Faker("user_name")
    ssh_key_file = factory.LazyFunction(_existing_ssh_key_file)
    passphrase = factory.Faker("password")
    become_method = factory.Faker("random_element", elements=list(NetworkCredentialBecomeMethods))
    become_user = factory.Faker("user_name")
    become_password = factory.Faker("password")


class NetworkCredentialFormDTOFactory(UnionDTOFactory):
    class Meta:
        model = NetworkCredentialFormDTO


class SatelliteCredentialFormDTOFactory(factory.Factory):
    class Meta:
        model = SatelliteCredentialFormDTO

    credential_name = factory.Faker("text", max_nb_chars=56)
    username = factory.Faker("user_name")
    password = factory.Faker("password")


class VCenterCredentialFormDTOFactory(factory.Factory):
    class Meta:
        model = VCenterCredentialFormDTO

    credential_name = factory.Faker("text", max_nb_chars=56)
    username = factory.Faker("user_name")
    password = factory.Faker("password")


class CredentialFormDTOFactory(UnionDTOFactory):
    class Meta:
        model = CredentialFormDTO


def _type_dependent_credential_form_factory(obj):
    credential_type = obj.credential_type
    if credential_type == CredentialTypes.NETWORK:
        return NetworkCredentialFormDTOFactory
    elif credential_type == CredentialTypes.SATELLITE:
        return SatelliteCredentialFormDTOFactory
    elif credential_type == CredentialTypes.VCENTER:
        return VCenterCredentialFormDTOFactory


class AddCredentialDTOFactory(factory.Factory):
    class Meta:
        model = AddCredentialDTO

    credential_type = factory.Faker("random_element", elements=list(CredentialTypes))
    credential_form_dto = LazyAttributeSubfactory(_type_dependent_credential_form_factory)


class SelectSourceDTOFactory(factory.Factory):
    class Meta:
        model = SelectSourceDTO

    source_type = factory.Faker("random_element", elements=list(SourceTypes))


class NetworkSourceFormDTOFactory(factory.Factory):
    class Meta:
        model = NetworkSourceFormDTO

    class Params:
        credentials_num = 1

    source_name = factory.Faker("text", max_nb_chars=56)

    @factory.lazy_attribute
    def addresses(self):
        faker = factory.Faker._get_faker()
        return [faker.ipv4_private()]

    @factory.lazy_attribute
    def credentials(self):
        data_provider = DataProvider()
        network_credential_generator = data_provider.credentials.new_many(
            {"type": "network"}, data_only=False
        )
        cred_names = []
        for _ in range(self.credentials_num):
            cred = next(network_credential_generator)
            cred_names.append(cred.name)
        return cred_names

    port = 22
    use_paramiko = factory.Faker("random_element", elements=optional_bool)


def _verify_ssl_based_on_connection(obj):
    if obj.connection == SourceConnectionTypes.DISABLE:
        return None
    faker = factory.Faker._get_faker()
    return faker.random_element(elements=optional_bool)


class SatelliteSourceFormDTOFactory(factory.Factory):
    class Meta:
        model = SatelliteSourceFormDTO

    class Params:
        credentials_num = 1

    source_name = factory.Faker("text", max_nb_chars=56)
    address = factory.Faker("ipv4_private")

    @factory.lazy_attribute
    def credentials(self):
        data_provider = DataProvider()
        network_credential_generator = data_provider.credentials.new_many(
            {"type": "satellite"}, data_only=False
        )
        cred_names = []
        for _ in range(self.credentials_num):
            cred = next(network_credential_generator)
            cred_names.append(cred.name)
        return cred_names

    connection = factory.Faker("random_element", elements=list(SourceConnectionTypes))
    verify_ssl = factory.LazyAttribute(_verify_ssl_based_on_connection)


class VCenterSourceFormDTOFactory(factory.Factory):
    class Meta:
        model = VCenterSourceFormDTO

    class Params:
        credentials_num = 1

    source_name = factory.Faker("text", max_nb_chars=56)
    address = factory.Faker("ipv4_private")

    @factory.lazy_attribute
    def credentials(self):
        data_provider = DataProvider()
        network_credential_generator = data_provider.credentials.new_many(
            {"type": "vcenter"}, data_only=False
        )
        cred_names = []
        for _ in range(self.credentials_num):
            cred = next(network_credential_generator)
            cred_names.append(cred.name)
        return cred_names

    connection = factory.Faker("random_element", elements=list(SourceConnectionTypes))
    verify_ssl = factory.LazyAttribute(_verify_ssl_based_on_connection)


class SourceFormDTOFactory(UnionDTOFactory):
    class Meta:
        model = SourceFormDTO


def _source_type_dependent_source_form_factory(obj):
    source_type = obj.select_source_type.source_type
    if source_type == SourceTypes.NETWORK_RANGE:
        return NetworkSourceFormDTOFactory
    elif source_type == SourceTypes.SATELLITE:
        return SatelliteSourceFormDTOFactory
    elif source_type == SourceTypes.VCENTER_SERVER:
        return VCenterSourceFormDTOFactory


class AddSourceDTOFactory(factory.Factory):
    class Meta:
        model = AddSourceDTO

    select_source_type = factory.SubFactory(SelectSourceDTOFactory)
    source_form = LazyAttributeSubfactory(_source_type_dependent_source_form_factory)


class NewScanFormDTOFactory(factory.Factory):
    class Meta:
        model = NewScanFormDTO

    scan_name = factory.Faker("text", max_nb_chars=56)
    max_concurrent_scans = None
    jboss_eap = factory.Faker(
        "random_element",
        elements=optional_bool,
    )
    fuse = factory.Faker(
        "random_element",
        elements=optional_bool,
    )
    jboss_web_server = factory.Faker(
        "random_element",
        elements=optional_bool,
    )
    decision_manager = factory.Faker(
        "random_element",
        elements=optional_bool,
    )
    # FIXME: produce real value
    alternate_dirs = None


class TriggerScanDTOFactory(factory.Factory):
    class Meta:
        model = TriggerScanDTO

    @factory.lazy_attribute
    def source_name(self):
        data_provider = DataProvider()
        source = data_provider.sources.new_one({}, data_only=False)
        return source.name

    scan_form = factory.SubFactory(NewScanFormDTOFactory)
