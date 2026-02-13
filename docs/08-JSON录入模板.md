# 言葉AI JSON录入模板

> 用于指导AI识别图片后输出标准JSON格式

---

## 标准JSON格式模板

```json
{
  "content_type": "sentence",
  "original_jp": "日语原文",
  "hiragana": "平假名注音",
  "romaji": "罗马音",
  "chinese_meaning": "中文意思",
  "source": "截图文件名",
  "tags": {
    "grammar_points": ["语法点1", "语法点2"],
    "scene": "使用场景",
    "difficulty": 1,
    "lesson": "第几课"
  },
  "segmented_words": [
    {
      "word_jp": "单词原文",
      "hiragana": "单词假名",
      "word_type": "词性",
      "position": 0,
      "grammar_info": {
        "meaning": "词义",
        "function": "语法功能"
      }
    }
  ]
}
```

---

## 字段说明

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `content_type` | string | ✅ | 内容类型 | `sentence` (句子), `word` (单词), `phrase` (短语) |
| `original_jp` | string | ✅ | 日语原文（汉字+假名） | `私は学生です` |
| `hiragana` | string | ✅ | 纯平假名注音 | `わたしはがくせいです` |
| `romaji` | string | ⚪ | 罗马音（可选） | `watashi wa gakusei desu` |
| `chinese_meaning` | string | ✅ | 中文意思 | `我是学生` |
| `source` | string | ⚪ | 截图文件名（可选） | `duolingo_20260211_001.png` |
| `tags` | object | ⚪ | 扩展信息（可选） | 包含语法点、场景、难度等 |

### tags 子字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `grammar_points` | array | 语法点列表 | `["は主题助词", "です判断句"]` |
| `scene` | string | 使用场景 | `自我介绍`, `购物`, `点餐` |
| `difficulty` | number | 难度等级 1-5 | `1` (简单) 到 `5` (困难) |
| `lesson` | string | 课程信息 | `第3课`, `L5` |

### segmented_words 子字段（重要！由AI预分词）

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `word_jp` | string | ✅ | 单词原文（含汉字） | `私`, `学生`, `です` |
| `hiragana` | string | ✅ | 单词平假名读音 | `わたし`, `がくせい`, `です` |
| `word_type` | string | ✅ | 词性标记 | 见下方词性表 |
| `position` | number | ✅ | 在句子中的位置（从0开始） | `0`, `1`, `2` |
| `grammar_info` | object | ⚪ | 语法信息 | `{"meaning": "我", "function": "代词"}` |

#### 词性标记（word_type）

| 词性值 | 说明 | 示例 |
|--------|------|------|
| `noun` | 名词 | `学生`, `本` |
| `verb` | 动词 | `食べる`, `行きます` |
| `adjective_i` | い形容词 | `大きい`, `新しい` |
| `adjective_na` | な形容词 | `静か`, `便利` |
| `particle` | 助词 | `は`, `が`, `を` |
| `pronoun` | 代词 | `私`, `あなた` |
| `adverb` | 副词 | `とても`, `すぐ` |
| `aux_verb` | 助动词 | `です`, `ます` |
| `conjunction` | 连词 | `そして`, `でも` |
| `interjection` | 感叹词 | `ああ`, `はい` |

---

## 实际示例

### 示例1：句子（含AI预分词）

```json
{
  "content_type": "sentence",
  "original_jp": "私は学生です",
  "hiragana": "わたしはがくせいです",
  "romaji": "watashi wa gakusei desu",
  "chinese_meaning": "我是学生",
  "source": "duolingo_20260211_001.png",
  "tags": {
    "grammar_points": ["は主题助词", "です礼貌体"],
    "scene": "自我介绍",
    "difficulty": 1,
    "lesson": "第3课"
  },
  "segmented_words": [
    {
      "word_jp": "私",
      "hiragana": "わたし",
      "word_type": "pronoun",
      "position": 0,
      "grammar_info": {
        "meaning": "我",
        "category": "人称代词"
      }
    },
    {
      "word_jp": "は",
      "hiragana": "は",
      "word_type": "particle",
      "position": 1,
      "grammar_info": {
        "meaning": "主题助词",
        "function": "标记句子主题"
      }
    },
    {
      "word_jp": "学生",
      "hiragana": "がくせい",
      "word_type": "noun",
      "position": 2,
      "grammar_info": {
        "meaning": "学生",
        "category": "职业/身份"
      }
    },
    {
      "word_jp": "です",
      "hiragana": "です",
      "word_type": "aux_verb",
      "position": 3,
      "grammar_info": {
        "meaning": "是（礼貌体）",
        "function": "判断助动词"
      }
    }
  ]
}
```

### 示例2：单词

```json
{
  "content_type": "word",
  "original_jp": "学生",
  "hiragana": "がくせい",
  "romaji": "gakusei",
  "chinese_meaning": "学生",
  "source": "duolingo_20260211_002.png",
  "tags": {
    "word_type": "noun",
    "category": "职业/身份",
    "difficulty": 1
  }
}
```

### 示例3：短语

```json
{
  "content_type": "phrase",
  "original_jp": "おはようございます",
  "hiragana": "おはようございます",
  "romaji": "ohayou gozaimasu",
  "chinese_meaning": "早上好（礼貌）",
  "source": "duolingo_20260211_003.png",
  "tags": {
    "scene": "早晨问候",
    "politeness": "礼貌体",
    "difficulty": 1
  }
}
```

### 示例4：含动词的句子

```json
{
  "content_type": "sentence",
  "original_jp": "ちびまる子ちゃんと一緒におもちゃで遊びます",
  "hiragana": "ちびまるこちゃんといっしょにおもちゃであそびます",
  "romaji": "chibi maruko chan to issho ni omocha de asobimasu",
  "chinese_meaning": "和樱桃小丸子一起玩玩具",
  "source": "duolingo_20260211_004.png",
  "tags": {
    "grammar_points": ["と表示和", "で表示手段", "ます礼貌体"],
    "scene": "日常活动",
    "difficulty": 2,
    "lesson": "第5课"
  }
}
```

---

## 识别流程（重要更新：AI预分词）

### 步骤1：用户发送截图
用户会说：
> "请识别这些日语学习内容，并按JSON录入模板分词"

### 步骤2：AI识别并预分词
AI必须完成以下工作：
1. ✅ 识别图片中的日语原文
2. ✅ 转换为完整平假名注音
3. ✅ 转换为罗马音（可选）
4. ✅ 翻译成中文
5. ✅ **对句子进行分词**（重要！每个单词单独拆分）
6. ✅ **标注每个单词的词性和语法信息**
7. ✅ 按上述JSON格式输出（含 `segmented_words` 数组）

#### 分词要求：
- **粒度**：每个独立的词（单词/助词/助动词）都要分开
- **准确性**：确保 `word_jp` + `hiragana` 拼接后与完整句子一致
- **词性**：正确标注 noun/verb/particle/pronoun 等
- **位置**：position 从 0 开始顺序递增

### 步骤3：用户复制JSON到系统
用户复制AI返回的完整JSON（含分词数据），粘贴到言葉AI录入页面。

#### ⚠️ 重要提示：
- 如果JSON中提供了 `segmented_words`，系统将**直接使用**AI的分词结果
- 如果没有提供，系统将使用**不准确的自动分词**（不推荐）
- **强烈建议**每次都让AI预分词，保证准确性

---

## 特殊情况处理

### 多个内容识别
如果截图中有多个单词或句子，输出JSON数组：

```json
[
  {
    "content_type": "word",
    "original_jp": "学生",
    "hiragana": "がくせい",
    "chinese_meaning": "学生"
  },
  {
    "content_type": "word",
    "original_jp": "先生",
    "hiragana": "せんせい",
    "chinese_meaning": "老师"
  }
]
```

### 不确定的读音
如果不确定汉字读音，标注出来：

```json
{
  "content_type": "sentence",
  "original_jp": "今日は良い天気です",
  "hiragana": "きょうは[よ/い]い[天/てん][気/き]です",
  "note": "[中/日]表示不确定的读音，请用户确认"
}
```

---

## 提示语模板（推荐）

复制以下内容发送给AI：

```
请识别图片中的日语学习内容，并按以下JSON格式输出：

{
  "content_type": "sentence",
  "original_jp": "日语原文（含汉字假名）",
  "hiragana": "平假名注音（不含标点）",
  "romaji": "罗马音",
  "chinese_meaning": "中文意思",
  "source": "截图来源",
  "tags": {
    "grammar_points": ["语法点"],
    "scene": "使用场景",
    "difficulty": 1-5
  },
  "segmented_words": [
    {
      "word_jp": "单词1",
      "hiragana": "假名1",
      "word_type": "词性(noun/verb/particle等)",
      "position": 0,
      "grammar_info": {"meaning": "词义", "function": "语法功能"}
    },
    {
      "word_jp": "单词2",
      "hiragana": "假名2",
      "word_type": "词性",
      "position": 1,
      "grammar_info": {}
    }
  ]
}

要求：
1. original_jp 保留原文的汉字和假名（含标点）
2. hiragana 提供完整平假名注音（❌不含标点！）
3. segmented_words 必须对句子进行准确分词（重要！）
4. 每个单词单独一项，词性标注准确
5. 助词（は/が/を等）和助动词（です/ます等）都要单独拆分
6. 所有 word_jp 拼接 = original_jp（去掉标点）
7. 所有 hiragana 拼接 = 完整注音（去掉标点）
8. 分析主要语法点并标注使用场景
```

---

## 验证检查清单

输出JSON后，请检查：

### 基础信息
- [ ] `original_jp` 和 `hiragana` 对应正确
- [ ] `chinese_meaning` 翻译准确
- [ ] `hiragana` 包含完整的读音（不含标点）
- [ ] `tags.grammar_points` 列出了主要语法点

### 分词数据（重要！）
- [ ] `segmented_words` 字段存在且为数组
- [ ] 所有单词的 `word_jp` 拼接起来等于 `original_jp`（去掉标点）
- [ ] 所有单词的 `hiragana` 拼接起来等于完整注音（去掉标点）
- [ ] 每个单词都有正确的 `word_type` 词性标记
- [ ] `position` 从 0 开始连续递增
- [ ] 动词、形容词标注了正确的语法信息

### JSON格式
- [ ] JSON格式正确（可用jsonlint.com验证）
- [ ] 没有遗漏的逗号或括号

---

**版本**: v2.0  
**最后更新**: 2026-02-11  
**更新说明**: 新增 `segmented_words` AI预分词字段，确保分词准确性
