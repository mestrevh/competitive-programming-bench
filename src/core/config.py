from pydantic import BaseModel, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, Any

class ProviderConfig(BaseModel):
    api_key: str
    model_name: str
    base_url: str
    input_price: float = 0.0
    output_price: float = 0.0

class _Config(BaseSettings):
    providers: Dict[str, ProviderConfig] = {}

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="allow"
    )

    @model_validator(mode='before')
    @classmethod
    def parse_providers(cls, data: Any) -> Any:
        """Parse provider configs from environment variables"""
        if isinstance(data, dict):
            providers = {}
            
            provider_names = set()
            for key in list(data.keys()):
                if '__' in key and key.count('__') == 1:
                    provider_name = key.split('__')[0].lower()
                    provider_names.add(provider_name)
            
            for provider_name in provider_names:
                api_key = data.get(f'{provider_name}__api_key')
                model_name = data.get(f'{provider_name}__model_name') or data.get(f'{provider_name}__model')
                base_url = data.get(f'{provider_name}__base_url')
                input_price = float(data.get(f'{provider_name}__input_price') or 0.0)
                output_price = float(data.get(f'{provider_name}__output_price') or 0.0)
                
                if api_key and model_name and base_url:
                    providers[provider_name] = ProviderConfig(
                        api_key=api_key,
                        model_name=model_name,
                        base_url=base_url,
                        input_price=input_price,
                        output_price=output_price
                    )
            
            data['providers'] = providers
        
        return data

    def list_providers(self) -> Dict[str, ProviderConfig]:
        """Retorna um dicionário com o nome do provedor e seus dados"""
        return self.providers

config = _Config()