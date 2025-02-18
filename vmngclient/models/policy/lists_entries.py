from enum import Enum
from ipaddress import IPv4Address, IPv4Network, IPv6Network
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress, field_validator, model_validator

from vmngclient.models.common import InterfaceTypeEnum, check_fields_exclusive


def check_jitter_ms(jitter_str: str) -> str:
    jitter = int(jitter_str)
    if jitter < 1 or jitter > 1000:
        raise ValueError("jitter should be in range 1-1000")
    return jitter_str


def check_latency_ms(latency_str: str) -> str:
    latency = int(latency_str)
    if latency < 1 or latency > 1000:
        raise ValueError("latency should be in range 1-1000")
    return latency_str


def check_loss_percent(loss_str: str) -> str:
    loss = int(loss_str)
    if loss < 0 or loss > 100:
        raise ValueError("loss should be in range 0-100")
    return loss_str


class PolicerExceedAction(str, Enum):
    DROP = "drop"
    REMARK = "remark"


class EncapEnum(str, Enum):
    IPSEC = "ipsec"
    GRE = "gre"


class PathPreferenceEnum(str, Enum):
    DIRECT_PATH = "direct-path"
    MULTI_HOP_PATH = "multi-hop-path"
    ALL_PATHS = "all-paths"


class ColorDSCPMap(BaseModel):
    color: str
    dscp: int = Field(ge=0, le=63)


class ColorGroupPreference(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    color_preference: str = Field(alias="colorPreference")
    path_preference: PathPreferenceEnum = Field(alias="pathPreference")


class FallbackBestTunnel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    criteria: str
    jitter_variance: Optional[str] = Field(None, alias="jitterVariance", description="jitter variance in ms")
    latency_variance: Optional[str] = Field(None, alias="latencyVariance", description="latency variance in ms")
    loss_variance: Optional[str] = Field(None, alias="lossVariance", description="loss variance as percentage")

    # validators
    _jitter_validator = field_validator("jitter_variance")(check_jitter_ms)  # type: ignore[type-var]
    _latency_validator = field_validator("latency_variance")(check_latency_ms)  # type: ignore[type-var]
    _loss_validator = field_validator("loss_variance")(check_loss_percent)  # type: ignore[type-var]

    @model_validator(mode="after")
    def check_criteria(self):
        expected_criteria = set()
        if self.jitter_variance is not None:
            expected_criteria.add("jitter")
        if self.latency_variance is not None:
            expected_criteria.add("latency")
        if self.loss_variance is not None:
            expected_criteria.add("loss")
        if len(expected_criteria) < 1:
            raise ValueError("At least one variance type needs to be present")
        observed_criteria = set(str(self.criteria).split("-"))
        if expected_criteria != observed_criteria:
            if len(expected_criteria) == 1:
                raise ValueError(f"Criteria must contain: {expected_criteria}")
            raise ValueError(f"Criteria must contain: {expected_criteria} separated by hyphen")
        return self


class DataPrefixListEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ip_prefix: IPv4Network = Field(alias="ipPrefix")


class SiteListEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    site_id: str = Field(alias="siteId")


class VPNListEntry(BaseModel):
    vpn: str = Field(description="0-65530 range or single number")

    @field_validator("vpn")
    @classmethod
    def check_vpn_range(cls, vpns_str: str):
        vpns = [int(vpn) for vpn in vpns_str.split("-")]
        if len(vpns) > 2:
            raise ValueError("VPN range should consist two integers separated by hyphen")
        for vpn in vpns:
            if vpn < 0 or vpn > 65530:
                raise ValueError("VPN should be in range 0-65530")
        if len(vpns) == 2 and vpns[0] >= vpns[1]:
            raise ValueError("Second VPN in range should be greater than first")
        return vpns_str


class ZoneListEntry(BaseModel):
    vpn: Optional[str] = Field(None, description="0-65530 single number")
    interface: Optional[InterfaceTypeEnum] = None

    @field_validator("vpn")
    @classmethod
    def check_vpn_range(cls, vpn_str: str):
        vpn = int(vpn_str)
        if vpn < 0 or vpn > 65530:
            raise ValueError("VPN should be in range 0-65530")
        return vpn_str

    @model_validator(mode="after")
    def check_vpn_xor_interface(self):
        check_fields_exclusive(self.__dict__, {"vpn", "interface"}, True)
        return self


class FQDNListEntry(BaseModel):
    pattern: str


class GeoLocationListEntry(BaseModel):
    country: Optional[str] = Field(description="ISO-3166 alpha-3 country code eg: FRA")
    continent: Optional[str] = Field(description="One of 2-letter continent codes: AF, NA, OC, AN, AS, EU, SA")

    @model_validator(mode="after")
    def check_country_xor_continent(self):
        check_fields_exclusive(self.__dict__, {"country", "continent"}, True)
        return self


class PortListEntry(BaseModel):
    port: str

    @field_validator("port")
    @classmethod
    def check_port_range(cls, port_str: str):
        port = int(port_str)
        if port < 0 or port > 65535:
            raise ValueError("Port should be in range 0-65535")
        return port_str


class ProtocolNameListEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    protocol_name: str = Field(alias="protocolName")


class LocalAppListEntry(BaseModel):
    app_family: Optional[str] = Field(alias="appFamily")
    app: Optional[str]

    @model_validator(mode="after")
    def check_app_xor_appfamily(self):
        check_fields_exclusive(self.__dict__, {"app", "app_family"}, True)
        return self


class AppListEntry(BaseModel):
    app_family: Optional[str] = Field(alias="appFamily")
    app: Optional[str]

    @model_validator(mode="after")
    def check_app_xor_appfamily(self):
        check_fields_exclusive(self.__dict__, {"app", "app_family"}, True)
        return self


class ColorListEntry(BaseModel):
    color: str


class DataIPv6PrefixListEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ipv6_prefix: IPv6Network = Field(alias="ipv6Prefix")


class LocalDomainListEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name_server: str = Field(
        pattern="^[^*+].*",
        alias="nameServer",
        max_length=240,
        description="Must be valid std regex."
        "String cannot start with a '*' or a '+', be empty, or be more than 240 characters",
    )


class IPSSignatureListEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    generator_id: str = Field(alias="generatorId")
    signature_id: str = Field(alias="signatureId")


class URLListEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pattern: str


class CommunityListEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    community: str = Field(description="Example: 1000:10000 or internet or local-AS or no advertise or no-export")


class PolicerListEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    burst: str = Field(description="bytes: integer in range 15000-10000000")
    exceed: PolicerExceedAction = PolicerExceedAction.DROP
    rate: str = Field(description="bps: integer in range 8-100000000000")

    @field_validator("burst")
    @classmethod
    def check_burst(cls, burst_str: str):
        burst = int(burst_str)
        if burst < 15000 or burst > 10000000:
            raise ValueError("burst should be in range 15000-10000000")
        return burst_str

    @field_validator("rate")
    @classmethod
    def check_rate(cls, rate_str: str):
        rate = int(rate_str)
        if rate < 8 or rate > 100000000000:
            raise ValueError("rate should be in range 8-10000000")
        return rate_str


class ASPathListEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    as_path: str = Field(alias="asPath")


class ClassMapListEntry(BaseModel):
    queue: str

    @field_validator("queue")
    @classmethod
    def check_queue(cls, queue_str: str):
        queue = int(queue_str)
        if queue < 0 or queue > 7:
            raise ValueError("queue should be in range 0-7")
        return queue_str


class MirrorListEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    remote_dest: IPvAnyAddress = Field(alias="remoteDest")
    source: IPvAnyAddress


class AppProbeClassListEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    map: List[ColorDSCPMap]
    forwarding_class: str = Field(alias="forwardingClass")


class SLAClassListEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    latency: Optional[str] = None
    loss: Optional[str] = None
    jitter: Optional[str] = None
    app_probe_class: Optional[str] = Field(alias="appProbeClass")
    fallback_best_tunnel: Optional[FallbackBestTunnel] = Field(None, alias="fallbackBestTunnel")

    # validators
    _jitter_validator = field_validator("jitter")(check_jitter_ms)  # type: ignore[type-var]
    _latency_validator = field_validator("latency")(check_latency_ms)  # type: ignore[type-var]
    _loss_validator = field_validator("loss")(check_loss_percent)  # type: ignore[type-var]

    @model_validator(mode="after")
    def check_at_least_one_criteria_is_set(self):
        if not any([self.latency, self.loss, self.jitter]):
            raise ValueError("At leas one of jitter, loss or latency entries must be set")
        return self


class TLOCListEntry(BaseModel):
    tloc: IPv4Address
    color: str
    encap: EncapEnum
    preference: str

    @field_validator("preference")
    @classmethod
    def check_preference(cls, preference_str: str):
        preference = int(preference_str)
        if preference < 0 or preference > 4294967295:
            raise ValueError("preference should be in range 0-4294967295")
        return preference_str


class PreferredColorGroupListEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    primary_preference: ColorGroupPreference = Field(alias="primaryPreference")
    secondary_preference: Optional[ColorGroupPreference] = Field(None, alias="secondaryPreference")
    tertiary_preference: Optional[ColorGroupPreference] = Field(None, alias="tertiaryPreference")

    @model_validator(mode="after")
    def check_optional_preferences_order(self):
        if self.secondary_preference is None and self.tertiary_preference is not None:
            raise ValueError("tertiary_preference cannot be set without secondary_preference")
        return self


class PrefixListEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ip_prefix: IPv4Network = Field(alias="ipPrefix")
    ge: Optional[str]
    le: Optional[str]

    @field_validator("ge", "le")
    @classmethod
    def check_ge_and_le(cls, ge_le_str: str):
        ge_le = int(ge_le_str)
        if ge_le < 0 or ge_le > 32:
            raise ValueError("ge,le should be in range 0-32")
        return ge_le_str


class IPv6PrefixListEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ipv6_prefix: IPv6Network = Field(alias="ipv6Prefix")
    ge: Optional[str]
    le: Optional[str]

    @field_validator("ge", "le")
    @classmethod
    def check_ge_and_le(cls, ge_le_str: str):
        ge_le = int(ge_le_str)
        if ge_le < 0 or ge_le > 128:
            raise ValueError("ge,le should be in range 0-128")
        return ge_le_str
