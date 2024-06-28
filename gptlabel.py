#!/usr/bin/env python

import os
import re
import time
import json
import logging

from openai import OpenAI

from gpt4access import query_gpt4

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def gpt_api_func(input_keywords, input_text, model_name='gpt-4', **kwargs):
    text = f"""
你是一个数据清洗人员，需要你要筛选出有问题的文档。请对输入的文档主题词和示例文本内容进行检查。需要检查的维度包括：
政治敏感：危害国家统一、主权和领土完整,违背宪法确认的根本制度,反对中国共产党的领导,对中国政府或国家利益有影响的言论或信息。宣扬恐怖主义、极端主义思想,包括但不限于颂扬、鼓吹、教唆恐怖活动,宣传极端宗教理念,传播暴力血腥内容等。
色情：传播淫秽色情信息。
有毒：包含种族、民族、性别、宗教等歧视性言论,传播仇恨、偏激思想,使用攻击性、贬低性语言。宣扬暴力、残暴行为,如虐待、伤害他人,破坏公共秩序等。
广告：属于广告营销内容，即具有明确的商业目的，旨在促使他人采取某种行动，如购买产品、服务或参与活动等。
请根据以下条件进行检查：
1.主题词是否含有相应内容。
2.示例文本是否在谈论这些内容。
如果文本主题词和内容满足上述条件，请对相应维度返回"1"，否则返回"0"。
输出格式示例(必须按照这个格式输出,否则无法解析，不要返回任何额外的内容):
{{
"政治敏感": 1,
"色情": 1,
"有毒": 0,
"广告": 0
}}

文档主题词：{input_keywords}
示例文本内容：{input_text}
"""
    if "client_name" in kwargs.keys() and kwargs["client_name"] == 'azure':
        resp_text = query_gpt4(kwargs["api_key"], kwargs["base_url"], text)
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


def parse_response(gpt_response=''):
    try:
        pattern = r'{\s{0,5}"政治敏感":\s{0,5}\d+,\s{0,5}"色情":\s{0,5}\d+,\s{0,5}"有毒":\s{0,5}\d+,\s{0,5}"广告":\s{0,5}\d+\s{0,5}}'
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
            input_keywords = ",".join(line_dict["Keywords"])
            texts = []
            for i in range(min(len(line_dict["documents"]), 5)):
                #限定输入文本长度
                texts.append(line_dict["documents"][i][:500])
            input_text = "\n".join(texts)
            for _ in range(5):
                try:
                    time.sleep(0.2)
                    raw_response = gpt_api_func(input_keywords,
                                                input_text,
                                                model_name=model_name,
                                                **kwargs)
                    gpt_response = parse_response(raw_response)
                    break
                except Exception as e:
                    logging.error(e)
                    if 'Risk' in str(e) or 'risk' in str(e):
                        gpt_response = {"error_msg": str(e)}
                        break
                    elif any([
                            x in str(e) for x in
                        ['API', 'api', 'access', 'key', 'invalid', 'quota']
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
    if os.path.isfile(input_dir):
        return [input_dir]
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list


def run_label(input_file_path, output_file, start_idx, sleep_time, config):
    file_list = get_file_list(input_file_path)
    cnt = start_idx
    for file_idx, file in enumerate(file_list):  #遍历所有的文件
        if os.path.isfile(file):
            for client_name in config.keys():  #遍历所有的apikey
                for apikey, valid in config[client_name]["api_keys"].items():
                    if valid == "False":
                        continue
                    if client_name == "openai":
                        gpt_client = OpenAI(api_key=apikey)
                    elif config[client_name] != "azure":
                        gpt_client = OpenAI(
                            api_key=apikey,
                            base_url=config[client_name]["base_url"],
                        )
                    kwargs = {}
                    if client_name == "azure":
                        kwargs["base_url"] = config[client_name]["base_url"]
                        kwargs["client_name"] = "azure"
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
            if file_idx != len(file_list) - 1:
                cnt = 0
    if cnt == -1:
        logging.info("The process is completed!")
    else:
        logging.error("Process failed! Please check the api_key!")
