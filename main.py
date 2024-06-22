import streamlit as st
from pylatexenc.latex2text import LatexNodes2Text
import subprocess
import base64
import os
from openai import OpenAI
from os.path import join, dirname
from dotenv import load_dotenv
import anthropic
# for the footer
from htbuilder import HtmlElement, div, ul, li, br, hr, a, p, img, styles, classes, fonts
from htbuilder.units import percent, px
from htbuilder.funcs import rgba, rgb

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Set the page layout to wide
st.set_page_config(layout="wide")

# initialize session states
if "pdf_compiled" not in st.session_state:
    st.session_state.pdf_compiled = False
if "pdf_compilation_error" not in st.session_state:
    st.session_state.pdf_compilation_error = False
if "claude_api_key" not in st.session_state:
    try:
        st.session_state.claude_api_key = os.environ["ANTHROPIC_API_KEY"]
    except KeyError:
        print("No Claude API key found in environment variables.")
        st.session_state.claude_api_key = ""
if "claude_model_name" not in st.session_state:
    st.session_state.claude_model_name = ""
if "openai_api_key" not in st.session_state:
    try:
        st.session_state.openai_api_key = os.environ["OPENAI_API_KEY"]
    except KeyError:
        st.session_state.openai_api_key = ""
if "openai_model_name" not in st.session_state:
    st.session_state.openai_model_name = ""
if "ai_model" not in st.session_state:
    st.session_state.ai_model = "OpenAI"
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = ("You are a large language model AI. Update the resume according to the job"
                                      " description.")
if "job_description" not in st.session_state:
    st.session_state.job_description = ""
if "job_title" not in st.session_state:
    st.session_state.job_title = ""
if "messages" not in st.session_state:
    st.session_state.messages = messages = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": "you are a very helpful AI assistant"
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "hello there msiter\n"
                }
            ]
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "Hello! How can I assist you today?"
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "nothing much just testing out\n"
                }
            ]
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "No problem at all! Feel free to ask me anything or let me know if there's something "
                            "specific you'd like help with. Enjoy your day!"
                }
            ]
        }
    ]


def compile_latex(latex_code):
    with open("temp.tex", "w") as f:
        f.write(latex_code)

    # Compile the .tex file to .pdf
    result = subprocess.run(["pdflatex", "-interaction=nonstopmode", "temp.tex"], capture_output=True, text=True)

    # Read the log file
    if os.path.exists("temp.log"):
        with open("temp.log", "r") as log_file:
            log_content = log_file.read()
    else:
        log_content = "Log file not found."

    if result.returncode != 0:
        st.session_state.pdf_compiled = False
        return None, log_content
    else:
        return "temp.pdf", None


def pdf_to_base64(pdf_path):
    with open(pdf_path, "rb") as pdf_file:
        return base64.b64encode(pdf_file.read()).decode('utf-8')


# Main page layout
col_latex, col_main, col_pdf = st.columns([1, 2, 1])

with col_latex:
    col1, col2 = st.columns([8, 1])
    with col1:
        st.markdown("##### LaTeX Editor")

    latex_code = st.text_area("Enter LaTeX code here", height=1164,
                              value=r'''\documentclass{article}\begin{document}Hello\end{document}''',
                              label_visibility="collapsed")
    with col2:
        if st.button("Compile", help="Compile the LaTeX code to PDF."):
            pdf_path, error = compile_latex(latex_code)
            if error:
                st.session_state.pdf_compilation_error = True
                st.session_state.pdf_compilation_error_message = error
            else:
                pdf_base64 = pdf_to_base64(pdf_path)
                st.session_state.pdf_display = (f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="900" '
                                                f'height="1164" type="application/pdf"></iframe>')
                st.session_state.pdf_compiled = True
                # remove temporary files
                os.remove("temp.pdf")
                os.remove("temp.tex")
                for aux_file in ["temp.aux", "temp.log"]:
                    if os.path.exists(aux_file):
                        os.remove(aux_file)

with col_pdf:
    st.markdown("##### PDF Preview")
    if st.session_state.pdf_compiled is True:
        st.markdown(st.session_state.pdf_display, unsafe_allow_html=True)
    elif st.session_state.pdf_compilation_error is True:
        st.error("Error compiling LaTeX code. Please check your code and try again.")
        st.write(st.session_state.pdf_compilation_error_message)

with (col_main):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### Choose your AI model")
        st.session_state.ai_model = st.selectbox("Select the LLM", ["OpenAI", "Claude"], label_visibility="collapsed")
        st.markdown("##### Enter your API key")
        if st.session_state.ai_model == "OpenAI":
            st.session_state.openai_api_key = st.text_input(f"Enter your OpenAI API key here", type="password",
                                                            value=st.session_state.openai_api_key,
                                                            label_visibility="collapsed")
        else:
            st.session_state.claude_api_key = st.text_input(f"Enter your Claude API key here", type="password",
                                                            value=st.session_state.claude_api_key
                                                            , label_visibility="collapsed")
        st.markdown("##### Job Listing")
        st.session_state.job_title = st.text_input("Enter the job title here", value=st.session_state.job_title
                                                   , label_visibility="collapsed",
                                                   placeholder="Enter the job title here.")
        # st.markdown("##### Job Description")
        st.session_state.job_description = st.text_area("Enter the job description here", height=400,
                                                        value=st.session_state.job_description,
                                                        placeholder="Enter the job description here.",
                                                        label_visibility="collapsed")
        # # Chatbot for cover letter
        if st.button("Generate Resume"):
            st.toast("Generating resume...")
        if st.session_state.ai_model == "OpenAI":
            client = OpenAI(api_key=st.session_state.openai_api_key)

            history = st.container(height=400)
            with history:
                for message in st.session_state.messages[1:]:
                    if message["role"] == "user":
                        with st.chat_message("user"):
                            st.write(message["content"][0]["text"])
                    if message["role"] == "assistant":
                        with st.chat_message("assistant"):
                            st.write(message["content"][0]["text"])

            prompt = st.chat_input("Write a message...")
            # if prompt:
            #     st.session_state.messages.append({"role": "user", "content": [{"type": "text", "text": prompt}]})
            #     response = client.chat.completions.create(
            #         model=st.session_state.openai_model_name,
            #         messages=st.session_state.messages,
            #     )
            #     st.session_state.messages.append({"role": "assistant", "content": response["choices"][0]["message"]})
            #     print(response["choices"][0]["message"])

    with col2:
        # Ask for model name
        st.markdown("##### Model Name")
        if st.session_state.ai_model == "OpenAI":
            st.session_state.openai_model_name = st.selectbox("Select OpenAI model", ["gpt-3.5-turbo-1106", "gpt-4o",
                                                                                      "gpt-4-turbo", "gpt-4"]
                                                              , label_visibility="collapsed")
        else:
            st.session_state.claude_model_name = st.selectbox("Select Claude model", ["claude-3-5-sonnet-20240620",
                                                                                      "claude-3-haiku-20240307",
                                                                                      "claude-3-opus-20240229"]
                                                              , label_visibility="collapsed")
        st.markdown("##### System Prompt")
        # st.write("Enter the system prompt here. This is the text that the AI model will use to generate the resume.")
        st.session_state.system_prompt = st.text_area(label="System Prompt", height=550, label_visibility="collapsed"
                                                      , value=st.session_state.system_prompt)
        st.markdown("##### Cover Letter")
        st.session_state.cover_letter = st.text_area("Cover Letter", height=415, label_visibility="collapsed",
                                                     value="Cover Letter will be generated here.")
        if st.button("Export Cover letter as PDF"):
            st.toast("Generating cover letter...")

############################################
# ########### FOOTER #######################
############################################

def image(src_as_string, **style):
    return img(src=src_as_string, style=styles(**style))


def link(link, text, **style):
    return a(_href=link, _target="_blank", style=styles(**style))(text)


def layout(*args):
    style = """
    <style>
      # MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
     .stApp { bottom: 70px; }
    </style>
    """

    style_div = styles(
        position="fixed",
        left=0,
        bottom=0,
        margin=px(0, 0, 0, 0),
        width=percent(100),
        color="white",
        text_align="center",
        height="auto",
        opacity=1
    )

    style_hr = styles(
        display="block",
        margin=px("auto"),
        border_style="inset",
        border_width=px(2)
    )

    body = p()
    foot = div(
        style=style_div
    )(
        hr(
            style=style_hr
        ),
        body
    )

    st.markdown(style, unsafe_allow_html=True)

    for arg in args:
        if isinstance(arg, str):
            body(arg)

        elif isinstance(arg, HtmlElement):
            body(arg)

    st.markdown(str(foot), unsafe_allow_html=True)


def footer():
    myargs = [
        "Made with  ❤ by ",
        link("https://mananvyas.in", "mananvyas.in"), br(),
        "© 2024, All Rights Reserved."
    ]
    layout(*myargs)


footer()
