from dataclasses import dataclass


@dataclass
class AirtableConfig:
    api_key: str
    base_url: str = "https://api.airtable.com"