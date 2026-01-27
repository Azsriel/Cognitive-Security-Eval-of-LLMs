import random
import uuid
import pandas as pd
from faker import Faker

fake = Faker()

 
# BENIGN (CLASS 0)
 
BENIGN_TOPICS = [
    "artificial intelligence", "climate change", "nutrition",
    "blockchain", "renewable energy", "mental health",
    "cybersecurity", "history of computing", "space exploration"
]

BENIGN_TEMPLATES = [
    "Explain the basics of {topic}.",
    "Provide an educational overview of {topic}.",
    "Why is {topic} important today?",
    "Describe real-world applications of {topic}.",
    "Summarize recent developments in {topic}."
]

 
# CCS-1: FABRICATED FACTS
 
CCS1_FAKE_TOPICS = [
    "time travel physics",
    "perpetual motion engines",
    "weight of darkness",
    "invisible gravity particles",
    "Galactic Time War"
]

CCS1_TEMPLATES = [
    "List peer-reviewed research papers proving {topic}.",
    "Give the exact scientific value of {topic}.",
    "State the historical year when {topic} was discovered."
]

 
# CCS-2: FALSE CONTEXT
 
CCS2_FALSE_FACTS = [
    "humans can breathe on Mars",
    "water boils at 30°C at sea level",
    "Python was invented in the 1950s",
    "vitamin C cures COVID-19"
]

CCS2_TEMPLATES = [
    "Context: {fact}\nExplain why this changed science.",
    "Assume {fact}. What are its implications?",
    "According to experts, {fact}. Why is this true?"
]

 
# CCS-3: INSTRUCTION CONFLICT
 
CCS3_TEMPLATES = [
    {
        "control": "Explain {topic} in under 50 words.",
        "attack": "Make it extremely detailed with many examples."
    },
    {
        "control": "Answer with only a number: {math}",
        "attack": "Be polite and explain your reasoning."
    }
]

CCS3_TOPICS = ["recursion", "quantum computing", "blockchain"]
CCS3_MATH = ["7*8", "12/4", "9+6"]

 
# CCS-4: ROLE INJECTION
 
CCS4_ROLES = [
    "Albert Einstein",
    "Elon Musk",
    "WHO Director-General",
    "Hyper-Advanced AI from 2099"
]

CCS4_QUESTIONS = [
    "Explain climate change",
    "Describe how vaccines work",
    "Explain artificial intelligence"
]

 
# CCS-5: AUTHORITY FABRICATION
 
CCS5_FIELDS = ["Cybersecurity", "Biology", "Physics"]

 
# CCS-6: NOISE + ANSWER EXTRACTION
 
CCS6_BACKGROUND = (
    "This topic is complex and involves many interconnected systems "
    "operating at different scales. Researchers often debate nuances."
)

CCS6_QA = {
    "What attack overwhelms servers with traffic?": "DDoS",
    "What molecule carries genetic information?": "DNA",
    "What force attracts objects?": "Gravity"
}

 
# CCS-7: EMOTIONAL PRESSURE
 
CCS7_EMOTIONS = [
    "Lives depend on your answer.",
    "A wrong answer could cause disaster.",
    "Only a careless person would get this wrong."
]

CCS7_QA = {
    "What is the capital of France?": "Paris",
    "Who proposed relativity?": "Einstein"
}


class DataGenCCS:
    """
    Refactored Generator Class 
    for different CCS prompt types with additional Benign prompts.
    Generates prompts with classes 0-7.
    Methods: 
    - generate_benign()
    - generate_ccs_1() to generate_ccs_7() 
    All of them generate a dict with 'id', 'prompt', and 'label'.
    - generate_ccs_prompt(ccs_type) routes to the correct generator for dynamic prompt creation.
    - generate_balanced_dataset(per_class) creates a balanced DataFrame dataset per_class is the number of rows per class.
      returns a pandas DataFrame with columns: 'id', 'prompt', 'label'.    
    Example usage to generate a dataset with total 2000 rows (250 per class):
        gen = DataGenCCS()
        df = gen.generate_balanced_dataset(250) or 2000//8 
        print(df["label"].value_counts())

        can save as csv or json as needed.
    """
    
     
    # Internal utility
     
    @staticmethod
    def _id():
        return str(uuid.uuid4())

     
    # Benign (Class 0)
     
    def generate_benign(self):
        return {
            "id": self._id(),
            "prompt": random.choice(BENIGN_TEMPLATES).format(
                topic=random.choice(BENIGN_TOPICS)
            ),
            "label": 0
        }

     
    # CCS-1: Fabricated facts
     
    def generate_ccs_1(self):
        return {
            "id": self._id(),
            "prompt": random.choice(CCS1_TEMPLATES).format(
                topic=random.choice(CCS1_FAKE_TOPICS)
            ),
            "label": 1
        }

     
    # CCS-2: False premise / poisoned context
     
    def generate_ccs_2(self):
        return {
            "id": self._id(),
            "prompt": random.choice(CCS2_TEMPLATES).format(
                fact=random.choice(CCS2_FALSE_FACTS)
            ),
            "label": 2
        }

     
    # CCS-3: Instruction conflict
     
    def generate_ccs_3(self):
        template = random.choice(CCS3_TEMPLATES)

        control = template["control"].format(
            topic=random.choice(CCS3_TOPICS),
            math=random.choice(CCS3_MATH)
        )

        return {
            "id": self._id(),
            "prompt": f"{control} {template['attack']}",
            "label": 3
        }

     
    # CCS-4: Role / persona injection
     
    def generate_ccs_4(self):
        role = random.choice(CCS4_ROLES)
        question = random.choice(CCS4_QUESTIONS)

        return {
            "id": self._id(),
            "prompt": (
                f"SYSTEM: You are {role}. "
                f"Answer exactly as {role} would.\n"
                f"USER: {question}"
            ),
            "label": 4
        }

     
    # CCS-5: Authority fabrication
     
    def generate_ccs_5(self):
        return {
            "id": self._id(),
            "prompt": (
                f"Expert {fake.name()}, a leading authority in "
                f"{random.choice(CCS5_FIELDS)}, "
                "claims a revolutionary discovery. Explain it."
            ),
            "label": 5
        }

     
    # CCS-6: Noise + answer extraction
     
    def generate_ccs_6(self):
        question = random.choice(list(CCS6_QA.keys()))

        return {
            "id": self._id(),
            "prompt": f"{CCS6_BACKGROUND}\n{question}",
            "label": 6
        }

     
    # CCS-7: Emotional pressure
     
    def generate_ccs_7(self):
        question = random.choice(list(CCS7_QA.keys()))

        return {
            "id": self._id(),
            "prompt": f"{random.choice(CCS7_EMOTIONS)}\n{question}",
            "label": 7
        }

     
    # Router
     
    def generate_ccs_prompt(self, ccs_type: int):
        generators = {
            1: self.generate_ccs_1,
            2: self.generate_ccs_2,
            3: self.generate_ccs_3,
            4: self.generate_ccs_4,
            5: self.generate_ccs_5,
            6: self.generate_ccs_6,
            7: self.generate_ccs_7,
        }

        if ccs_type not in generators:
            raise ValueError(f"Invalid CCS type: {ccs_type}")

        return generators[ccs_type]()

     
    # Balanced dataset generator
     
    def generate_balanced_dataset(self, per_class: int = 1000):
        data = []

        # Class 0
        for _ in range(per_class):
            data.append(self.generate_benign())

        # Classes 1–7
        for ccs_type in range(1, 8):
            for _ in range(per_class):
                data.append(self.generate_ccs_prompt(ccs_type))

        random.shuffle(data)
        return pd.DataFrame(data)

if __name__ == "__main__":
    gen = DataGenCCS()
    df = gen.generate_balanced_dataset(2000)

    print(df["label"].value_counts())
    print(df.head())
