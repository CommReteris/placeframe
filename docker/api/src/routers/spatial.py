from litestar.exceptions import ClientException
from sqlalchemy import Select, func


def validate_spatial_params(
    position_x: float | None,
    position_y: float | None,
    position_z: float | None,
    radius: float | None,
) -> tuple[float, float, float, float] | None:
    params = [position_x, position_y, position_z, radius]
    if not any(p is not None for p in params):
        return None
    if not all(p is not None for p in params):
        raise ClientException(
            "Cannot provide partial spatial parameters; position_x, position_y, position_z, and radius must all be provided together"
        )
    return (position_x, position_y, position_z, radius)  # type: ignore[return-value]


def apply_spatial_filter[T](
    query: Select[tuple[T]],
    col_x: object,
    col_y: object,
    col_z: object,
    position_x: float,
    position_y: float,
    position_z: float,
    radius: float,
) -> Select[tuple[T]]:
    return query.where(
        func.ST_3DDWithin(
            func.ST_MakePoint(col_x, col_y, col_z),
            func.ST_MakePoint(position_x, position_y, position_z),
            radius,
        )
    )
