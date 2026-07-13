from pydantic import BaseModel, ConfigDict


class SettingsBase(BaseModel):
    two_factor_enabled: bool = False
    email_alerts: bool = True
    slack_alerts: bool = False
    slack_webhook_url: str | None = None
    weekly_reports: bool = True
    theme: str = "dark"
    currency: str = "USD"


class SettingsUpdate(SettingsBase):
    pass


class SettingsResponse(SettingsBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str


class AWSAccountUpdate(BaseModel):
    account_id: str
    role_arn: str
    account_name: str | None = None
    region: str | None = "us-east-1"


class AWSAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    org_id: str
    account_id: str
    account_name: str
    role_arn: str | None = None
    external_id: str | None = None
    region: str
    is_active: bool
