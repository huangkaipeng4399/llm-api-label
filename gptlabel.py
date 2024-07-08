#!/usr/bin/env python

import os
import re
import time
import json
import logging

from openai import OpenAI

from qwen2_access import QWen2
from gpt4_access import query_gpt4

logger = logging.getLogger()
logger.setLevel(logging.INFO)

with open("prompt.txt", "r") as f:
    prompt = f.read()


def gpt_api_func(model_name='gpt-4', **kwargs):
    text = eval(f'f"""{prompt}"""')
    if "client_name" in kwargs.keys() and kwargs["client_name"] == 'azure':
        resp_text = query_gpt4(kwargs["api_key"], kwargs["base_url"], text)
    elif "client_name" in kwargs.keys() and kwargs["client_name"] == 'qwen2':
        model = QWen2("101.230.144.204:17906")
        dialog=[
            {
                "role": "user",
                "content": text
            },
        ]
        resp_text = model.chat(dialog)
    else:
        messages = [
            {
                "role": "user",
                "content": text
            },
        ]
        completion = kwargs["gpt_client"].chat.completions.create(
            model=model_name,
            messages=messages,
            stream=False,
        )
        resp_text = completion.choices[0].message.content
    return resp_text


def parse_response(
    gpt_response='',
    pattern=r'{\s{0,5}"政治敏感":\s{0,5}\d+,\s{0,5}"色情":\s{0,5}\d+,\s{0,5}"有毒":\s{0,5}\d+,\s{0,5}"广告":\s{0,5}\d+\s{0,5}}'
):
    try:
        matches = re.findall(pattern, gpt_response)
        parse_dict = json.loads(matches[0])
        logging.info(f"parsed_dict:{parse_dict}")
    except Exception as e:
        logging.error(f"{e}")
        parse_dict = {'raw_response_text': gpt_response}
        logging.info(f"parsed_dict:{parse_dict}")

    return parse_dict


def relabel_text(input_file,
                 output_file,
                 start_idx=0,
                 model_name='gpt-4',
                 sleep_time=1,
                 **kwargs):
    logging.info(
        f"================Using model:{model_name}====================")
    logging.info(f"Reading file:{input_file}")
    cnt = 0
    with open(input_file) as f_in, open(output_file, 'a') as f_out:
        for line in f_in:
            cnt += 1
            if cnt <= start_idx:
                continue
            if not line.strip():
                continue
            logging.info(f"Processing line: {cnt}")
            line_dict = json.loads(line.strip())
            """
            请根据需要修改以下代码段，
            并在gpt_api_func中根据你的prompt内容调整要传递给prompt的参数。
            """
            #begin
            input_keywords = ",".join(line_dict["Keywords"])
            input_text = "\n".join(line_dict["contents"])[:2000]
            #end

            for _ in range(5):
                try:
                    time.sleep(0.2)
                    raw_response = gpt_api_func(model_name=model_name,
                                                input_keywords=input_keywords,
                                                input_text=input_text,
                                                **kwargs)
                    gpt_response = parse_response(raw_response,
                                                  r'{\s{0,5}"Political Sensitivity":\s{0,5}\d+,\s{0,5}"Porn":\s{0,5}\d+,\s{0,5}"Toxic":\s{0,5}\d+,\s{0,5}"Advertisement":\s{0,5}\d+\s{0,5}}')
                    break
                except Exception as e:
                    logging.error(e)
                    if 'Risk' in str(e) or 'risk' in str(e):
                        gpt_response = {"error_msg": str(e)}
                        break
                    elif any([
                            x in str(e) for x in [
                                'API', 'api', 'access', 'key', 'invalid',
                                'quota', 'uth'
                            ]
                    ]):
                        return cnt
                    else:
                        time.sleep(sleep_time)
                        continue
            line_dict.update(gpt_response)
            f_out.write(json.dumps(line_dict, ensure_ascii=False) + '\n')
    return -1


def get_file_list(input_dir):
    file_list = []
    print(input_dir)
    if os.path.isfile(input_dir):
        return [input_dir]
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list


def run_label(input_file_path, output_file, start_idx, sleep_time, config):
    file_list = get_file_list(input_file_path)
    cnt = start_idx
    print(file_list)
    for file_idx, file in enumerate(file_list):  #遍历所有的文件
        if os.path.isfile(file):
            for client_name in config.keys():  #遍历所有的apikey
                for apikey, valid in config[client_name]["api_keys"].items():
                    if valid == "False":
                        continue
                    if client_name == "openai":
                        gpt_client = OpenAI(api_key=apikey)
                    elif config[client_name] != "azure" or config[client_name] != "qwen2":
                        gpt_client = OpenAI(
                            api_key=apikey,
                            base_url=config[client_name]["base_url"],
                        )
                    kwargs = {}
                    if client_name == "azure":
                        kwargs["base_url"] = config[client_name]["base_url"]
                        kwargs["client_name"] = "azure"
                        kwargs["api_key"] = apikey
                    elif client_name == "qwen2":
                        kwargs["client_name"] = "qwen2"
                        kwargs["api_key"] = apikey
                    else:
                        kwargs["gpt_client"] = gpt_client
                    cnt = relabel_text(
                        file,
                        output_file,
                        start_idx=cnt,
                        model_name=config[client_name]["model_name"],
                        sleep_time=sleep_time,
                        **kwargs)
                    #正常返回-1.如果返回的是cnt，说明文件在处理到第cnt行时出现了问题。
                    if cnt == -1:
                        break
                    else:
                        if cnt > 0:
                            cnt -= 1
                        config[client_name]["api_keys"][apikey] = "False"
                        continue
                if cnt == -1:
                    break
        if file_idx != len(file_list) - 1:
            cnt = 0
    if cnt == -1:
        logging.info("The process is completed!")
    else:
        logging.error("Process failed! Please check the api_key!")
