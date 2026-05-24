from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, model_serializer


class UTCDatetimeModel(BaseModel):
    @model_serializer(mode='plain', when_used='json')
    def serialize_model(self) -> dict[str, Any]:
        result = {}
        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, datetime) and field_value.tzinfo is None:
                result[field_name] = field_value.replace(tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z')
            else:
                result[field_name] = field_value
        return result
