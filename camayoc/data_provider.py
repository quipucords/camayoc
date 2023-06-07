import random
from itertools import chain
from itertools import cycle

from littletable import Table

from camayoc.api import HTTPError
from camayoc.config import settings
from camayoc.exceptions import NoMatchingDataDefinitionException
from camayoc.qpc_models import Credential
from camayoc.qpc_models import Scan
from camayoc.qpc_models import Source
from camayoc.tests.qpc.utils import get_object_id
from camayoc.tests.qpc.utils import sort_and_delete
from camayoc.utils import uuid4


def replace_definition_name(definition, name=None):
    if not name:
        name = f"{definition.name}-{uuid4()}"
    new_definition = definition.copy()
    new_definition.name = name
    return new_definition


class ModelWorker:
    def __init__(self, data_provider, definitions, model_class):
        self._data_provider = data_provider
        self._model_class = model_class
        definition_table = Table()
        definition_table.insert_many(definitions)
        self._defined_models = definition_table
        self._created_models = {}

    def _select_definitions(self, match_criteria):
        matching = self._defined_models.where(**match_criteria)
        if not matching:
            msg = (
                "No data matching provided criteria. "
                "Try changing 'match_criteria' or review Camayoc configuration."
            )
            raise NoMatchingDataDefinitionException(msg)
        return list(matching)

    def _create_model(self, model):
        try:
            model.create()
        except HTTPError as e:
            if "already exists" not in e.api_error_message:
                raise

            if not model._id and model.name:
                model._id = get_object_id(model)

        self._created_models[model.name] = model

    def _create_dependencies(self, definition, new):
        dependencies_ids = []
        if issubclass(self._model_class, Credential):
            return dependencies_ids

        if issubclass(self._model_class, Source):
            dependency_definitions = self._data_provider.credentials._select_definitions(
                match_criteria={"name": Table.is_in(definition.credentials)}
            )
            for dependency_definition in dependency_definitions:
                if new:
                    dependency_definition = replace_definition_name(dependency_definition)
                credential = self._data_provider.credentials._create_from_definition(
                    definition=dependency_definition,
                    new_dependencies=new,
                    data_only=False,
                )
                dependencies_ids.append(credential._id)
            return dependencies_ids

        if issubclass(self._model_class, Scan):
            dependency_definitions = self._data_provider.sources._select_definitions(
                match_criteria={"name": Table.is_in(definition.sources)}
            )
            for dependency_definition in dependency_definitions:
                if new:
                    dependency_definition = replace_definition_name(dependency_definition)
                source = self._data_provider.sources._create_from_definition(
                    definition=dependency_definition,
                    new_dependencies=new,
                    data_only=False,
                )
                dependencies_ids.append(source._id)
            return dependencies_ids

    def _create_from_definition(self, definition, new_dependencies, data_only):
        if existing_model := self._created_models.get(definition.name):
            return existing_model

        dependencies_ids = self._create_dependencies(definition, new=new_dependencies)
        new_model = self._model_class.from_definition(definition, dependencies=dependencies_ids)

        if not data_only:
            self._create_model(new_model)

        return new_model

    def defined_many(self, match_criteria):
        matching_definitions = self._select_definitions(match_criteria)
        random.shuffle(matching_definitions)

        for definition in matching_definitions:
            model = self._create_from_definition(
                definition=definition, new_dependencies=False, data_only=False
            )
            yield model

    def defined_one(self, match_criteria):
        defined_generator = self.defined_many(match_criteria)
        return next(defined_generator)

    def new_many(self, match_criteria, new_dependencies=True, data_only=True):
        matching_definitions = self._select_definitions(match_criteria)
        random.shuffle(matching_definitions)

        for definition in cycle(matching_definitions):
            definition = replace_definition_name(definition)
            model = self._create_from_definition(
                definition=definition,
                new_dependencies=new_dependencies,
                data_only=data_only,
            )
            yield model

    def new_one(self, match_criteria, new_dependencies=True, data_only=True):
        new_generator = self.new_many(
            match_criteria=match_criteria,
            new_dependencies=new_dependencies,
            data_only=data_only,
        )
        return next(new_generator)


class DataProvider:
    def __init__(
        self,
        credentials=settings.credentials,
        sources=settings.sources,
        scans=settings.scans,
    ):
        self.credentials = ModelWorker(
            data_provider=self, definitions=credentials, model_class=Credential
        )
        self.sources = ModelWorker(data_provider=self, definitions=sources, model_class=Source)
        self.scans = ModelWorker(data_provider=self, definitions=scans, model_class=Scan)
        self._stores = ("credentials", "sources", "scans")

    def mark_for_cleanup(self, *objects):
        for obj in objects:
            obj_name = f"manually-added-{obj.name}"
            for store in self._stores:
                worker = getattr(self, store)
                if isinstance(obj, worker._model_class):
                    worker._created_models[obj_name] = obj

    def cleanup(self):
        trash = chain.from_iterable(
            (getattr(self, store)._created_models.values() for store in self._stores)
        )
        sort_and_delete(trash)
