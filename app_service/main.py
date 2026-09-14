from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, status
from psycopg.errors import UniqueViolation
from pydantic import BaseModel, ConfigDict, Field

from app_service import repository


class ApplicationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    package_name: str = Field(
        min_length=3,
        max_length=200,
        pattern=r"^[A-Za-z0-9_.]+$",
    )
    category: str = Field(min_length=1, max_length=100)


class ApplicationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    package_name: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
        pattern=r"^[A-Za-z0-9_.]+$",
    )
    category: str | None = Field(default=None, min_length=1, max_length=100)
    active: bool | None = None


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    package_name: str
    category: str
    active: bool


app = FastAPI(
    title="Sahabino Application Service",
    version="1.0.0",
    description="Stores the list of applications used by the crawler.",
)


@app.get("/health")
def health():
    return {"status": "ok" if repository.database_is_ready() else "error"}


@app.post(
    "/applications",
    response_model=ApplicationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_application(body: ApplicationCreate):
    try:
        return repository.create_application(body.model_dump())
    except UniqueViolation as exc:
        raise HTTPException(
            status_code=409,
            detail="Package name already exists",
        ) from exc


@app.get("/applications", response_model=list[ApplicationOut])
def list_applications(active_only: Annotated[bool, Query()] = False):
    return repository.list_applications(active_only)


@app.get("/applications/{application_id}", response_model=ApplicationOut)
def get_application(application_id: int):
    result = repository.get_application(application_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Application not found")

    return result


@app.put("/applications/{application_id}", response_model=ApplicationOut)
def update_application(application_id: int, body: ApplicationUpdate):
    try:
        result = repository.update_application(
            application_id,
            body.model_dump(exclude_none=True),
        )
    except UniqueViolation as exc:
        raise HTTPException(
            status_code=409,
            detail="Package name already exists",
        ) from exc

    if result is None:
        raise HTTPException(status_code=404, detail="Application not found")

    return result


@app.delete("/applications/{application_id}", response_model=ApplicationOut)
def deactivate_application(application_id: int):
    result = repository.deactivate_application(application_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Application not found")

    return result
