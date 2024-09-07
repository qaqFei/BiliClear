import openai


def _gpt_replay(apikey, content, prompt):
    openai.api_key = apikey

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ]
    )

    return response['choices'][0]['message']['content'].strip().lower()


def gpt_porn(content, apikey):
    return "true" in _gpt_replay(apikey,
                                 f"Does the following text contain any adult or explicit content?\n\nText: {content}\n"
                                 f"\nAnswer with True or False.",
                                 "You are a content safety assistant.")


def gpt_ad(content, apikey, need_at=True):
    if need_at:
        if "@" in content or "@" in content:
            return "true" in _gpt_replay(apikey,
                                         f"Does the following text contain any promotional or advertisement content, "
                                         f"including content that attempts to redirect users to websites, homepages, or encourages watching videos?\n\nText: {content}\n\nAnswer with True or False.",
                                         "You are a content safety assistant.")
        else:
            return False

    else:

        return "true" in _gpt_replay(apikey,
                                     f"Does the following text contain any promotional or advertisement "
                                     f"content?\n\nText: {content}\n\nAnswer with True or False.",
                                     "You are a content safety assistant.")


