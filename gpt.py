import openai
import openai.error
import datetime
import json
import os

gpt_model = "gpt-4o-mini"
RateLimitError = openai.RateLimitError
usage_file = "gpt_usage.json"


# 初始化或者加载记录
def load_usage_data():
    if os.path.exists(usage_file):
        with open(usage_file, "r") as file:
            return json.load(file)
    else:
        return {}


# 保存记录到文件
def save_usage_data(data):
    with open(usage_file, "w") as file:
        json.dump(data, file, indent=4)


# 获取当天日期字符串
def get_today_date():
    return datetime.datetime.now().strftime("%Y-%m-%d")


# 获取今日的 GPT 使用量，从日志文件中加载
def get_today_gpt_usage():
    usage_data = load_usage_data()
    today = get_today_date()
    return usage_data.get(today, 0)


# 记录使用的 token 数量
def record_token_usage(tokens_used):
    usage_data = load_usage_data()
    today = get_today_date()

    # 如果是新的一天，重置当天的使用量
    if today not in usage_data:
        usage_data[today] = 0

    # 累加当天的 token 使用量
    usage_data[today] += tokens_used

    # 保存数据到文件
    save_usage_data(usage_data)


# GPT 交互并记录使用量
def _gpt_replay(content, prompt) -> str:
    response = openai.ChatCompletion.create(
        model=gpt_model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ]
    )
    tokens_used = response['usage']['total_tokens']

    # 记录 token 使用量
    record_token_usage(tokens_used)

    return response["choices"][0]["message"]["content"]


def _pcs_gpt_result(result: str):
    return "true" in result.lower()


def gpt_porn(content):
    return _pcs_gpt_result(_gpt_replay(
        content,
        "You are a content safety assistant, Does the following text contain any adult or explicit content? Answer with True or False."
    ))


def gpt_ad(content, need_at=True):
    if need_at:
        return _pcs_gpt_result(_gpt_replay(
            content,
            "You are a content safety assistant, Does the following text contain any promotional, advertisement, or fraudulent content, including content that attempts to redirect users to websites, homepages, solicit money (such as false donation requests or scams), or encourages watching videos? Casual mentions asking someone to watch a video (e.g., '@X come watch this') should not be considered as promotional or advertisement content. Answer with True or False."
        )) if "@" in content else False
    else:
        return _pcs_gpt_result(_gpt_replay(
            content,
            "You are a content safety assistant, Does the following text contain any promotional, advertisement, or fraudulent content, including content that attempts to redirect users to websites, homepages, solicit money (such as false donation requests or scams), or encourages watching videos? Casual mentions asking someone to watch a video (e.g., '@X come watch this') should not be considered as promotional or advertisement content. Answer with True or False."
        ))


if __name__ == "__main__":
    # 示例调用：打印今天的 GPT 使用量
    usage_today = get_today_gpt_usage()
    print(f"Today's GPT usage: {usage_today} tokens")

    # 您可以根据需要在此调用 gpt_porn 或 gpt_ad 函数测试 GPT 功能
