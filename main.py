import json
import time
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
from fpdf import FPDF
import random
import tempfile

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
        # print("No Claude API key found in environment variables.")
        st.session_state.claude_api_key = ""
if "claude_model_name" not in st.session_state:
    st.session_state.claude_model_name = ""
if "openai_api_key" not in st.session_state:
    try:
        st.session_state.openai_api_key = os.environ["OPENAI_API_KEY"]
    except KeyError:
        st.session_state.openai_api_key = ""
        # print("No OpenAI API key found in environment variables.")
if "openai_model_name" not in st.session_state:
    st.session_state.openai_model_name = ""
if "ai_model" not in st.session_state:
    st.session_state.ai_model = "OpenAI"

INITIAL_SYSTEM_PROMPT = os.environ["INITIAL_SYSTEM_PROMPT"]

if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = INITIAL_SYSTEM_PROMPT

INITIAL_COVER_LETTER_PROMPT = os.environ["INITIAL_COVER_LETTER_PROMPT"]

if "cover_letter_system_prompt" not in st.session_state:
    st.session_state.cover_letter_system_prompt = INITIAL_COVER_LETTER_PROMPT

if "cover_letter" not in st.session_state:
    st.session_state.cover_letter = "Cover letter will be generated here."

if "job_description" not in st.session_state:
    st.session_state.job_description = ""
if "job_title" not in st.session_state:
    st.session_state.job_title = ""
if "resume" not in st.session_state:
    try:
        with open("resume.tex", 'r') as file:
            latex_code = file.read()
        st.session_state.resume = latex_code
    except FileNotFoundError:
        st.session_state.resume = "Please create a .tex file, and paste your resume in that"

if "cover_letter_file_name" not in st.session_state:
    st.session_state.cover_letter_file_name = "cover_letter"

SYSTEM_PROMPT_START = ("You are an expert resume writer and job application specialist. "
                       "Your task is to analyze the provided job posting and full resume, "
                       "then create a tailored resume and cover letter. Output your response in "
                       "JSON format with a 'resume' key containing latex code of new resume content, and "
                       "a 'cover_letter' key containing the generated cover letter. Ensure the JSON is"
                       " properly formatted and escaped. No need to include ```json before the start"
                       " of JSON string. You are NOT allowed to change the format of the resume in "
                       "any way unless explicitly stated by the user/job posting. You must provide a "
                       "complete resume in LaTeX format. The cover letter should be plain text."
                       "REMEMBER: YOU SHOULD PROVIDE THE COMPLETE UPDATED CODE OF RESUME IN LATEX. \n\n"
                       "Here are the custom instructions by the user: \n\n"
                       )

def on_generate_resume():
    current_latex = st.session_state.latex_input
    job_title = st.session_state.job_title
    job_description = st.session_state.job_description
    about_you = st.session_state.about_you

    if st.session_state.ai_model == "OpenAI":
        client = OpenAI(api_key=st.session_state.openai_api_key)
        current_latex = st.session_state.latex_input
        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT_START + st.session_state.system_prompt
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Job Title: {st.session_state.job_title}; "
                                f"Job Description:{st.session_state.job_description}; "
                                f"About User: {st.session_state.about_you}"
                                f"\n"
                                f"Resume: {current_latex}"
                    }
                ]
            }
        ]
        if st.session_state.job_title == "" or st.session_state.job_description == "":
            st.error("Please enter the job title and job description.")
        else:
            print(messages)
            st.toast("Generating resume...")
            response = client.chat.completions.create(
                model=st.session_state.openai_model_name,
                response_format={"type": "json_object"},
                messages=messages,
            )
            st.toast("Generating resume...")
            st.session_state.latex_input = json.loads(response.choices[0].message.content)['resume']
            # st.session_state.latex_input = f"Resume generated by OpenAI {random.randint(0, 1000)}"
            st.session_state.cover_letter = json.loads(response.choices[0].message.content)['cover_letter']

            # Compile the LaTeX code to PDF
            pdf_path, error = compile_latex(st.session_state.latex_input)
            if error:
                st.session_state.pdf_compilation_error = True
                st.session_state.pdf_compilation_error_message = error
            else:
                pdf_base64 = pdf_to_base64(pdf_path)
                st.session_state.pdf_display = (f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="100%" '
                                                f'height="1164" type="application/pdf"></iframe>')
                st.session_state.pdf_compiled = True
                # remove temporary files
                os.remove("temp.pdf")
                os.remove("temp.tex")
                for aux_file in ["temp.aux", "temp.log"]:
                    if os.path.exists(aux_file):
                        os.remove(aux_file)


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
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("##### LaTeX Editor")
    placeholder = ("Enter LaTeX code here. Its recommended to use add your complete resume here. Include all your "
                   "sections + all of the projects, experience. LLM will automatically use all relevant information")
    with open("resume.tex", 'r') as file:
        temp = file.read()

    st.text_area("Enter LaTeX code here", height=1164,
                 value=temp, label_visibility="collapsed", placeholder=placeholder, key="latex_input")
    with col2:
        if st.button("Compile", help="Compile the LaTeX code to PDF."):
            pdf_path, error = compile_latex(st.session_state.latex_input)
            if error:
                st.session_state.pdf_compilation_error = True
                st.session_state.pdf_compilation_error_message = error
            else:
                pdf_base64 = pdf_to_base64(pdf_path)
                st.session_state.pdf_display = (f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="100%" '
                                                f'height="1164" type="application/pdf"></iframe>')
                st.session_state.pdf_compiled = True
                # remove temporary files
                os.remove("temp.pdf")
                os.remove("temp.tex")
                for aux_file in ["temp.aux", "temp.log"]:
                    if os.path.exists(aux_file):
                        os.remove(aux_file)

with col_pdf:
    st.markdown("##### Resume Preview")
    if st.session_state.pdf_compiled is True:
        st.markdown(st.session_state.pdf_display, unsafe_allow_html=True)
    elif st.session_state.pdf_compilation_error is True:
        st.error("Error compiling LaTeX code. Please check your code and try again.")
        st.write(st.session_state.pdf_compilation_error_message)

with ((col_main)):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### Choose your AI model")
        st.session_state.ai_model = st.selectbox("Select the LLM", ["OpenAI", "Claude"], label_visibility="collapsed")
        st.markdown("##### Enter your API key")
        if st.session_state.ai_model == "OpenAI":
            st.session_state.openai_api_key = st.text_input(f"Enter your OpenAI API key here", type="password",
                                                            label_visibility="collapsed",
                                                            value=os.environ["OPENAI_API_KEY"])
        else:
            st.session_state.claude_api_key = st.text_input(f"Enter your Claude API key here", type="password"
                                                            , label_visibility="collapsed",
                                                            value=os.environ["ANTHROPIC_API_KEY"])
        st.markdown("##### Job Listing / Personal Details")
        sample_job_title = "SIG Investment / Portfolio Management Software Engineering Internship: Summer 2025"
        st.session_state.job_title = st.text_input("Enter the job title here"
                                                   , label_visibility="collapsed",
                                                   placeholder="Enter the job title here.",
                                                   value=sample_job_title)
        # st.markdown("##### Job Description")
        sample_job_description = """Overview Are you interested in our summer 2025 Software Engineering internship? Apply here, and we will reach out to you in late summer when recruiting begins. Susquehanna is looking for highly motivated full-time students for our 10-week software engineering summer internship program. As a software engineering intern, you’ll be part of a team that builds some of the most powerful trading systems in the finance industry. You will work alongside our experienced software engineers on the development, delivery, support, and enhancements of our trading systems and infrastructure. Throughout the summer, you will have the chance to work on challenging projects that will be pushed into production. You’ll also meet with senior technologists to learn about Susquehanna technology and how it impacts our trading strategies. To learn more about what it’s like to work at Susquehanna, check out our campus programs site, where you can take a virtual office tour, meet some of our employees, and learn more about our unique culture! What we're looking for Students pursuing a BS or MS in Computer Science, Computer Engineering or a similar major Intention to graduate with a bachelor’s or master’s degree within one year of the internship program Strong software development skills in any object oriented language (we use C++, Python, and C# the most) Knowledge of algorithms, data structures, and object-oriented design patterns A passion for technology and a tinkering spirit Exceptional problem solving skills This internship will be a fully in-person experience in our Philadelphia-area headquarters. INTERN PERKS: Fully-furnished housing provided for duration of internship Relaxed dress code: jeans and sneakers are the norm and shorts all summer long A 9,000 square-foot gym with cardio, cross fit, and strength machines Social events such as dinners in Philadelphia, sporting events, and more! Discounts for shopping, travel, dining, entertainment, and attractions On-site services such as dry cleaning, auto repair and detailing, barber, and ATM On-site Wellness Center staffed with full-time Nurse Practitioner Follow us on Instagram at @workingatsig to check out what our interns have been up to this summer! ABOUT SUSQUEHANNA: Susquehanna is a global quantitative trading firm founded with a growth mindset and an analytical approach to decision making. As one of the largest proprietary trading firms in the world, Susquehanna benefits the financial markets by providing liquidity and ensuring competitive prices for buyers and sellers. Susquehanna brings together the brightest minds, the best technology, and an expansive library of data to design and implement quantitative trading strategies that make us leaders in the financial markets. Beyond trading, Susquehanna is active in global private equity, institutional brokerage, sports analytics, and structured capital. Susquehanna does not accept unsolicited resumes from recruiters or search firms. Any resume or referral submitted in the absence of a signed agreement will become the property of Susquehanna and no fee will be paid."""
        st.session_state.job_description = st.text_area("Enter the job description here", height=300,
                                                        placeholder="Enter the job description here.",
                                                        label_visibility="collapsed",
                                                        value=sample_job_description)
        temp_about_you = "I was the sole tech intern at a startup for 4 months (athlytic.io)"
        st.session_state.about_you = st.text_area("About You", height=50, label_visibility="collapsed",
                                                  placeholder="Something about you that you want to include in the "
                                                              "resume/cover letter/tell the AI."
                                                  , value=temp_about_you)

        # if st.button("Generate Resume and cover letter"):
        st.button("Generate Resume and cover letter", on_click=on_generate_resume)

        if st.session_state.ai_model == "OpenAI":

            if "messages" not in st.session_state:
                st.session_state.messages = messages = [
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "text": f"You are professional resume writer and job application specialist. "
                                        f"Your current role is to create a custom cover letter for the user. "
                                        f"You can ask the user for more information. "
                                        f"You have to respond in JSON format with a 'cover_letter' key containing the "
                                        f"updated cover letter. and 'reply' key containing your response to user's reply."
                                        f"Basically its an app where users can edit cover letter side by side via GPT API\n"
                                        f"Make sure the JSON is properly formatted and escaped. No need to include "
                                        f"```json before the start of JSON string. \n"
                                        f"Cover letter should be in plain text format. start the letter with"
                                        f"something like 'dear hiring manager' or something. No need to use the standard"
                                        f"letter format. End it with Thanks,[Name] \n"
                                        f"{st.session_state.cover_letter_system_prompt} \n"
                                        f"User Resume: {st.session_state.latex_input} \n"
                                        f"Job Title: {st.session_state.job_title} \n"
                                        f"Job Description: {st.session_state.job_description} \n"
                                        f"About User: {st.session_state.about_you} \n"
                                        f"Current Cover Letter: {st.session_state.cover_letter} \n"
                            }
                        ]
                    }
                ]

            st.session_state.messages[0]["content"][0]["text"] = (f"You are professional resume writer and job application specialist. "
                                                                  f"Your current role is to create a custom cover letter for the user. "
                                        f"You can ask the user for more information. "
                                        f"You have to respond in JSON format with a 'cover_letter' key containing the "
                                        f"updated cover letter, 'reply' key containing your response to user's reply. "
                                        f"and a 'name' key containng the name of the cover letter file. Try to name it "
                                        f"in a way that it can be easily identified. (eg: coverLetterMananxCompany)"
                                        f"Basically its an app where users can edit cover letter side by side via GPT API\n"
                                        f"Make sure the JSON is properly formatted and escaped. No need to include "
                                        f"```json before the start of JSON string. \n"
                                        f"Cover letter should be in plain text format. start the letter with"
                                        f"something like 'dear hiring manager' or something. No need to use the standard"
                                        f"letter format. End it with Thanks,[Name] \n"
                                        f"{st.session_state.cover_letter_system_prompt} \n"
                                        f"User Resume: {st.session_state.latex_input} \n"
                                        f"Job Title: {st.session_state.job_title} \n"
                                        f"Job Description: {st.session_state.job_description} \n"
                                        f"About User: {st.session_state.about_you} \n"
                                        f"Current Cover Letter: {st.session_state.cover_letter} \n")



            client = OpenAI(api_key=st.session_state.openai_api_key)

            history = st.container(height=400)
            with history:
                if len(st.session_state.messages) == 1:
                    st.write("No messages yet. Here you can chat with the AI model. and it can update your cover letter"
                             "accordingly")
                for message in st.session_state.messages[1:]:
                    if message["role"] == "user":
                        with st.chat_message("user"):
                            st.write(message["content"][0]["text"])
                    if message["role"] == "assistant":
                        with st.chat_message("assistant"):
                            st.write(message["content"][0]["text"])
            # # Chatbot for cover letter generation
            prompt = st.chat_input("Write a message... (Only for cover letter generation)")
            if prompt:
                st.session_state.messages.append({"role": "user", "content": [{"type": "text", "text": prompt}]})
                # print(st.session_state.messages)
                response = client.chat.completions.create(
                    model=st.session_state.openai_model_name,
                    messages=st.session_state.messages,
                    response_format={"type": "json_object"}
                )

                st.session_state.messages.append({"role": "assistant", "content": [
                    {
                        "type": "text",
                        "text": json.loads(response.choices[0].message.content)["reply"]
                    }
                ]})
                st.session_state.cover_letter = json.loads(response.choices[0].message.content)["cover_letter"]
                st.session_state.cover_letter_file_name = json.loads(response.choices[0].message.content)["name"]
                st.rerun()

        if st.session_state.ai_model == "Claude":
            st.error("Claude is not yet supported. Please select OpenAI as the AI model. "
                     "(or contribute to the project)")
            st.stop()

    with col2:
        # Ask for model name
        st.markdown("##### Model Name (for generating cover letter)")
        if st.session_state.ai_model == "OpenAI":
            st.session_state.openai_model_name = st.selectbox("Select OpenAI model", ["gpt-3.5-turbo-1106", "gpt-4o",
                                                                                      "gpt-4-turbo", "gpt-4"]
                                                              , label_visibility="collapsed")
        else:
            st.session_state.claude_model_name = st.selectbox("Select Claude model", ["claude-3-5-sonnet-20240620",
                                                                                      "claude-3-haiku-20240307",
                                                                                      "claude-3-opus-20240229"]
                                                              , label_visibility="collapsed")
        st.markdown("##### Resume System Prompt (Job details + old resume will be sent automatically)")
        # st.write("Enter the system prompt here. This is the text that the AI model will use to generate the resume.")
        st.session_state.system_prompt = st.text_area(label="System Prompt", height=275, label_visibility="collapsed"
                                                      , value=INITIAL_SYSTEM_PROMPT)
        st.markdown('##### Cover Letter System Prompt (Job details + new resume will be sent automatically)')
        st.session_state.cover_letter_system_prompt = st.text_area(label="Cover Letter System Prompt", height=275,
                                                                   label_visibility="collapsed"
                                                                   , value=INITIAL_COVER_LETTER_PROMPT)
        st.markdown("##### Cover Letter")
        st.text_area("Cover Letter", height=360, label_visibility="collapsed",
                     placeholder="Cover Letter will be generated here.",
                     value=st.session_state.cover_letter)
        # if st.button("Export Cover letter as PDF"):
        class PDF(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 12)
        file_name = st.session_state.cover_letter_file_name
        cover_letter_text = st.session_state.cover_letter
        cover_letter_text = cover_letter_text.replace("’", "'")

        # if cover_letter_text != "Cover letter will be generated here.":
        pdf = PDF()
        pdf.add_page()

        pdf.set_font("Times", size=11)
        pdf.set_left_margin(20)
        pdf.set_right_margin(20)
        pdf.set_top_margin(20)
        pdf.set_auto_page_break(auto=True, margin=20)

        paragraphs = cover_letter_text.split('\n\n')

        for paragraph in paragraphs:
            pdf.multi_cell(0, 5, paragraph.strip(), align='L')
            pdf.ln(5)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf.output(tmpfile.name)

        with open(tmpfile.name, "rb") as f:
            pdf_data = f.read()

        os.unlink(tmpfile.name)

        st.download_button(
            label="Download Cover Letter",
            data=pdf_data,
            file_name=f"{file_name}.pdf",
            mime="application/pdf"
        )

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
     .stApp { bottom: 30px; }
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
