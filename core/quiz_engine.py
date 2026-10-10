import random
from typing import List, Dict, Any
from core.vocabulary_db import VocabularyDB


class QuizQuestion:
    def __init__(self, q_type: str, prompt: str, target: str, options: List[str], 
                 word_id: int, extra: Dict[str, Any] = None):
        self.q_type = q_type          # 'choice', 'scramble', 'match'
        self.prompt = prompt          # Ekranda gösterilecek soru
        self.target = target          # Doğru cevap
        self.options = options        # Şıklar veya kelime blokları
        self.word_id = word_id        # Kelime id'si (SRS güncellemesi için)
        self.extra = extra or {}      # Ek veriler (eşleştirme çiftleri vb.)

    def to_dict(self):
        return {
            "type": self.q_type,
            "prompt": self.prompt,
            "target": self.target,
            "options": self.options,
            "word_id": self.word_id,
            "extra": self.extra
        }


class QuizEngine:
    def __init__(self, db: VocabularyDB = None):
        self.db = db or VocabularyDB()

    def generate_quiz_session(self, question_count: int = 8) -> List[QuizQuestion]:
        """
        SRS sırasına göre kelimeleri çeker ve Duolingo tarzı karışık soru listesi üretir.
        """
        review_words = self.db.get_review_words(limit=question_count)
        all_words = self.db.get_all_words()

        if not review_words:
            review_words = all_words[:question_count]

        if not review_words:
            return []

        questions: List[QuizQuestion] = []

        # En az 4 kelime varsa eşleştirme (Match Pairs) sorusu ekle
        if len(all_words) >= 4:
            match_subset = random.sample(all_words, min(4, len(all_words)))
            pairs = {w["word"]: w["meaning"] for w in match_subset}
            
            tokens = list(pairs.keys()) + list(pairs.values())
            random.shuffle(tokens)
            
            questions.append(QuizQuestion(
                q_type="match",
                prompt="Kelimeleri Türkçe karşılıklarıyla eşleştirin:",
                target="",
                options=tokens,
                word_id=-1,
                extra={"pairs": pairs}
            ))

        # Kalan soruları 'choice' ve 'scramble' olarak dağıt
        for w in review_words:
            word_str = w["word"]
            meaning_str = w["meaning"]
            w_id = w["id"]

            distractors = [
                other["meaning"] for other in all_words 
                if other["word"].lower() != word_str.lower()
            ]
            if len(distractors) >= 3:
                chosen_distractors = random.sample(distractors, 3)
            else:
                chosen_distractors = ["seçenek A", "seçenek B", "seçenek C"][:len(distractors)]

            coin = random.random()

            if coin < 0.65 or len(word_str.split()) > 1:
                # Çoktan Seçmeli
                options = [meaning_str] + chosen_distractors
                random.shuffle(options)

                questions.append(QuizQuestion(
                    q_type="choice",
                    prompt=f"Bu kelimenin anlamı nedir?\n\n<b>{word_str.upper()}</b>",
                    target=meaning_str,
                    options=options,
                    word_id=w_id
                ))
            else:
                # Kelime Blokları (Scramble / Word Bank)
                target_words = meaning_str.split()
                if len(target_words) > 1:
                    tokens = list(target_words)
                    extra_tokens = ["ve", "için", "bir", "ile"]
                    tokens.append(random.choice(extra_tokens))
                    random.shuffle(tokens)

                    questions.append(QuizQuestion(
                        q_type="scramble",
                        prompt=f"Doğru anlamı oluşturun:\n\n<b>{word_str.upper()}</b>",
                        target=meaning_str,
                        options=tokens,
                        word_id=w_id
                    ))
                else:
                    options = [meaning_str] + chosen_distractors
                    random.shuffle(options)
                    questions.append(QuizQuestion(
                        q_type="choice",
                        prompt=f"Bu kelimenin anlamı nedir?\n\n<b>{word_str.upper()}</b>",
                        target=meaning_str,
                        options=options,
                        word_id=w_id
                    ))

        random.shuffle(questions)
        return questions[:question_count]