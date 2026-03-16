from openai import OpenAI
from string import Template

lines = "----------------------------------------\n"
client = OpenAI(
        base_url="http://localhost:1234/v1",
        api_key="lmstudio"
    )
WRAPPERS = [

Template("""
Solve the following task step by step.

Return exactly:

COT:
1.
2.
3.

FINAL: <answer>

Task:
$task
"""),

Template("""
Think step by step and output JSON.

{
 "cot": ["step1", "step2", "step3"],
 "answer": "final_answer"
}

Task:
$task
"""),

Template("""
Solve the task.

Return strictly in this format:

T1:
T2:
T3:
ANS:

Task:
$task
"""),

Template("""
Work through the reasoning.

Output exactly:

[THOUGHT]
step

[THOUGHT]
step

[THOUGHT]
step

[FINAL]
answer

Task:
$task
""")

]
def see_wrapper(wrapper_idx:int,task:str|None = r'I need to solve this math problem: (23+340)/7')->str:
  '''
  function to see the result of the LLM given by a specific wrapper index in the above list WRAPPERS.
  you can give your own task or deafult task is a math problem.
  Giving the argument for wrapper index is compulsory.
  The result will be stored in a file responses.txt in the same folder.
  The format for the result file will be:
  prompt
  -------------------------
  response
  '''
  prompt = WRAPPERS[wrapper_idx].substitute(task=task)
  response = client.chat.completions.create(
    model="meta-llama-3-8b-instruct",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=500
  )
  with open(f"responses.txt", "w") as f:
    f.write(prompt+ '\n')
    f.write(lines)
    f.write(response.choices[0].message.content) 
  return response.choices[0].message.content
def test_cot(wrapper_idx:int,task:str|None = r'I need to solve this math problem: (23+340)/7')->bool:
  '''
  '''
  system_prompt = '''You are a reasoning verifier.

Your job is to evaluate a chain-of-thought (COT) and determine whether the reasoning correctly leads to the final answer.

Rules:
- Do not generate a new solution unless necessary.
- Check each step for logical consistency.
- Identify incorrect or unsupported steps.
- Decide whether the final answer is valid.

Output strictly in this format:

VERDICT: VALID | INVALID
ERROR_STEP: <step number or NONE>
EXPLANATION: <short explanation>
'''
  prompt = see_wrapper(wrapper_idx,task)
  response = client.chat.completions.create(
    model="phi-3-mini-4k-instruct",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=500
  )
  output = str(response.choices[0].message.content) 
  print(output)
  if 'VALID' in output:
    return True
  else:
    return False

if __name__ == "__main__":
    #see_wrapper(2)
    print(test_cot(2))

    

    