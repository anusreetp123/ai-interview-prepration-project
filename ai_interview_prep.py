import streamlit as st
import os
import re
import json
import anthropic


MODEL = "claude-sonnet-4-6"


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

    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        st.error("ANTHROPIC_API_KEY is missing")
        st.stop()

    return anthropic.Anthropic(api_key=api_key)



def ask_claude(client, prompt):

    response = client.messages.create(
        model=MODEL,
        max_tokens=800,
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    return "".join(
        block.text 
        for block in response.content 
        if block.type=="text"
    )



def extract_json(text):

    cleaned = re.sub(
        r"```json|```",
        "",
        text
    ).strip()


    start=min(
        [
            i for i in [
                cleaned.find("{"),
                cleaned.find("[")
            ]
            if i!=-1
        ]
    )

    end=max(
        cleaned.rfind("}"),
        cleaned.rfind("]")
    )

    return json.loads(
        cleaned[start:end+1]
    )



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


    response=ask_claude(client,prompt)

    return extract_json(response)



def evaluate_answer(client, role, question, answer):

    prompt=f"""
You are an expert interview evaluator.

Role:
{role}

Question:
{question}

Candidate Answer:
{answer}


Return JSON:

{{
"score":8,
"strengths":[""],
"improvements":[""],
"model_answer_tip":""
}}

"""


    response=ask_claude(client,prompt)

    return extract_json(response)



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