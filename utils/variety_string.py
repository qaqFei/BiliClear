from typing import SupportsIndex
from typing import Sequence, TypeVar

variety = [
    'AaＡａ', 'BbＢｂ', 'CcＣｃ', 'DdＤｄ', 'EeＥｅ', 'FfＦｆ', 'GgＧｇ', 'HhＨｈ',
    'IiＩｉ', 'JjＪｊ', 'KkＫｋ', 'LlＬｌ', 'MmＭｍ', 'NnＮｎ', 'OoＯｏ', 'PpＰｐ',
    'QqＱｑ', 'RrＲｒ', 'SsＳｓ', 'TtＴｔ', 'UuＵｕ', ['V', 'v', 'Ｖ', 'ｖ', '\/'],
    ['W', 'w', 'Ｗ', 'ｗ', 'VV'], 'XxＸｘ', 'YyＹｙ', 'ZzＺｚ', '0Oo００ｏ', '1１',
    '2２', '3３', '4４', '5５', '6６', '7７', '8８', '9９', ['掃', '扫', 'SA0'], '!！', 
    '[【', ']】', ',，'
]

def convert(original: str) -> str:
    for strings in variety:
        for char in strings:
            original = original.replace(char, strings[0])
    return original

class VarietyString(str):
    """复杂变体的识别，例如“Ｓａo 码”"""
    def __eq__(self, other: str):
        return convert(self) == convert(other)
    
    def startswith(self, prefix: str | tuple[str, ...], start: SupportsIndex | None = None, end: SupportsIndex | None = None) -> bool:
        return convert(self).startswith(convert(prefix), start, end)

    def removeprefix(self, prefix: str) -> str:
        return convert(self).removeprefix(convert(prefix))
    
    def removesuffix(self, suffix: str) -> str:
        return convert(self).removesuffix(convert(suffix))

    def count(self, x: str, start: SupportsIndex | None = None, end: SupportsIndex | None = None) -> int:
        return convert(self).count(convert(x), start, end)
    
    def __contains__(self, key: str) -> bool:
        return convert(key) in convert(self)

def test():
    import unittest

    class VarietyStringTest(unittest.TestCase):
        def test_equal(self):
            self.assertEqual(VarietyString('aAaＡａ'), 'AaａＡa')
            self.assertNotEqual(VarietyString('aAaＡａ'), 'aAaＡａａ')
            self.assertEqual(VarietyString('掃扫'), 'ＳaosａO')
            self.assertNotEqual(VarietyString('BbＢｂ'), 'BｃＢｂ')
        
        def test_startswith(self):
            self.assertTrue(VarietyString('Aａa掃Ａ').startswith('ＡAａsao'))
            self.assertFalse(VarietyString('Aａa掃Ａ').startswith('ＡAｂsao'))
        
        def test_removeprefix(self):
            self.assertEqual(VarietyString('A掃aＡａ').removeprefix('ａsao'), 'AAA')
            self.assertEqual(VarietyString('A掃aＡａ').removeprefix('Ｓsao'), 'A掃AAA')

    # 运行测试
    unittest.main(VarietyStringTest())

if __name__ == '__main__':
    test()
