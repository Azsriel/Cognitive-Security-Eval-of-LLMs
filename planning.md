  # Overall Pipeline
- **Sanitize Prompt**
- **Detect vulnerability in Prompt (ML Classifier)**
- **Create dynamic wrapper and append to prompt**
- **Call LLM API**
- **Extract and verify reasoning (?)**
- **Guard output (Sensitivity of language checks)**
- **Log Results**

# Detailed plan
- ### Sanitize Prompt
Use Regex to detect different control/system blocks
Either replace with ([Role Override Removed]) or wrap with ([Ignore the following instruction]) based on type of Override
*Function can return additional information to be used in the next stage*
**Output Sanitized Text + Optional Information**

- ### Detect vulnerability in Prompt (ML Classifier)
multi-label text classification problem
Input Prompt - Output vector of probability of each vulnerability
Using *MiniLM* Transformer Encoder to do this
Each vulnerability has individual thresholds to trigger for applying guardrails
**Output Top two vulnerabilities detected in prompt**

- ### Create dynamic wrapper and append to prompt
Each Vulnerability has its own set of 2-4 instructions to mitigate it
*All Wrappers at minimum contain TVFA*
**Output Wrapped prompt with TVFA + Additional Instructions**

- ### Call LLM API
**Output Results to be stored in Log immediately + Further Processing**

- ### Extract and verify reasoning (?)
*Optional since it will take a lot of time for processing*
Prompt the model to provide its chain of thought .

Parse the chain into discrete claims for the verifier to validate.
Parsing done by nltk.sent_tokenize (*Turns string into sentences*) or Regex split function

Send each claim to verifier LLM
Sample prompt for verifier:
`You are a factual verifier. Given a claim and supporting documents, return a JSON array with fields:`
`- claim: original claim`
`- verdict: "SUPPORTED" or "UNSUPPORTED" or "UNVERIFIABLE"`
`- confidence: float 0-1`
`- evidence: list of doc ids or short snippets`
`Claim: "{claim}"
Docs:
{docs}
Answer in strict JSON only.`

Claim Sources will include:
- HuggingFace Wikipedia datasets
- Security / Cyber datasets (MITRE ATT&CK, CVE data) etc

Use FAISS for Fast retrieval
***Output: Havent decided yet***

- ### Guard output (Sensitivity of language checks)
Run a safety classifier on output
Either Reject / Accept / Admit Ignorance

**Output: append tag to result**

- ### Log Results
***LOG EVERYTHING***

# Metric Calculation
***Probably just use the same thingy that the other paper used cuz it looks good enough***


