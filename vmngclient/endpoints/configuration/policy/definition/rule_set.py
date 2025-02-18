# mypy: disable-error-code="empty-body"
from vmngclient.endpoints import APIEndpoints, delete, get, post, put
from vmngclient.models.policy.definitions.rule_set import RuleSet
from vmngclient.models.policy.policy_definition import (
    PolicyDefinitionEditResponse,
    PolicyDefinitionEndpoints,
    PolicyDefinitionId,
    PolicyDefinitionInfo,
    PolicyDefinitionPreview,
)
from vmngclient.typed_list import DataSequence


class RuleSetEditPayload(RuleSet, PolicyDefinitionId):
    pass


class RuleSetInfo(RuleSet, PolicyDefinitionId, PolicyDefinitionInfo):
    pass


class ConfigurationPolicyRuleSetDefinition(APIEndpoints, PolicyDefinitionEndpoints):
    @post("/template/policy/definition/ruleset")
    def create_policy_definition(self, payload: RuleSet) -> PolicyDefinitionId:
        ...

    @delete("/template/policy/definition/ruleset/{id}")
    def delete_policy_definition(self, id: str) -> None:
        ...

    def edit_multiple_policy_definition(self):
        # PUT /template/policy/definition/ruleset/multiple/{id}
        ...

    @put("/template/policy/definition/ruleset/{id}")
    def edit_policy_definition(self, id: str, payload: RuleSetEditPayload) -> PolicyDefinitionEditResponse:
        ...

    @get("/template/policy/definition/ruleset", "data")
    def get_definitions(self) -> DataSequence[RuleSetInfo]:
        ...

    @get("/template/policy/definition/ruleset/{id}")
    def get_policy_definition(self, id: str) -> RuleSetInfo:
        ...

    @post("/template/policy/definition/ruleset/preview")
    def preview_policy_definition(self, payload: RuleSet) -> PolicyDefinitionPreview:
        ...

    @get("/template/policy/definition/ruleset/preview/{id}")
    def preview_policy_definition_by_id(self, id: str) -> PolicyDefinitionPreview:
        ...

    def save_policy_definition_in_bulk(self):
        # PUT /template/policy/definition/ruleset/bulk
        ...
