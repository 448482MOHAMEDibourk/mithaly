# -*- coding: utf-8 -*-
from mithaly.core.registry import register_layer


@register_layer('gaps')
class GapAnalyzer:
    """Simple GapAnalyzer stub for mithaly.core.gaps.

    Upgraded: `process` now extracts keywords and flags incomplete descriptions.
    """

    def __init__(self):
        pass

    def process(self, data):
        """Process input data: extract keywords and assess completeness.

        Heuristics implemented:
        - Tokenize text, remove common stopwords (Arabic + English)
        - Choose top keywords by frequency
        - Flag `needs_clarification` when text is short or few keywords found

        Args:
            data: input string or dict containing 'text' key.
        Returns:
            dict with keys: `layer`, `status`, `keywords`, `needs_clarification`, `suggestions`, `input`
        """
        text = None
        if isinstance(data, dict):
            text = data.get('text') or data.get('description')
        elif isinstance(data, str):
            text = data

        if not text:
            print('[gaps] GapAnalyzer: لا يوجد وصف نصي؛ يلزم توضيح الوصف.')
            return {
                'layer': 'gaps',
                'status': 'ok',
                'keywords': [],
                'needs_clarification': True,
                'suggestions': ['أضف وصفاً مختصراً عن الهدف، النتيجة المتوقعة، والقيود.'],
                'input': data,
            }

        import re
        from collections import Counter

        # minimal stopword sets (expandable)
        arabic_stop = set(['و', 'في', 'على', 'من', 'إلى', 'عن', 'هذا', 'هذه', 'هو', 'هي', 'أن', 'ما', 'مع', 'كل', 'ل', 'لا', 'نحن', 'أنا', 'هناك', 'قد', 'كان', 'كانت'])
        english_stop = set(['the', 'and', 'or', 'in', 'on', 'of', 'to', 'a', 'an', 'for', 'with', 'by', 'is', 'are', 'be'])

        # normalize and tokenize
        norm = text.lower()
        tokens = re.findall(r"[\w\u0600-\u06FF']+", norm)
        # filter tokens
        tokens = [t for t in tokens if len(t) > 1 and t not in arabic_stop and t not in english_stop]

        counts = Counter(tokens)
        # choose top keywords (up to 8)
        keywords = [w for w, _ in counts.most_common(8)]

        # heuristics for clarification
        needs_clarification = False
        suggestions = []
        if len(text.strip()) < 40 or len(keywords) < 3:
            needs_clarification = True
            suggestions.append('الوصف قصير أو مفتقر لتفاصيل كافية؛ أضف هدفًا واضحًا ونطاقًا أو أمثلة.')

        # detect vague terms
        vague = set(['بعض', 'متعدد', 'غير محدد', 'etc', 'etc.'])
        if any(v in norm for v in vague):
            needs_clarification = True
            suggestions.append('تجنّب الكلمات الفضفاضة مثل "بعض" أو "متعدد"؛ حدد أمثلة أو أرقام إن أمكن.')
        # Context analysis: classify project type and detect technical mentions
        project_type = None
        detected_languages = []
        detected_databases = []
        technical_gaps = []

        # project type heuristics
        if any(k in norm for k in ['web', 'ويب', 'frontend', 'backend', 'django', 'flask', 'react', 'angular', 'vue']):
            project_type = 'web'
        elif any(k in norm for k in ['cli', 'command-line', 'سطر', 'terminal']):
            project_type = 'cli'
        elif any(k in norm for k in ['bot', 'telegram', 'slack', 'discord', 'روبوت']):
            project_type = 'bot'
        else:
            project_type = 'unknown'

        # detect languages and databases
        language_keywords = {'python', 'javascript', 'java', 'go', 'rust', 'php', 'ruby', 'c#', 'c++'}
        db_keywords = {'mysql', 'postgres', 'postgresql', 'sqlite', 'mongodb', 'redis'}
        for lang in language_keywords:
            if lang in norm:
                detected_languages.append(lang)
        for db in db_keywords:
            if db in norm:
                detected_databases.append(db)

        # technical gap heuristics
        if not detected_languages:
            technical_gaps.append('missing_language')
            suggestions.append('لم تُذكر لغة برمجة مفضلة؛ حدد لغة أو أطر عمل إن وُجدت.')
        # if text implies persistent data but no DB mentioned
        if any(w in norm for w in ['data', 'database', 'حفظ', 'تخزين', 'بيانات', 'store']):
            if not detected_databases:
                technical_gaps.append('missing_database')
                suggestions.append('المشروع يتعامل مع بيانات لكن لم تُذكر قاعدة بيانات؛ ضع متطلبات التخزين.')
        # generate clarification questions when technical gaps exist for web/bot projects
        clarification_questions = []
        if technical_gaps and project_type in ('web', 'bot'):
            if 'missing_language' in technical_gaps:
                clarification_questions.append('ما لغة البرمجة والإطار المفضل لديك؟ مثال: Python/Django، JavaScript/Node.js/Express')
            if 'missing_database' in technical_gaps:
                clarification_questions.append('ما قاعدة البيانات التي تفضل استخدامها لحفظ السجلات والبيانات؟ مثال: PostgreSQL، MySQL، MongoDB')
            if needs_clarification:
                clarification_questions.append('هل يمكنك إعطاء أمثلة للبيانات أو السيناريوهات الرئيسية لاستخدام النظام؟')

        print('[gaps] GapAnalyzer تعمل الآن. الكلمات المفتاحية المستخرجة:', keywords)
        print('[gaps] تصنيف نوع المشروع:', project_type)
        if detected_languages:
            print('[gaps] لغات مكتشفة:', detected_languages)
        if detected_databases:
            print('[gaps] قواعد بيانات مكتشفة:', detected_databases)
        if clarification_questions:
            print('[gaps] أسئلة توضيحية مقترحة:', clarification_questions)
        elif needs_clarification or technical_gaps:
            print('[gaps] احتياج إلى توضيح أو فجوات تقنية — اقتراحات:', suggestions)
        else:
            print('[gaps] الوصف كافٍ للمستوى الأولي.')

        return {
            'layer': 'gaps',
            'status': 'ok',
            'keywords': keywords,
            'needs_clarification': needs_clarification,
            'suggestions': suggestions,
            'project_type': project_type,
            'detected_languages': detected_languages,
            'detected_databases': detected_databases,
            'technical_gaps': technical_gaps,
            'clarification_questions': clarification_questions,
            'input': data,
            'probe': {
                'layer': 'gaps',
                'capabilities': ['extract_keywords', 'detect_databases'],
                'requirements': {
                    'requires_db': 'yes' if detected_databases else 'maybe'
                },
                'attributes': {
                    'estimated_time_seconds': 5,
                    'sensitive': False,
                }
            },
        }

    def probe(self, data=None):
        """Return a lightweight probe describing capabilities/requirements."""
        # re-run a light detection if data provided, otherwise generic
        if data and isinstance(data, dict):
            det = []
            g = self.process(data)
            det = g.get('detected_databases', [])
            req = {'requires_db': 'yes' if det else 'maybe'}
        else:
            req = {'requires_db': 'maybe'}

        return {
            'layer': 'gaps',
            'capabilities': ['extract_keywords', 'detect_databases'],
            'requirements': req,
            'attributes': {'estimated_time_seconds': 5, 'sensitive': False},
        }

