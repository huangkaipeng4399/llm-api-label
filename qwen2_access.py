from transformers import AutoTokenizer
import requests
import json


class QWen2:
    def __init__(self, api, parameters=None):
        self.url = f"http://{api}/generate"
        if parameters:
            self.parameters = parameters
        else:
            self.parameters = {
                'max_new_tokens': 1024,
                'do_sample': False
            }
        self.tokenizer = AutoTokenizer.from_pretrained("./qwen-2-instruct")
        
    def process_messages(self, messages):
        new_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                new_messages.append(msg)
            elif msg['role'] == 'user':
                new_messages.append(msg)
            elif msg['role'] == 'assistant':
                if 'tool_calls' in msg:
                    tool_calls_text = json.dumps(msg['tool_calls'][0]['function'], ensure_ascii=False)
                    msg['content'] = tool_calls_text
                new_messages.append(msg)
            elif msg['role'] == 'function' or msg['role'] == 'tool':
                msg['role'] = 'assistant'
                new_messages.append(msg)
                messages = new_messages
                
        merged_messages = []
        current_message = messages[0]
        for message in messages[1:]:
            if message["role"] == current_message["role"]:
                current_message["content"] += " " + message["content"]
            else:
                merged_messages.append(current_message)
                current_message = message
        merged_messages.append(current_message)
        return merged_messages
    
    def decode_response(self, raw_resp):
        toolcalls = raw_resp.split("\n")
        
        tool_calls = []
        for tc in toolcalls:
            try:
                tc = json.loads(tc)
                tool_calls.append(tc)
            except:
                continue
        if tool_calls == []:
            decoded_resp = {
                "content": raw_resp
            }
        else:
            decoded_resp = {
                "tool_calls": tool_calls
            }
        return decoded_resp
     
    def chat(self, messages=[]):
        messages = self.process_messages(messages)

        dialog_prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        headers = {'Content-Type': 'application/json'}
        input_data =  {"inputs": dialog_prompt,"parameters": self.parameters}
        
        raw_response = requests.post(self.url, headers=headers, json=input_data, stream=False)
        raw_response = raw_response.json()
        content = raw_response['generated_text'][0]
        # decoded_resp = self.decode_response(content)
        # return decoded_resp
        return content


SYSTEM_PROMPT_FOR_CHAT_MODEL = """
    You are an expert in composing functions. You are given a question and a set of possible functions. 
    Based on the question, you will need to make one or more function/tool calls to achieve the purpose. 
    If none of the function can be used, point it out. If the given question lacks the parameters required by the function,
    also point it out. You should only return the function call in tools call sections.\n
    
    Here is a list of functions in JSON format that you can invoke:\n[FUNCTIONS_TO_REPLACE]. 
    Should you decide to return the function call(s),Put it in the JSON format of {"name": function_name1, "arguments": { "args1": value1, "args2": value2, ...}}\n{"name": function_name2, "arguments": { "args1": value1, "args2": value2, ...}}\n
    """


if __name__ == "__main__":
    dialog = [
        {
            "role": "user",
            "content": "我要吃红色的菜"
        },        
    ]
    
    model = QWen2("101.230.144.204:17906")
    response = model.chat(messages=dialog)
    print(response)