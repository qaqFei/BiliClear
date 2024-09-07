import openai
import requests
import datetime

gpt_model = "gpt-4o-mini"


def get_today_gpt_usage(api_key):
    """获取当天的 GPT tokens 使用量"""
    headers = {
        'Authorization': f'Bearer {api_key}',
    }

    # 获取当前日期的开始时间 (UTC)
    today = datetime.datetime.utcnow().date()
    start_time = f"{today}T00:00:00Z"
    end_time = f"{today}T23:59:59Z"

    url = f"https://api.openai.com/v1/usage?start={start_time}&end={end_time}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("total_tokens", 0)
        else:
            print(f"Error: Unable to retrieve GPT usage, Status code: {response.status_code}")
            return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 0


def _gpt_replay(content, prompt) -> str:
    return openai.ChatCompletion.create(
        model=gpt_model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ]
    )["choices"][0]["message"]["content"]


def _pcs_gpt_result(result: str):
    return "true" in result.lower()


def gpt_porn(content):
    return _pcs_gpt_result(_gpt_replay(
        f"Does the following text contain any adult or explicit content?\n\nText: {content}\n\nAnswer with True or False.",
        "You are a content safety assistant."
    ))


def gpt_ad(content, need_at=True):
    if need_at:
        return _pcs_gpt_result(_gpt_replay(
            f"Does the following text contain any promotional or advertisement content, including content that attempts to redirect users to websites, homepages, or encourages watching videos?\n\nText: {content}\n\nAnswer with True or False.",
            "You are a content safety assistant."
        )) if "@" in content else False
    else:
        return _pcs_gpt_result(_gpt_replay(
            f"Does the following text contain any promotional or advertisement content?\n\nText: {content}\n\nAnswer with True or False.",
            "You are a content safety assistant."
        ))
