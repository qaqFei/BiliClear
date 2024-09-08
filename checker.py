import re
import yaml
import unicodedata
from Levenshtein import ratio

class Checker:
    def __init__(self) -> None:
        """
        初始化 Checker 类，读取 YAML 配置文件并加载违禁词列表。
        """
        with open("res/curse.yaml", 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        self.words = config.get("curse_words", [])
        self.words_v2 = config.get("curse_words_v2", [])

    def normalize_text(self, text: str) -> str:
        """
        将文本转换为小写、简体中文和英文符号。
        
        :param text: 待转换的字符串
        :return: 转换后的字符串
        """
        # 转换为小写
        text = text.lower()
        # 转换为简体中文
        text = unicodedata.normalize('NFKC', text)
        # 替换英文符号
        text = text.replace('！', '!').replace('。', '.').replace('，', ',').replace('“', '"').replace('”', '"')
        return text

    def V1(self, text: str) -> bool:
        """
        检查字符串中是否包含违禁词或匹配正则表达式。
        
        :param text: 待检查的字符串
        :return: 如果包含违禁词或匹配正则表达式，则返回 True；否则返回 False
        """
        # 规范化文本
        text = self.normalize_text(text)
        
        for item in self.words:
            if isinstance(item, list):
                all_match = all(re.search(keyword.lower(), text) for keyword in item)
                if all_match:
                    return True
            elif isinstance(item, str):
                if re.search(item.lower(), text):
                    return True
            
        return False

    def V2(self, text: str, threshold: float = 0.7) -> bool:
        """
        检查字符串中是否包含违禁词或匹配正则表达式，并根据匹配程度进行判断。
        
        :param text: 待检查的字符串
        :param threshold: 匹配程度阈值，默认为 0.7
        :return: 如果匹配程度大于等于阈值，则返回 True；否则返回 False
        """
        # 规范化文本
        text = self.normalize_text(text)
        
        match_scores = []
        
        for item in self.words:
            if isinstance(item, list):
                all_match = all(re.search(keyword.lower(), text) for keyword in item)
                if all_match:
                    match_scores.append(1.0)
            elif isinstance(item, str):
                matches = re.findall(item.lower(), text)
                score = len(matches) / len(text)
                match_scores.append(score)
        
        if match_scores:
            avg_score = sum(match_scores) / len(match_scores)
            return avg_score >= threshold
        
        return False
    
    def V3(self, text: str, threshold: float = 0.7) -> bool:
        """
        检查字符串中是否包含违禁词，并根据相似程度进行判断。
        
        :param text: 待检查的字符串
        :param threshold: 相似程度阈值，默认为 0.7
        :return: 如果相似程度大于等于阈值，则返回 True；否则返回 False
        """
        # 规范化文本
        text = self.normalize_text(text)
        
        match_scores = []
        
        for item in self.words_v2:
            if isinstance(item, str):
                similarity = ratio(item.lower(), text)
                match_scores.append(similarity)
        
        if match_scores:
            avg_score = sum(match_scores) / len(match_scores)
            return avg_score >= threshold
        
        return False