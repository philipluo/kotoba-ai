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
  }
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

---

## 实际示例

### 示例1：句子

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
  }
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

## 识别流程

### 步骤1：用户发送截图
用户会说：
> "请识别这些日语学习内容"

### 步骤2：AI识别并输出JSON
AI应该：
1. 识别图片中的日语内容
2. 转换为平假名
3. 转换为罗马音（可选）
4. 翻译成中文
5. 分析语法点
6. 按上述JSON格式输出

### 步骤3：用户复制JSON到系统
用户复制AI返回的JSON，粘贴到言葉AI的录入页面

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

## 提示语模板

复制以下内容发送给AI：

```
请识别图片中的日语学习内容，并按以下JSON格式输出：

{
  "content_type": "sentence",  // sentence, word, phrase
  "original_jp": "日语原文",
  "hiragana": "平假名注音",
  "romaji": "罗马音",
  "chinese_meaning": "中文意思",
  "source": "截图来源",
  "tags": {
    "grammar_points": ["语法点"],
    "scene": "使用场景",
    "difficulty": 1-5,
    "lesson": "课程信息"
  }
}

要求：
1. original_jp 保留原文的汉字和假名
2. hiragana 提供完整的平假名注音
3. 分析主要语法点
4. 标注使用场景和难度
```

---

## 验证检查清单

输出JSON后，请检查：

- [ ] `original_jp` 和 `hiragana` 对应正确
- [ ] `chinese_meaning` 翻译准确
- [ ] `hiragana` 包含完整的读音
- [ ] `tags.grammar_points` 列出了主要语法点
- [ ] JSON格式正确（可用jsonlint.com验证）

---

**版本**: v1.0  
**最后更新**: 2026-02-11
