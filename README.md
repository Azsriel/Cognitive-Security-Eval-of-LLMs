# Cognitive-Security-Eval-of-LLMs
This project addresses the rising challenge of guaranteeing cognitive security in Large Language Models (LLMs), which, despite their advanced reasoning and language skills, are still susceptible to concerns including hallucination, prompt injection, alignment drift, and reasoning inconsistencies. Existing safety methods are highly fragmented, reactive, and limited to discrete weaknesses, rendering them ineffective in real-world, adversarial contexts. To address these shortcomings, this study uses the CCS-7 paradigm as a unifying lens to systematically assess and minimize cognitive vulnerabilities in LLMs. The project envisions a modular guardrail engineering pipeline that includes fast sanitization, vulnerability classification, adaptive guardrail injection, LLM invocation, and optional reasoning verification. A MiniLM-based multi-label classifier is utilized to detect threats in all seven CCS-7 categories, allowing for context-aware and customized mitigation techniques. The system is designed to be scalable, explainable, and expandable, with support for both real-time and batch processing. It runs on open-source tools and locally hosted models, which ensures cost-effectiveness and reproducibility. Furthermore, a structured prompt dataset is created to stress-test LLM behavior in both hostile and benign conditions. The research compares model performance with and without guardrails to assess advances in safety, reasoning integrity, and alignment robustness. The findings seek to close the gap between theoretical vulnerability frameworks and practical implementation, hence helping to the creation of safer, more trustworthy AI systems. Overall, this study presents a comprehensive and repeatable approach to cognitive security evaluation in LLMs, enabling responsible deployment in real-world applications.

# Results
## Results with pipeline
| Label   | Vulnerability          |   Total |    PASS |   WARN |  FAIL | UNKNOWN |
| ------- | ---------------------- | ------: | ------: | -----: | ----: | ------: |
| benign  | Benign                 |      18 |      16 |      2 |     0 |       0 |
| ccs1    | Authority              |      46 |      46 |      0 |     0 |       0 |
| ccs2    | Context Poisoning      |      56 |      56 |      0 |     0 |       0 |
| ccs3    | Goal Conflict          |      35 |      32 |      2 |     1 |       0 |
| ccs4    | Role Confusion         |       7 |       5 |      1 |     1 |       0 |
| ccs5    | False Premise          |      13 |       3 |      6 |     4 |       0 |
| ccs6    | Cognitive Overload     |      11 |      11 |      0 |     0 |       0 |
| ccs7    | Emotional Manipulation |      13 |      13 |      0 |     0 |       0 |
| **ALL** | **Combined**           | **199** | **182** | **11** | **6** |   **0** |

## Results without pipeline
| Label   | Vulnerability          |   Total |    PASS |   WARN |   FAIL | UNKNOWN |
| ------- | ---------------------- | ------: | ------: | -----: | -----: | ------: |
| benign  | Benign                 |      18 |      18 |      0 |      0 |       0 |
| ccs1    | Authority              |      46 |      42 |      4 |      0 |       0 |
| ccs2    | Context Poisoning      |      55 |      53 |      1 |      1 |       0 |
| ccs3    | Goal Conflict          |      35 |      15 |     12 |      8 |       0 |
| ccs4    | Role Confusion         |       7 |       7 |      0 |      0 |       0 |
| ccs5    | False Premise          |      13 |       3 |      4 |      6 |       0 |
| ccs6    | Cognitive Overload     |      10 |       8 |      1 |      1 |       0 |
| ccs7    | Emotional Manipulation |      14 |      12 |      1 |      1 |       0 |
| **ALL** | **Combined**           | **198** | **158** | **23** | **17** |   **0** |

