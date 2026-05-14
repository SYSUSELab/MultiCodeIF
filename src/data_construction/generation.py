from openai import OpenAI
import concurrent.futures
from tenacity import retry, wait_random_exponential, stop_after_attempt

class LLM():
    def __init__(
        self, 
        api_keys : list,
        model_name : str
    ):
        if not api_keys or not any(api_key and api_key.strip() and api_key != "sk-" for api_key in api_keys):
            raise ValueError("API keys are invalid or empty, please configure a valid API key")
        self.clients = [OpenAI(api_key=api_key, base_url = "") for api_key in api_keys if api_key and api_key.strip() and api_key != "sk-"]
        if not self.clients:
            raise ValueError("No valid API key client")
        self.model_name = model_name

    def generation_in_parallel(self, prompts):
        results = [None] * len(prompts)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.clients)) as executor:
            future_to_index = {executor.submit(self.generation, prompt, self.clients[i % len(self.clients)]): i for i, prompt in enumerate(prompts)}
            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    data = future.result()
                    results[index] = (prompts[index], data)
                except Exception as exc:
                    import traceback
                    error_detail = traceback.format_exc()
                    results[index] = (prompts[index], f"Request generated an exception: {exc}\nDetailed error information:\n{error_detail}")
    
        return results
    
    @retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(6))
    def generation(self, content, client, temperature=0.3):
        try:
            response = client.chat.completions.create(
                model=self.model_name, 
                messages=[
                    {
                        "role": "user", 
                        "content": content
                    }
                ],
                temperature=temperature
            )
            if not response:
                raise ValueError("API returned an empty response")
            
            if hasattr(response, 'error') and response.error:
                error_info = response.error
                error_code = error_info.get('code', 'unknown') if isinstance(error_info, dict) else getattr(error_info, 'code', 'unknown')
                error_message = error_info.get('message', 'Unknown error') if isinstance(error_info, dict) else getattr(error_info, 'message', 'Unknown error')
                raise ValueError(f"API returned error [{error_code}]: {error_message}")
            
            if not hasattr(response, 'choices') or not response.choices:
                raise ValueError(f"No 'choices' field in API response, response content: {response}")
            if len(response.choices) == 0:
                raise ValueError("API response 'choices' is empty")
            if not hasattr(response.choices[0], 'message') or not response.choices[0].message:
                raise ValueError(f"Missing 'message' field in API response, response content: {response.choices[0]}")
            if not hasattr(response.choices[0].message, 'content'):
                raise ValueError(f"Missing 'content' field in API response, response content: {response.choices[0].message}")
            
            content_text = response.choices[0].message.content
            if content_text:
                return content_text
            else:
                raise ValueError("API returned empty content")
        except Exception as e:
            error_msg = f"API call failed: {str(e)}"
            if hasattr(e, 'response') and e.response:
                error_msg += f"\nAPI response status code: {getattr(e.response, 'status_code', 'N/A')}"
                try:
                    error_msg += f"\nAPI response content: {e.response.text if hasattr(e.response, 'text') else str(e.response)}"
                except:
                    pass
            raise Exception(error_msg) from e


api_keys = [""]


def generation_in_parallel(prompts, model_name):
    if isinstance(prompts, str):
        prompts = [prompts]
    
    llm = LLM(api_keys, model_name)
    return llm.generation_in_parallel(prompts)


if __name__ == "__main__":
    prompts = ["Hello, how are you?"]
    model_name = "gpt-5.2"
    print(generation_in_parallel(prompts, model_name))