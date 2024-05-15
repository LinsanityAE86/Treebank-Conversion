import spacy

# 加载spaCy模型
nlp = spacy.load('zh_core_web_sm')

# 输入文本数据
text = "罗立言率府中从人自东来，李孝本率台中从人自西来，共四百馀人，上殿纵击，内官死伤者数十人。训时愈急，逦迆入宣政门，帝瞋目叱训，内官]志荣奋拳击其胸，训即僵仆于地。。"

# 将文本数据输入到模型中进行预测
doc = nlp(text)

# 输出识别出的命名实体
for entity in doc.ents:
    print(entity.text, entity.label_)
