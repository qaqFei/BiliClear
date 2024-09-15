import openai
import openai.error
import datetime
import json
import os

gpt_model = "gpt-4o-mini"
RateLimitError = openai.error.RateLimitError
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
            {"role": "user", "content": content},
        ],
    )
    tokens_used = response["usage"]["total_tokens"]

    # 记录 token 使用量
    record_token_usage(tokens_used)

    return response["choices"][0]["message"]["content"]


def _pcs_gpt_result(result: str):
    return "true" in result.lower()


def gpt_porn(content):
    return _pcs_gpt_result(
        _gpt_replay(
            content,
            "You are a content safety assistant, Does the following text contain any adult or explicit content? Answer with True or False.",
        )
    )


def gpt_ad(content, need_at=False):
    if need_at:
        return (
            _pcs_gpt_result(
                _gpt_replay(
                    content,
                    "You are a content safety assistant. Does the following text contain any promotional, advertisement, or fraudulent content? This includes, but is not limited to, any content that attempts to solicit money or financial contributions (such as donation requests, crowdfunding campaigns, investment opportunities, or scams), redirect users to websites, promote products or services, or encourage watching videos for monetary gain. Casual mentions asking someone to watch a video (e.g., '@X come watch this') should not be considered promotional or advertisement content. Answer with True or False.",
                )
            )
            if "@" in content
            else False
        )
    else:
        return _pcs_gpt_result(
            _gpt_replay(
                content,
                "You are a content safety assistant. Does the following text contain any promotional, advertisement, or fraudulent content? This includes, but is not limited to, any content that attempts to solicit money or financial contributions (such as donation requests, crowdfunding campaigns, investment opportunities, or scams), redirect users to websites, promote products or services, or encourage watching videos for monetary gain. Casual mentions asking someone to watch a video (e.g., '@X come watch this') should not be considered promotional or advertisement content. Answer with True or False.",
            )
        )


if __name__ == "__main__":
    print(
        gpt_ad(
            "我的女儿被确诊为恶性肿瘤，一直在医院进行治疗 ,前期的治疗费用都是从五亲六戚和朋友中借款筹备治疗的 ,现在已经欠下了重重债务，无法承担这样的大病医.疗费用 ，还有后期的化疗治疗更加昂贵的医药费用 ，现在因癌症治疗，无法支付后期巨额医疗费用，实在无法延续生命，希望大家可以伸出援助之手帮帮我们 ，谢谢大家🙏"
        )
    )
    usage_today = get_today_gpt_usage()
    print(f"Today's GPT usage: {usage_today} tokens")
