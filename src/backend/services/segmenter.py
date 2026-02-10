import re
from typing import List, Optional, Dict, Any, Tuple
from ..models import SegmentedWord, VerbMaster, VerbConjugation

class JapaneseSegmenter:
    """日文自动分词器"""
    
    # 标点符号列表（将被忽略）
    PUNCTUATIONS = {
        '。', '．', '、', '，', '？', '！', '「', '」', '"', '"', ''', ''',
        '（', '）', '［', '］', '｛', '｝', '【', '】', '《', '》',
        '：', '；', '…', '‥', '―', 'ー', '・', '．', '／', '～'
    }
    
    # 常用助词列表
    PARTICLES = {
        'は', 'が', 'を', 'に', 'で', 'へ', 'と', 'から', 'まで', 'より',
        'も', 'や', 'か', 'ね', 'よ', 'わ', 'ぞ', 'ぜ', 'な', 'さ',
        'けれど', 'けど', 'ので', 'のに', 'ように', 'ような'
    }
    
    # 常见助动词
    AUX_VERBS = {
        'です', 'ます', 'たい', 'たがる', 'らしい', 'そうだ', 'ようだ',
        'だ', 'である', 'でした', 'でしょう', 'ました', 'ません',
        'た', 'なかった', 'て', 'で', 'ながら', 'ば', 'なら', 'のに'
    }
    
    # 常用代词
    PRONOUNS = {
        '私', 'わたし', '僕', 'ぼく', '俺', 'おれ', 'あたし',
        'あなた', '君', 'きみ', 'お前', 'おまえ',
        '彼', 'かれ', '彼女', 'かのじょ',
        '私たち', 'わたしたち', '僕たち', 'ぼくたち',
        'あなたたち', '彼ら', 'かれら', '彼女ら', 'かのじょら',
        'これ', 'それ', 'あれ', 'どれ',
        'この', 'その', 'あの', 'どの',
        'ここ', 'そこ', 'あそこ', 'どこ'
    }
    
    # 常见副词
    ADVERBS = {
        'とても', 'たいへん', 'すごく', '非常に',
        'あまり', 'あんまり', '全然', 'ぜんぜん',
        '少し', 'すこし', 'ちょっと', '少々', 'しょうしょう',
        'もっと', 'もう少し', 'いつも', '常に', 'つねに',
        '時々', 'ときどき', 'たまに', '再び', 'ふたたび',
        '一緒に', 'いっしょに', '単に', 'たんに',
        '特に', 'とくに', '主に', 'おもに', '大体', 'だいたい'
    }
    
    def __init__(self):
        self.verb_conjugator = VerbConjugator()
    
    def segment(self, text: str, hiragana: str) -> List[SegmentedWord]:
        """
        分词主函数
        
        Args:
            text: 原文
            hiragana: 平假名注音
            
        Returns:
            分词结果列表
        """
        words = []
        position = 0
        remaining_text = text
        remaining_hira = hiragana
        
        while remaining_text:
            # 跳过标点符号
            if remaining_text[0] in self.PUNCTUATIONS:
                remaining_text = remaining_text[1:]
                if remaining_hira:
                    remaining_hira = remaining_hira[1:]
                continue
            
            word, word_type, word_hira, consumed = self._match_word(
                remaining_text, remaining_hira
            )
            
            if word:
                grammar_info = self._get_grammar_info(word, word_type, word_hira)
                
                seg_word = SegmentedWord(
                    raw_entry_id=0,  # 稍后设置
                    word_jp=word,
                    hiragana=word_hira,
                    word_type=word_type,
                    position=position,
                    grammar_info=grammar_info,
                    verb_id=None
                )
                
                # 如果是动词，识别原型
                if word_type == 'verb':
                    verb_info = self._detect_verb(word, word_hira)
                    if verb_info:
                        seg_word.grammar_info.update(verb_info)
                
                words.append(seg_word)
                position += 1
            
            remaining_text = remaining_text[consumed:]
            remaining_hira = remaining_hira[len(word_hira):]
        
        return words
    
    def _match_word(self, text: str, hiragana: str) -> Tuple[Optional[str], str, str, int]:
        """
        匹配一个单词
        
        Returns:
            (word, word_type, word_hiragana, consumed_chars)
        """
        # 1. 优先匹配助动词（通常较长）
        for aux in sorted(self.AUX_VERBS, key=len, reverse=True):
            if text.startswith(aux):
                return aux, 'aux_verb', self._get_hiragana(text[:len(aux)], hiragana), len(aux)
        
        # 2. 匹配助词
        for particle in sorted(self.PARTICLES, key=len, reverse=True):
            if text.startswith(particle):
                return particle, 'particle', self._get_hiragana(text[:len(particle)], hiragana), len(particle)
        
        # 3. 匹配副词
        for adv in sorted(self.ADVERBS, key=len, reverse=True):
            if text.startswith(adv):
                return adv, 'adverb', self._get_hiragana(text[:len(adv)], hiragana), len(adv)
        
        # 4. 匹配代词
        for pronoun in sorted(self.PRONOUNS, key=len, reverse=True):
            if text.startswith(pronoun):
                return pronoun, 'pronoun', self._get_hiragana(text[:len(pronoun)], hiragana), len(pronoun)
        
        # 5. 匹配动词（通过变形特征）
        verb_match = self._match_verb(text, hiragana)
        if verb_match:
            return verb_match
        
        # 6. 匹配形容词（い结尾或な结尾）
        adj_match = self._match_adjective(text, hiragana)
        if adj_match:
            return adj_match
        
        # 7. 默认按2-4字符分割名词
        return self._split_noun(text, hiragana)
    
    def _get_hiragana(self, word: str, full_hiragana: str) -> str:
        """从完整平假名中提取对应部分的读音"""
        # 简化处理：假设原文和假名长度对应
        return full_hiragana[:len(word)]
    
    def _match_verb(self, text: str, hiragana: str) -> Optional[Tuple]:
        """匹配动词"""
        # 检查常见动词变形后缀
        verb_endings = [
            ('ます', 'verb'), ('ました', 'verb'), ('ません', 'verb'),
            ('て', 'verb'), ('で', 'verb'), ('た', 'verb'), ('だ', 'verb'),
            ('ない', 'verb'), ('なかった', 'verb'),
            ('れる', 'verb'), ('られる', 'verb'), ('せる', 'verb'), ('させる', 'verb'),
            ('よう', 'verb'), ('ましょう', 'verb'),
        ]
        
        # 尝试匹配包含变形后缀的词
        for ending, word_type in verb_endings:
            if ending in text[:6]:  # 限制搜索长度
                # 找到词干（简化处理）
                idx = text.find(ending)
                if idx > 0:
                    word = text[:idx+len(ending)]
                    return word, word_type, hiragana[:len(word)], len(word)
        
        return None
    
    def _match_adjective(self, text: str, hiragana: str) -> Optional[Tuple]:
        """匹配形容词"""
        # い形容词：以い结尾
        if len(text) >= 2 and text.endswith('い') and not text.endswith('だい'):
            # 简单判断：排除一些常见的非形容词
            if text not in ['いい']:  # いい是形容词，但容易误判
                return text, 'adjective_i', hiragana, len(text)
        
        # な形容词：通常后跟「な」
        if len(text) >= 2:
            # 检查常见的な形容词
            na_adjs = ['静か', 'しずか', '有名', 'ゆうめい', '便利', 'べんり']
            for adj in na_adjs:
                if text.startswith(adj):
                    return adj, 'adjective_na', hiragana[:len(adj)], len(adj)
        
        return None
    
    def _split_noun(self, text: str, hiragana: str) -> Tuple[str, str, str, int]:
        """分割名词（按2-4字符）"""
        # 简单策略：优先取2-4个字符，跳过标点符号
        for length in [4, 3, 2, 1]:
            if len(text) >= length:
                word = text[:length]
                # 如果包含标点符号，减少长度再试
                if any(c in self.PUNCTUATIONS for c in word):
                    continue
                word_hira = hiragana[:length]
                return word, 'noun', word_hira, length
        
        # 如果都是标点符号，返回第一个字符作为other类型
        char = text[0] if text else ''
        if char in self.PUNCTUATIONS:
            return char, 'punctuation', char, 1
        return char, 'other', hiragana[0] if hiragana else '', 1
    
    def _get_grammar_info(self, word: str, word_type: str, hiragana: str) -> Dict[str, Any]:
        """获取语法信息"""
        info = {}
        
        if word_type == 'particle':
            particle_meanings = {
                'は': '主题助词，标记句子主题',
                'が': '主格助词，标记主语',
                'を': '宾格助词，标记宾语',
                'に': '位置/时间助词',
                'で': '场所/手段助词',
                'へ': '方向助词',
                'と': '和/引用助词',
                'から': '起点/原因助词',
                'まで': '终点助词',
                'も': '也',
                'や': '等，列举',
            }
            info['meaning'] = particle_meanings.get(word, '助词')
            info['function'] = '助词'
            
        elif word_type == 'pronoun':
            pronoun_meanings = {
                '私': '我（正式）',
                '僕': '我（男性，非正式）',
                '俺': '我（男性，粗俗）',
                'あなた': '你',
                '君': '你（亲密）',
                '彼': '他',
                '彼女': '她',
            }
            info['meaning'] = pronoun_meanings.get(word, '代词')
            info['category'] = '人称代词'
            
        elif word_type.startswith('adjective'):
            info['meaning'] = '形容词'
            info['type'] = 'い形容词' if word_type == 'adjective_i' else 'な形容词'
            
        elif word_type == 'noun':
            info['meaning'] = '名词'
            info['category'] = '普通名词'
        
        return info
    
    def _detect_verb(self, word: str, hiragana: str) -> Optional[Dict[str, Any]]:
        """检测动词信息"""
        info = {}
        
        # 识别动词变形
        if word.endswith('ます'):
            stem = word[:-2]
            info['form'] = 'masu'
            info['form_name'] = '礼貌体'
            info['prototype'] = f"{stem}る"
            info['verb_class'] = '二类动词'
            
        elif word.endswith('ました'):
            stem = word[:-3]
            info['form'] = 'mashita'
            info['form_name'] = '礼貌体过去式'
            info['prototype'] = f"{stem}る"
            info['verb_class'] = '二类动词'
            
        elif word.endswith('て') or word.endswith('で'):
            info['form'] = 'te'
            info['form_name'] = 'て形'
            
        elif word.endswith('た') or word.endswith('だ'):
            info['form'] = 'ta'
            info['form_name'] = 'た形（过去式）'
            
        elif word.endswith('ない'):
            info['form'] = 'nai'
            info['form_name'] = '否定形'
        
        return info if info else None


class VerbConjugator:
    """动词活用生成器"""
    
    # 一类动词（五段）词尾变化表
    GODAN_CONJUGATIONS = {
        'う': {
            'dictionary': ('う', 'う'),
            'masu': ('います', 'います'),
            'te': ('って', 'って'),
            'ta': ('った', 'った'),
            'nai': ('わない', 'わない'),
            'potential': ('える', 'える'),
            'passive': ('われる', 'われる'),
            'causative': ('わせる', 'わせる'),
            'causative_passive': ('わせられる', 'わせられる'),
            'volitional': ('おう', 'おう'),
            'imperative': ('え', 'え'),
            'conditional': ('えば', 'えば')
        },
        'く': {
            'dictionary': ('く', 'く'),
            'masu': ('きます', 'きます'),
            'te': ('いて', 'いて'),
            'ta': ('いた', 'いた'),
            'nai': ('かない', 'かない'),
            'potential': ('ける', 'ける'),
            'passive': ('かれる', 'かれる'),
            'causative': ('かせる', 'かせる'),
            'causative_passive': ('かせられる', 'かせられる'),
            'volitional': ('こう', 'こう'),
            'imperative': ('け', 'け'),
            'conditional': ('けば', 'けば')
        },
        'ぐ': {
            'dictionary': ('ぐ', 'ぐ'),
            'masu': ('ぎます', 'ぎます'),
            'te': ('いで', 'いで'),
            'ta': ('いだ', 'いだ'),
            'nai': ('がない', 'がない'),
            'potential': ('げる', 'げる'),
            'passive': ('がれる', 'がれる'),
            'causative': ('がせる', 'がせる'),
            'causative_passive': ('がせられる', 'がせられる'),
            'volitional': ('ごう', 'ごう'),
            'imperative': ('げ', 'げ'),
            'conditional': ('げば', 'げば')
        },
        'す': {
            'dictionary': ('す', 'す'),
            'masu': ('します', 'します'),
            'te': ('して', 'して'),
            'ta': ('した', 'した'),
            'nai': ('さない', 'さない'),
            'potential': ('せる', 'せる'),
            'passive': ('される', 'される'),
            'causative': ('させる', 'させる'),
            'causative_passive': ('させられる', 'させられる'),
            'volitional': ('そう', 'そう'),
            'imperative': ('せ', 'せ'),
            'conditional': ('せば', 'せば')
        },
        'つ': {
            'dictionary': ('つ', 'つ'),
            'masu': ('ちます', 'ちます'),
            'te': ('って', 'って'),
            'ta': ('った', 'った'),
            'nai': ('たない', 'たない'),
            'potential': ('てる', 'てる'),
            'passive': ('たれる', 'たれる'),
            'causative': ('たせる', 'たせる'),
            'causative_passive': ('たせられる', 'たせられる'),
            'volitional': ('とう', 'とう'),
            'imperative': ('て', 'て'),
            'conditional': ('てば', 'てば')
        },
        'ぬ': {
            'dictionary': ('ぬ', 'ぬ'),
            'masu': ('にます', 'にます'),
            'te': ('んで', 'んで'),
            'ta': ('んだ', 'んだ'),
            'nai': ('なない', 'なない'),
            'potential': ('ねる', 'ねる'),
            'passive': ('なれる', 'なれる'),
            'causative': ('なせる', 'なせる'),
            'causative_passive': ('なせられる', 'なせられる'),
            'volitional': ('のう', 'のう'),
            'imperative': ('ね', 'ね'),
            'conditional': ('ねば', 'ねば')
        },
        'ぶ': {
            'dictionary': ('ぶ', 'ぶ'),
            'masu': ('びます', 'びます'),
            'te': ('んで', 'んで'),
            'ta': ('んだ', 'んだ'),
            'nai': ('ばない', 'ばない'),
            'potential': ('べる', 'べる'),
            'passive': ('ばれる', 'ばれる'),
            'causative': ('ばせる', 'ばせる'),
            'causative_passive': ('ばせられる', 'ばせられる'),
            'volitional': ('ぼう', 'ぼう'),
            'imperative': ('べ', 'べ'),
            'conditional': ('べば', 'べば')
        },
        'む': {
            'dictionary': ('む', 'む'),
            'masu': ('みます', 'みます'),
            'te': ('んで', 'んで'),
            'ta': ('んだ', 'んだ'),
            'nai': ('まない', 'まない'),
            'potential': ('める', 'める'),
            'passive': ('まれる', 'まれる'),
            'causative': ('ませる', 'ませる'),
            'causative_passive': ('ませられる', 'ませられる'),
            'volitional': ('もう', 'もう'),
            'imperative': ('め', 'め'),
            'conditional': ('めば', 'めば')
        },
        'る': {
            'dictionary': ('る', 'る'),
            'masu': ('ります', 'ります'),
            'te': ('って', 'って'),
            'ta': ('った', 'った'),
            'nai': ('らない', 'らない'),
            'potential': ('れる', 'れる'),
            'passive': ('られる', 'られる'),
            'causative': ('らせる', 'らせる'),
            'causative_passive': ('らせられる', 'らせられる'),
            'volitional': ('ろう', 'ろう'),
            'imperative': ('れ', 'れ'),
            'conditional': ('れば', 'れば')
        }
    }
    
    # 二类动词活用规则
    ICHIDAN_CONJUGATIONS = {
        'dictionary': ('る', 'る'),
        'masu': ('ます', 'ます'),
        'te': ('て', 'て'),
        'ta': ('た', 'た'),
        'nai': ('ない', 'ない'),
        'potential': ('られる', 'られる'),
        'passive': ('られる', 'られる'),
        'causative': ('させる', 'させる'),
        'causative_passive': ('させられる', 'させられる'),
        'volitional': ('よう', 'よう'),
        'imperative': ('ろ', 'ろ'),
        'conditional': ('れば', 'れば')
    }
    
    # 三类动词特殊规则
    IRREGULAR_VERBS = {
        'する': {
            'dictionary': ('する', 'する'),
            'masu': ('します', 'します'),
            'te': ('して', 'して'),
            'ta': ('した', 'した'),
            'nai': ('しない', 'しない'),
            'potential': ('できる', 'できる'),
            'passive': ('される', 'される'),
            'causative': ('させる', 'させる'),
            'causative_passive': ('させられる', 'させられる'),
            'volitional': ('しよう', 'しよう'),
            'imperative': ('しろ', 'せよ'),
            'conditional': ('すれば', 'すれば')
        },
        '来る': {
            'dictionary': ('来る', 'くる'),
            'masu': ('来ます', 'きます'),
            'te': ('来て', 'きて'),
            'ta': ('来た', 'きた'),
            'nai': ('来ない', 'こない'),
            'potential': ('来られる', 'こられる'),
            'passive': ('来られる', 'こられる'),
            'causative': ('来させる', 'こさせる'),
            'causative_passive': ('来させられる', 'こさせられる'),
            'volitional': ('来よう', 'こよう'),
            'imperative': ('来い', 'こい'),
            'conditional': ('来れば', 'くれば')
        }
    }
    
    FORM_NAMES = {
        'dictionary': '辞書形',
        'masu': 'ます形',
        'te': 'て形',
        'ta': 'た形',
        'nai': 'ない形',
        'potential': '可能形',
        'passive': '受身形',
        'causative': '使役形',
        'causative_passive': '使役受身形',
        'volitional': '意志形',
        'imperative': '命令形',
        'conditional': '条件形'
    }
    
    def conjugate(self, prototype: str, reading: str, verb_class: str) -> List[VerbConjugation]:
        """
        生成动词的所有活用形式
        
        Args:
            prototype: 动词原型（如「遊ぶ」「食べる」）
            reading: 读音（平假名）
            verb_class: 动词类别（一类/二类/三类）
            
        Returns:
            动词活用列表
        """
        conjugations = []
        
        if verb_class == '一类动词':
            conjugations = self._conjugate_godan(prototype, reading)
        elif verb_class == '二类动词':
            conjugations = self._conjugate_ichidan(prototype, reading)
        elif verb_class == '三类动词':
            conjugations = self._conjugate_irregular(prototype, reading)
        
        return conjugations
    
    def _conjugate_godan(self, prototype: str, reading: str) -> List[VerbConjugation]:
        """生成一类动词（五段）活用"""
        stem = prototype[:-1]
        stem_reading = reading[:-1]
        ending = reading[-1]
        
        if ending not in self.GODAN_CONJUGATIONS:
            return []
        
        rules = self.GODAN_CONJUGATIONS[ending]
        conjugations = []
        
        for form_type, (suffix, suffix_reading) in rules.items():
            conj = VerbConjugation(
                verb_id=0,  # 稍后设置
                form_type=form_type,
                form_name=self.FORM_NAMES.get(form_type, form_type),
                form_value=f"{stem}{suffix}",
                reading=f"{stem_reading}{suffix_reading}",
                example=self._generate_example(stem, suffix, form_type),
                politeness='polite' if form_type in ['masu'] else 'plain',
                difficulty=1 if form_type in ['dictionary', 'masu'] else (2 if form_type in ['te', 'ta', 'nai'] else 3),
                meaning=self._get_form_meaning(form_type)
            )
            conjugations.append(conj)
        
        return conjugations
    
    def _conjugate_ichidan(self, prototype: str, reading: str) -> List[VerbConjugation]:
        """生成二类动词（一段）活用"""
        stem = prototype[:-1]
        stem_reading = reading[:-1]
        
        conjugations = []
        
        for form_type, (suffix, suffix_reading) in self.ICHIDAN_CONJUGATIONS.items():
            conj = VerbConjugation(
                verb_id=0,
                form_type=form_type,
                form_name=self.FORM_NAMES.get(form_type, form_type),
                form_value=f"{stem}{suffix}",
                reading=f"{stem_reading}{suffix_reading}",
                example=self._generate_example(stem, suffix, form_type),
                politeness='polite' if form_type in ['masu'] else 'plain',
                difficulty=1 if form_type in ['dictionary', 'masu'] else (2 if form_type in ['te', 'ta', 'nai'] else 3),
                meaning=self._get_form_meaning(form_type)
            )
            conjugations.append(conj)
        
        return conjugations
    
    def _conjugate_irregular(self, prototype: str, reading: str) -> List[VerbConjugation]:
        """生成三类动词（不规则）活用"""
        # 检查是否是来る
        if '来' in prototype or reading.endswith('くる'):
            rules = self.IRREGULAR_VERBS['来る']
        else:
            rules = self.IRREGULAR_VERBS['する']
        
        conjugations = []
        
        for form_type, (written, yomi) in rules.items():
            # 根据原型选择正确形式
            if '来る' in prototype:
                form_value = written if '来' in prototype else written.replace('来', '来')
                form_reading = yomi
            else:
                form_value = written.replace('する', prototype)
                form_reading = reading.replace('する', yomi)
            
            conj = VerbConjugation(
                verb_id=0,
                form_type=form_type,
                form_name=self.FORM_NAMES.get(form_type, form_type),
                form_value=form_value,
                reading=form_reading,
                example=self._generate_example(prototype.replace('する', '').replace('来る', ''), '', form_type),
                politeness='polite' if form_type in ['masu'] else 'plain',
                difficulty=3,
                meaning=self._get_form_meaning(form_type)
            )
            conjugations.append(conj)
        
        return conjugations
    
    def _generate_example(self, stem: str, suffix: str, form_type: str) -> str:
        """生成例句"""
        # 简化的例句生成
        examples = {
            'dictionary': f'{stem}のが好きです',
            'masu': f'{stem}ます',
            'te': f'{stem}てください',
            'ta': f'昨日、{stem}た',
            'nai': f'{stem}ないでください',
            'potential': f'{stem}ることができます',
            'passive': f'{stem}れました',
            'causative': f'子供を{stem}せました',
            'volitional': f'一緒に{stem}ましょう',
        }
        return examples.get(form_type, f'{stem}...')
    
    def _get_form_meaning(self, form_type: str) -> str:
        """获取活用形式含义"""
        meanings = {
            'dictionary': '原型',
            'masu': '礼貌体',
            'te': '连接形',
            'ta': '过去式',
            'nai': '否定',
            'potential': '能力',
            'passive': '被动',
            'causative': '使役',
            'causative_passive': '使役被动',
            'volitional': '意向',
            'imperative': '命令',
            'conditional': '假设'
        }
        return meanings.get(form_type, '')
