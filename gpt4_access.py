# gpt4调用接口
import os
import requests
import base64


def query_gpt4(GPT4_KEY, GPT4_ENDPOINT, content):
    headers = {
        "Content-Type": "application/json",
        "api-key": GPT4_KEY,
    }
    payload = {
        "messages": [{
            "role": "user",
            "content": [{
                "type": "text",
                "text": f"{content}"
            }]
        }],
        "temperature":
        0.7,
        "top_p":
        0.95,
        "max_tokens":
        800
    }
    try:
        response = requests.post(GPT4_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status(
        )  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.RequestException as e:
        raise Exception(f"Failed to make the request. Error: {e}")
    return response.json()["choices"][0]["message"]["content"]

if __name__ == '__main__':
    print(query_gpt4("1b31a3085ad744d0bfb5fe0c0407edb6", "https://mtc2023.openai.azure.com/openai/deployments/GPT4-0409-PTU/chat/completions?api-version=2024-02-15-preview", "你好"))