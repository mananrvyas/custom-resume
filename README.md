# Custom Resume Generator

This project is a Streamlit-based web application that helps users generate customized resumes and cover letters using AI models. It allows users to input their existing resume in LaTeX format, job descriptions, and personal details, then uses AI to tailor the resume and create a matching cover letter.

## Features

- LaTeX resume editor and PDF previewer
- AI-powered resume customization
- Cover letter generation
- Interactive chat interface to refine and edit cover letters with AI assistance
- Support for OpenAI models (Claude support coming soon)
- Exportable cover letter as PDF

## Installation

1. Clone the repository:

```
git clone https://github.com/mananrvyas/custom-resume.git
cd custom-resume
```

2. Install the required dependencies:

```
pip install -r requirements.txt
```

3.  Install LaTeX:
- For macOS: Download and install [MacTeX](https://tug.org/mactex/mactex-download.html) from their official website
- For Windows: Install a LaTeX distribution like MiKTeX or TeX Live

## Configuration

1. Create a `.env` file in the project root directory with the following variables:

```
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
INITIAL_SYSTEM_PROMPT="Create an Evidence-Based Resume using the WHO Method
Choose relevant experiences you would like to include on your resume (job, internship, volunteer activity,
club membership, course projects, study abroad, service learning, etc.).
Choose tasks from each experience relevant to the job that can demonstrate skills and contributions.
Use the WHO method to evaluate tasks and experiences to help you write evidence-based statements.
W = What did you do (tasks/projects)
H = How did you do the work? (skills, strategies, methods, tools, techniques, attitudes)
O = Outcomes associated with the work (results, impact, contribution, intention, scope"
INITIAL_COVER_LETTER_PROMPT="The cover letter should not be robotic. and it should not start with something like 'hope this finds you well' or anything generic. Make sure to include something about the company which can make the letter stand out."
```

2. Create a file named `resume.tex` in the project root directory and paste your LaTeX resume code into it.

## Usage

1. Run the Streamlit app:

```
streamlit run main.py
```

2. Open your web browser and navigate to the URL provided by Streamlit (usually `http://localhost:8501`).

3. Use the interface to:
- Edit your LaTeX resume
- Enter job details and personal information
- Generate a customized resume and cover letter
- Preview and download the results

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

© 2024, All Rights Reserved.
