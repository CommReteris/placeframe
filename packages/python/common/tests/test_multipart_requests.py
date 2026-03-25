from typing import Annotated
from uuid import UUID, uuid4

import pytest
from common.multipart_requests import (
    MultipartRequestModel,
    MultipartRequestOperation,
    multipart_json,
    multipart_json_list,
)
from litestar import Litestar, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from pydantic import BaseModel, BeforeValidator, Json, ValidationError


class _CameraConfig(BaseModel):
    width: int


class _MultipartUuidListPayload(MultipartRequestModel):
    reconstruction_ids: Annotated[Json[list[UUID]], BeforeValidator(multipart_json_list)]


class _MultipartObjectPayload(MultipartRequestModel):
    camera_config: Annotated[Json[_CameraConfig], BeforeValidator(multipart_json)]


class _MultipartRoutePayload(MultipartRequestModel):
    reconstruction_ids: Annotated[Json[list[UUID]], BeforeValidator(multipart_json_list)]
    camera_config: Annotated[Json[_CameraConfig], BeforeValidator(multipart_json)]
    image: UploadFile


@post("/localization", operation_class=MultipartRequestOperation, sync_to_thread=False)
def _multipart_route(data: Annotated[_MultipartRoutePayload, Body(media_type=RequestEncodingType.MULTI_PART)]) -> None:
    del data


def test_multipart_request_model_parses_csv_uuid_lists() -> None:
    first_id = uuid4()
    second_id = uuid4()

    payload = _MultipartUuidListPayload.model_validate({"reconstruction_ids": [f"{first_id},{second_id}"]})

    assert payload.reconstruction_ids == [first_id, second_id]


def test_multipart_request_model_parses_json_objects_from_single_part_lists() -> None:
    payload = _MultipartObjectPayload.model_validate({"camera_config": ['{"width": 1280}']})

    assert payload.camera_config == _CameraConfig(width=1280)


def test_multipart_request_model_rejects_multiple_json_object_parts() -> None:
    with pytest.raises(ValidationError) as exc_info:
        _MultipartObjectPayload.model_validate({"camera_config": ['{"width": 1280}', '{"width": 720}']})

    assert exc_info.value.errors()[0]["type"] == "value_error"


def test_multipart_request_operation_marks_uuid_arrays_as_json() -> None:
    app = Litestar(route_handlers=[_multipart_route])

    schema = app.openapi_schema.to_schema()
    content = schema["paths"]["/localization"]["post"]["requestBody"]["content"]["multipart/form-data"]

    assert content["encoding"]["camera_config"]["contentType"] == "application/json"
    assert content["encoding"]["reconstruction_ids"]["contentType"] == "application/json"
