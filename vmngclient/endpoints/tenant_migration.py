# mypy: disable-error-code="empty-body"
from io import BufferedReader
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from pydantic import BaseModel, Field

from vmngclient.endpoints import APIEndpoints, CustomPayloadType, PreparedPayload, get, post, versions
from vmngclient.model.tenant import Tenant


class MigrationTokenQueryParams(BaseModel):
    migration_id: str = Field(alias="migrationId")


class ExportInfo(BaseModel):
    process_id: str = Field(alias="processId")


class ImportInfo(BaseModel):
    process_id: str = Field(alias="processId")
    migration_token_url: str = Field(alias="migrationTokenURL")

    @property
    def migration_token_query(self) -> str:
        return urlsplit(self.migration_token_url).query

    @property
    def migration_token_query_params(self) -> MigrationTokenQueryParams:
        query = self.migration_token_query
        return MigrationTokenQueryParams.parse_obj(parse_qsl(query))


class MigrationInfo(BaseModel):
    process_id: str = Field(alias="processId")


class MigrationFile(CustomPayloadType):
    def __init__(self, data: BufferedReader):
        self.payload = PreparedPayload(files={"file": (Path(data.name).name, data)})

    def prepared(self) -> PreparedPayload:
        return self.payload


class TenantMigration(APIEndpoints):
    @get("/tenantmigration/download/{path}")
    def download_tenant_data(self, path: str = "default.tar.gz") -> bytes:
        ...

    @post("/tenantmigration/export")
    def export_tenant_data(self, payload: Tenant) -> ExportInfo:
        ...

    @get("/tenantmigration/migrationToken")
    def get_migration_token(self, params: MigrationTokenQueryParams) -> str:
        ...

    @versions("<20.13")
    @post("/tenantmigration/import")
    def import_tenant_data(self, payload: MigrationFile) -> ImportInfo:
        ...

    @versions(">=20.13")
    @post("/tenantmigration/import/{migration_key}")
    def import_tenant_data_with_key(self, payload: MigrationFile, migration_key: str) -> ImportInfo:
        ...

    @post("/tenantmigration/networkMigration")
    def migrate_network(self, payload: str) -> MigrationInfo:
        ...

    def retrigger_network_migration(self):
        # GET /tenantmigration/networkMigration
        ...
