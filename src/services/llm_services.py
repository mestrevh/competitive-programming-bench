from typing import Optional, Union, List, Dict, Any
from pydantic import BaseModel
from openai import OpenAI


class LLMResponse(BaseModel):
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    input_cost_usd: float = 0.0
    output_cost_usd: float = 0.0
    total_cost_usd: float = 0.0


class LLM:
    def __init__(self,
                 api_key: str,
                 base_url: str,
                 model: str,
                 temperature: float = 1.0,
                 top_p: float = 1.0,
                 seed: Optional[int] = None,
                 frequency_penalty: float = 0.0,
                 presence_penalty: float = 0.0,
                 input_price: float = 0.0,
                 output_price: float = 0.0):
        
        if not (0.0 <= temperature <= 2.0):
            raise ValueError("[LLM Service]: 0.0 <= temperature <= 2.0")
            
        if not (0.0 <= top_p <= 1.0):
            raise ValueError("[LLM Service]: 0.0 <= top_p <= 1.0")
        
        if not (-2.0 <= frequency_penalty <= 2.0):
            raise ValueError("[LLM Service]: -2.0 <= frequency_penalty <= 2.0")
        
        if not (-2.0 <= presence_penalty <= 2.0):
            raise ValueError("[LLM Service]: -2.0 <= presence_penalty <= 2.0")
        
        self.__model                = model
        self.__temperature          = temperature
        self.__top_p                = top_p
        self.__seed                 = seed
        self.__frequency_penalty    = frequency_penalty
        self.__presence_penalty     = presence_penalty
        self.__base_url             = base_url
        self.__input_price          = input_price
        self.__output_price         = output_price
        
        self.__client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
                
    def generate(self,
                 prompt: Union[str, List[Dict[str, Any]]],
                 system_prompt: Optional[str] = None,
                 response_format: dict = {"type": "text"}) -> LLMResponse:
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        kwargs = {
            "model": self.__model,
            "messages": messages,
            "temperature": self.__temperature,
            "top_p": self.__top_p,
            "response_format": response_format
        }
        
        is_google = "googleapis.com" in (self.__base_url or "")
        if not is_google:
            if self.__seed is not None:
                kwargs["seed"] = self.__seed
            if self.__frequency_penalty != 0.0:
                kwargs["frequency_penalty"] = self.__frequency_penalty
            if self.__presence_penalty != 0.0:
                kwargs["presence_penalty"] = self.__presence_penalty
        
        response = self.__client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content or ""
        
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        if hasattr(response, "usage") and response.usage:
            prompt_tokens = response.usage.prompt_tokens or 0
            completion_tokens = response.usage.completion_tokens or 0
            total_tokens = response.usage.total_tokens or (prompt_tokens + completion_tokens)
            
        # Custos baseados no valor por 1 milhão de tokens (1M tokens)
        input_cost = (prompt_tokens / 1_000_000.0) * self.__input_price
        output_cost = (completion_tokens / 1_000_000.0) * self.__output_price
        total_cost = input_cost + output_cost
        
        return LLMResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            input_cost_usd=round(input_cost, 6),
            output_cost_usd=round(output_cost, 6),
            total_cost_usd=round(total_cost, 6)
        )

    def send_prompt(self,
                    prompt: Union[str, List[Dict[str, Any]]],
                    system_prompt: Optional[str] = None,
                    response_format: dict = {"type": "text"}) -> str:
        result = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format=response_format
        )
        return result.content