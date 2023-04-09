import re
from dataclasses import dataclass
from typing import List, Tuple, Union

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

from django.db.models import Model

from worf.serializers import Serializer

OPEN_API_VERSION = "3.0.2"
SUPPORTED_FORMATS = ["json", "yaml"]


@dataclass
class SchemaMetadata:
    path: str
    method: str
    description: str
    serializer: Serializer
    is_list: bool
    model: Model
    tag: str


class OpenApiGenerator:
    def __init__(self, title: str, base_url: str, version: str):
        self.title = title
        self.base_url = base_url
        self.version = version

    def get_schema(
        self, endpoints: List[SchemaMetadata], _format: str
    ) -> Union[dict, str]:
        if _format not in SUPPORTED_FORMATS:
            raise Exception(f"Format {_format} not supported")

        spec = APISpec(
            title=self.title,
            version=self.version,
            openapi_version=OPEN_API_VERSION,
            plugins=[MarshmallowPlugin()],
        )
        spec.options["servers"] = [{"url": self.base_url}]

        already_seen_components = set()
        for endpoint in endpoints:
            component_schema = self.get_component_schema(endpoint.serializer)
            component_name = endpoint.model.__name__
            if component_name not in already_seen_components:
                already_seen_components.add(component_name)
                spec.components.schema(component_name, schema=component_schema)

            request_schema, response_schema = self._resolve_schemas(
                endpoint.is_list, component_name
            )
            parameters = self._get_parameters(endpoint.path)
            operations = self._get_operations(
                endpoint.method,
                endpoint.description,
                [endpoint.tag],
                request_schema,
                response_schema,
            )

            spec.path(path=endpoint.path, parameters=parameters, operations=operations)

        if _format == "json":
            return spec.to_dict()
        elif _format == "yaml":
            return spec.to_yaml()
        else:
            raise Exception(f"Format {_format} not handled properly")

    @staticmethod
    def _get_operations(
        method: str, description: str, tags: List[str], request_schema, response_schema
    ) -> dict:
        if method.lower() == "get":
            operations = {
                method.lower(): {
                    "tags": tags,
                    "responses": {
                        200: {
                            "content": {
                                "application/json": {"schema": response_schema}
                            },
                            "description": description,
                        }
                    },
                }
            }
        elif method.lower() == "put":
            operations = {
                method.lower(): {
                    "tags": tags,
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": request_schema}},
                    },
                    "responses": {200: {"description": description}},
                }
            }
        elif method.lower() == "delete":
            operations = {
                method.lower(): {
                    "tags": tags,
                    "responses": {200: {"description": description}},
                }
            }
        else:
            operations = {
                method.lower(): {
                    "tags": tags,
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": request_schema}},
                    },
                    "responses": {
                        200: {
                            "content": {
                                "application/json": {"schema": response_schema}
                            },
                            "description": description,
                        }
                    },
                }
            }

        return operations

    @staticmethod
    def _get_parameters(path: str) -> List[dict]:
        parameter_names = re.findall(r"{(\w+)}", path)
        parameters = []
        for name in parameter_names:
            parameters.append(
                {
                    "in": "path",
                    "name": name,
                    "required": True,
                    "schema": {"type": "integer"},
                }
            )

        return parameters

    @staticmethod
    def _resolve_schemas(is_list: bool, component_name: str) -> Tuple[dict, dict]:
        if is_list:
            request_schema = {
                "type": "array",
                "items": {"$ref": f"#/components/schemas/{component_name}"},
            }
            response_schema = {
                "type": "array",
                "items": {"$ref": f"#/components/schemas/{component_name}"},
            }
        else:
            request_schema = {"$ref": f"#/components/schemas/{component_name}"}
            response_schema = {"$ref": f"#/components/schemas/{component_name}"}

        return request_schema, response_schema

    @staticmethod
    def get_component_schema(serializer) -> Serializer:
        if not isinstance(serializer, type):
            serializer = serializer.__class__

        return serializer
