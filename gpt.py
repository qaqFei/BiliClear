import openai
import openai.error

gpt_model = "gpt-4o-mini"
RateLimitError = openai.error.RateLimitError

def _gpt_replay(content, prompt) -> str:
    response = openai.ChatCompletion.create(
        model = gpt_model,
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ]
    )
    
    return response["choices"][0]["message"]["content"]

def _pcs_gpt_result(result: str):
    return "true" in result.lower()

def gpt_porn(content):
    return _pcs_gpt_result(_gpt_replay(
        content,
        "You are a content safety assistant, Does the following text contain any adult or explicit content? Answer with True or False."
    ))

def gpt_ad(content, need_at=False):
    if need_at:
        return _pcs_gpt_result(_gpt_replay(
            content,
            "You are a content safety assistant. Does the following text contain any promotional, advertisement, or fraudulent content? This includes, but is not limited to, any content that attempts to solicit money or financial contributions (such as donation requests, crowdfunding campaigns, investment opportunities, or scams), redirect users to websites, promote products or services, or encourage watching videos for monetary gain. Casual mentions asking someone to watch a video (e.g., '@X come watch this') should not be considered promotional or advertisement content. Answer with True or False."
        )) if "@" in content else False
    else:
        return _pcs_gpt_result(_gpt_replay(
            content,
            "You are a content safety assistant. Does the following text contain any promotional, advertisement, or fraudulent content? This includes, but is not limited to, any content that attempts to solicit money or financial contributions (such as donation requests, crowdfunding campaigns, investment opportunities, or scams), redirect users to websites, promote products or services, or encourage watching videos for monetary gain. Casual mentions asking someone to watch a video (e.g., '@X come watch this') should not be considered promotional or advertisement content. Answer with True or False."
        ))