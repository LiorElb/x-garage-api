from dataclasses import dataclass

from pydantic import BaseModel, root_validator


@dataclass
class _MISSING:
    pass


MISSING = _MISSING()


class BaseUpdateModel(BaseModel):

    @root_validator(pre=True)
    def not_empty(cls, values):
        if not any(v != MISSING for v in values):
            raise ValueError('Must have at least 1 value')
        return values

    def dict(self, *args, **kwargs):
        kwargs['exclude_unset'] = True
        return super().dict(*args, **kwargs)
