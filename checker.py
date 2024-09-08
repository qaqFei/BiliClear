import re
import yaml
import unicodedata

from Levenshtein import ratio

class Checker:
    def __init__(self) -> None:
        with open("./res/rules.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.rules_exact: list[str | list[str]] = config.get("rules_exact", [])
        self.rules_elastic = config.get("rules_elastic", [])

    def normalize_text(self, text: str) -> str:
        "将文本转换为小写、简体中文和英文符号"
        text = text.lower()
        text = unicodedata.normalize("NFKC", text)
        text = text.replace("！", "!").replace("。", ".").replace("，", ",").replace("“", "\"").replace("”", "\"")
        return text

    def check_v1(self, text: str):
        "检查字符串"
        text = self.normalize_text(text)
        
        for item in self.rules_exact:
            if isinstance(item, list):
                if all([not re.search(keyword.lower(), text.replace("$-not ", "")) if text.startswith("$-not ") else re.search(keyword.lower(), text) for keyword in item]):
                    return True, str(item)
            elif isinstance(item, str):
                if re.search(item.lower(), text):
                    return True, item
            
        return False, ""

    def check_v2(self, text: str, threshold: float = 0.7):
        "检查字符串, 并根据匹配程度进行判断 threshold: 匹配程度阈值"
        text = self.normalize_text(text)
        match_scores = []
        
        for item in self.rules_exact:
            if isinstance(item, list):
                if all([not re.search(keyword.lower(), text.replace("$-not ", "")) if text.startswith("$-not ") else re.search(keyword.lower(), text) for keyword in item]):
                    match_scores.append(1.0)
            elif isinstance(item, str):
                matches = re.findall(item.lower(), text)
                score = len(matches) / len(text)
                match_scores.append(score)
        
        if match_scores:
            avg_score = sum(match_scores) / len(match_scores)
            return avg_score >= threshold, "规则匹配程度匹配"
        
        return False, ""
    
    def check_v3(self, text: str, threshold: float = 0.7):
        "检查字符串, 并根据相似程度进行判断 threshold: 相似程度阈值"
        text = self.normalize_text(text)
        match_scores = []
        
        for item in self.rules_elastic:
            if isinstance(item, str):
                similarity = ratio(item.lower(), text)
                match_scores.append(similarity)
        
        if match_scores:
            avg_score = sum(match_scores) / len(match_scores)
            return avg_score >= threshold, "规则相似程度匹配"
        
        return False, ""
    
    def check(self, text: str, threshold: float = 0.7):
        "使用使用方法检查字符串"
        checks: list[tuple[bool, str]] = [
            self.check_v1(text),
            self.check_v2(text, threshold),
            self.check_v3(text, threshold)
        ]
        for isp, r in checks:
            if isp:
                return True, r
        return False, ""