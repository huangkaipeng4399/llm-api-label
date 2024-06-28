# Label Clusters By GPT



这个repo用于使用llm接口批量标定文本属性，可以支持多文件输入以及添加多个可用的api-key。

## Get Started
在run.sh里面添加自己的输入文件和输出文件。输入文件可以是单个jsonl文件也可以是一个文件夹。

在config.json中添加你要使用的api-key及其对应信息。

具体的细节需要根据具体需求在gptlabel.py中调整所使用的prompt、所用到的正则匹配式等等。

## Run the code
运行前，将你的输入文件路径和你希望的输出文件路径添加到run.sh脚本中，并将你的api-keys按照使用规则添加到config.yaml中。
### 使用规则：
```yaml
azure:
  api_keys:
    xxxxx: 'True'       #在这里添加你的api-keys
  base_url: https://mtc2023.openai.azure.com/openai/deployments/GPT4-0409-PTU/chat/completions?api-version=2024-02-15-preview   #与官方文档相同
  model_name: gpt-4     #与官方文档相同
deepseek:
  api_keys:
    xxxxx: 'True'  
    xxxxx: 'True'
  base_url: https://api.deepseek.com
  model_name: deepseek-chat
openai:
  api_keys:
    xxxxx: 'True'   
  base_url: ''          #如果直接使用openai的接口，则不需要base_url
  model_name: gpt-4
```
上述配置完成后，你需要安装必须的扩展包，然后运行以下命令来启动你的任务。
```
bash run.sh
```