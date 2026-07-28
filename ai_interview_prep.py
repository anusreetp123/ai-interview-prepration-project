import streamlit as st
import os
import re
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")



MODEL = "llama-3.1-8b-instant"

ROLES = [
    "Software Engineer",
    "Product Manager",
    "Data Analyst",
    "UX Designer",
    "Marketing Manager",
    "Sales Executive",
    "Customer Success",
    "Finance Analyst",
]


STYLES = {
    "Behavioral": "behavioral",
    "Technical": "technical",
    "Mixed": "mixed (behavioral and technical)"
}


def get_client():

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        st.error("Groq API key missing")
        st.stop()

    return Groq(api_key=api_key)


def ask_groq(client, prompt):

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content




def extract_json(text):

    cleaned = text.strip()

    cleaned = re.sub(
        r"```json|```",
        "",
        cleaned
    ).strip()

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError:

        start_obj = cleaned.find("{")
        end_obj = cleaned.rfind("}")

        if start_obj != -1 and end_obj != -1:
            return json.loads(
                cleaned[start_obj:end_obj+1]
            )

        st.error("Invalid JSON from AI")
        st.code(text)
        st.stop()

def generate_questions(client, role, style, count):

    prompt=f"""
You are an interview coach.

Generate {count} {style} interview questions
for a {role} position.

Return ONLY JSON array.

Example:
[
"Tell me about yourself?",
"Explain your project?"
]
"""


    response=ask_groq(client,prompt)
    return extract_json(response)




def evaluate_answer(client, role, question, answer):

    if not answer.strip():
        return {
            "score": 0,
            "strengths": [],
            "improvements": [
                "Please provide an answer to evaluate"
            ],
            "model_answer_tip": "Use the STAR method to structure your answer"
        }

    prompt=f"""
You are a strict interview evaluator.

Role:
{role}

Interview Question:
{question}

Candidate Answer:
{answer}

Scoring rules:
- Empty answer: score 0-2
- Very short answer: score 2-4
- Basic answer: score 5-7
- Strong detailed answer: score 8-10

Return ONLY valid JSON.

Format:

{{
    "score": 0,
    "strengths": [],
    "improvements": [],
    "model_answer_tip": ""
}}
"""

    response = ask_groq(client, prompt)


    feedback = extract_json(response)

    return feedback
# ---------------- STREAMLIT UI ----------------


st.title("🤖 AI Interview Preparation Coach")


role = st.selectbox(
    "Choose Interview Role",
    ROLES
)


style = st.selectbox(
    "Question Style",
    list(STYLES.keys())
)


count = st.slider(
    "Number of Questions",
    3,
    8,
    5
)



if "questions" not in st.session_state:
    st.session_state.questions=[]



if st.button("Generate Interview Questions"):

    client=get_client()

    with st.spinner("Creating questions..."):

        st.session_state.questions = generate_questions(
            client,
            role,
            STYLES[style],
            count
        )



if st.session_state.questions:

    st.subheader("Interview Questions")


    for i,q in enumerate(
        st.session_state.questions,
        1
    ):

        st.write(
            f"### Question {i}"
        )

        st.write(q)


        answer=st.text_area(
            "Your Answer",
            key=f"ans{i}"
        )


        if st.button(
            f"Evaluate Answer {i}"
        ):

            client=get_client()

            feedback=evaluate_answer(
                client,
                role,
                q,
                answer
            )


            st.success(
                f"Score: {feedback['score']}/10"
            )


            st.write(
                "### Strengths"
            )

            for x in feedback["strengths"]:
                st.write("✅",x)


            st.write(
                "### Improvements"
            )

            for x in feedback["improvements"]:
                st.write("🔹",x)


            st.write(
                "💡 Tip:",
                feedback["model_answer_tip"]
            )