# classifier_inference.py

import joblib
import numpy as np
from DataGen2 import DataGenCCS

CLASSES = ["benign", "ccs1", "ccs2", "ccs3", "ccs4", "ccs5", "ccs6", "ccs7"]
LABEL_NAMES = {
    "benign" : "Benign",
    "ccs1"   : "Authority",
    "ccs2"   : "Context_Poisoning",
    "ccs3"   : "Goal_Conflict",
    "ccs4"   : "Role_Confusion",
    "ccs5"   : "False_Premise",
    "ccs6"   : "Cognitive_Overload",
    "ccs7"   : "Emotional_Manipulation"
}


class CCSClassifier:
    def __init__(self,
                 model_path    = "ccs_classifier.joblib",
                 embedder_path = "ccs_embedder.joblib",
                 confidence_threshold = 0.4):
        self.clf       = joblib.load(model_path)
        self.embedder  = joblib.load(embedder_path)
        self.threshold = confidence_threshold
        # Below this confidence, flag as uncertain rather than committing

    def classify(self, prompt: str) -> dict:
        embedding  = self.embedder.encode([prompt])
        proba      = self.clf.predict_proba(embedding)[0]
        scores     = dict(zip(self.clf.classes_, proba))

        predicted  = self.clf.classes_[np.argmax(proba)]
        confidence = float(np.max(proba))

        # If top prediction is below threshold, mark uncertain
        if confidence < self.threshold:
            predicted = "uncertain"

        return {
            "label"      : predicted,
            "name"       : LABEL_NAMES.get(predicted, "Uncertain"),
            "confidence" : round(confidence, 4),
            "scores"     : {k: round(float(v), 4) for k, v in scores.items()},
            "flagged"    : predicted not in ("benign", "uncertain")
        }
    

if __name__ == "__main__":
    clas = CCSClassifier()
    gen = DataGenCCS()
    Data = gen.generate_balanced_dataset(3)
    for index, data in Data.iterrows():
        answer = CLASSES[data['label']]
        res = clas.classify(data['prompt'])
        print("EXPECTED: " + answer)
        print("RECEIVED: " + res['label'])
        print()


