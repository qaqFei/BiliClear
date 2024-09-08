import time

import openai
import openai.error
import requests
import datetime

gpt_model = "gpt-4o-mini"
RateLimitError = openai.error.RateLimitError

import requests
import datetime
import openai


def get_today_gpt_usage():
    # 获取当前时间（UTC）
    datetime_now = datetime.datetime.utcnow()
    today = f"{datetime_now.year}-{datetime_now.month:02d}-{datetime_now.day:02d}"
    start_time = f"{today}T00:00:00Z"
    end_time = f"{today}T23:59:59Z"

    # 定义API请求的URL和头信息
    url = f"https://api.openai.com/v1/usage?start={start_time}&end={end_time}"
    headers = {
        "Authorization": f"Bearer {openai.api_key}",
    }

    try:
        # 发起GET请求获取当日使用情况
        response = requests.get(url, headers=headers)

        # 检查请求是否成功
        if response.status_code == 200:
            data = response.json()
            # 获取已使用的token数量
            return data.get("total_tokens", 0)
        else:
            # 输出状态码错误信息
            print(f"Error: Unable to retrieve GPT usage, Status code: {response.status_code}")
            return 0
    except Exception as e:
        # 捕获任何异常并输出错误信息
        print(f"Get today GPT usage error: {str(e)}")
        return 0


def _gpt_replay(content, prompt) -> str:
    # print(openai.ChatCompletion.create(
    #     model = gpt_model,
    #     messages = [
    #         {"role": "system", "content": prompt},
    #         {"role": "user", "content": content}
    #     ]
    # )["choices"][0]["message"]["content"])
    # time.sleep(3)
    return openai.ChatCompletion.create(
        model = gpt_model,
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ]
    )["choices"][0]["message"]["content"]

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
