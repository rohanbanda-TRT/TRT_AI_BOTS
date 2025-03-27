GRAMMAR_PROMPT = """
Act as a Spoken English Teacher and Improver and your task is to thoroughly review the given text and identify any grammar mistakes, typos, and factual errors present within it. Analyze the content in detail and provide a comprehensive report with the following:

=> Grammar and Typo Identification:
- Identify any grammatical errors, such as incorrect sentence structure, subject-verb agreement issues, improper use of punctuation, etc.
- Detect any typographical errors, including misspellings, incorrect capitalization, and other typing mistakes.
- Provide the correct grammar or spelling for each identified issue.
- Strictly specify the type of grammatical error for each sentence, such as subject-verb agreement, pronoun usage, tense,misspellings, incorrect capitalization, and other typing mistakes. etc.
- Scrutinize the content for any factual inaccuracies, such as incorrect dates, names, statistics, or other verifiable information.

Your analysis should be thorough, objective, and demonstrate a strong command of grammar, spelling, and fact-checking principles. The goal is to help the user enhance the overall quality, clarity, and reliability of the provided content through your detailed feedback and recommendations.

Text: {context}
"""

PLAGIARISM_PROMPT = """
Your task is to perform a comprehensive plagiarism and AI-generated content detection check on the given text or document. Analyze the content and compare it against a large corpus of online sources, academic publications, and other relevant databases to identify any instances of plagiarism or unattributed use of external material. 

Provide a detailed report that includes the following:

1. Plagiarism detection score: A numerical score (e.g., 0-100%) indicating the overall likelihood of plagiarism in the provided content.
2. Identified plagiarized sections: Highlight any specific passages or sentences that appear to be copied or closely paraphrased from other sources, along with the corresponding source information.

4. Originality assessment: Evaluate the overall originality and uniqueness of the content, considering the extent of any identified plagiarism and AI-generated content.

Your analysis should be thorough, objective, and adhere to best practices in plagiarism detection and academic integrity. Provide clear and actionable insights to help the user address any plagiarism or AI-generated content concerns.

Text: {context}
"""
VOICE_CONVERSION_PROMPT = """
Your task is to convert the provided text from active voice to passive voice, or from passive voice to active voice, as specified by the user.

The conversion should adhere to the following standards:

1. Voice Conversion:
   - If the user requests an active to passive conversion, transform all active voice sentences into their corresponding passive voice counterparts.
   - If the user requests a passive to active conversion, transform all passive voice sentences into their corresponding active voice counterparts.

2. Sentence Structure Preservation:
   - Maintain the overall sentence structure and meaning during the voice conversion process.
   - Ensure that the converted sentences are grammatically correct and coherent within the context of the text or document.

3. Pronoun and Subject Adjustments:
   - Modify the pronouns and subjects as necessary to align with the new voice structure.
   - For active to passive conversion, the subject of the active sentence becomes the object in the passive sentence.
   - For passive to active conversion, the object of the passive sentence becomes the subject in the active sentence.

4. Verb Tense and Form Adjustments:
   - Adjust the verb tenses and forms to match the new voice structure.
   - For active to passive conversion, use the appropriate form of the verb "to be" along with the past participle of the main verb.
   - For passive to active conversion, use the appropriate active verb form.

5. Formatting and Consistency:
   - Preserve the original formatting, layout, and structure of the text or document.
   - Ensure that the converted text maintains a consistent voice throughout the document.
                                                                                                                                                            Text: {context}
Voice Conversion: {voice_conversion}
"""

THEME_PROMPT = """
Analyze the given text and provide a concise summary of the main theme or themes. The theme should capture the central idea, message, or underlying meaning conveyed in the content.

Please provide your response in the following format:

The theme of the content is [theme]. [Explanation of the theme and how it is reflected in the text.]

Text: {context}
"""

STYLE_SUGGESTIONS_PROMPT = """
Analyze the given text and provide the  improved text . Your improved text  should focus on the following aspects:
1.Sentence Structure:
   -Identify opportunities to vary sentence length and structure for better flow and readability.
   -Suggest ways to improve sentence clarity and conciseness.
2.Tone and Voice:
   -Evaluate the overall tone and voice of the writing.
   -Provide recommendations to enhance the tone, such as making it more formal, informal, persuasive, or engaging.
3.Vocabulary:
   -Identify areas where more precise or vivid language could be used.
   -Suggest alternative words or phrases to improve the vocabulary and word choice.
4.Overall Readability:
   -Assess the overall readability and clarity of the text.
   -Provide general suggestions to improve the overall quality and effectiveness of the writing.

Please provide improved text in a clear and structured manner and the explanation of changes you have done for better understanding in the text by comparing it with the original text.
Text: {context}
"""

READABILITY_PROMPT = """
Analyze the given text and provide a comprehensive readability assessment with the following:
1.Readability Metrics:
   -Determine the overall readability level (easy, moderate, or hard) based on the Flesch-Kincaid Reading Ease score, Gunning Fog Index, and SMOG Index. Show the level of readability by easy, moderate, or hard depending on the score. Don't show Flesch-Kincaid Reading Ease score, Gunning Fog Index, and SMOG Index values.Just show the level of readability.
2.Readability Evaluation:
   -Assess the overall readability of the text, considering the target audience and purpose.
   -Identify areas where the text could be improved to enhance clarity and comprehension.
3.Alternative Text:
   -If the readability level is moderate or hard then only suggest an alternative version of the text that is more readable and accessible to the target audience. Ensure that the meaning of the original text is intact in the alternative version.If the readability level is easy don't provide alternative text.

Text: {context}
"""

AI_DETECTION_PROMPT = """
Your task is to assess the likelihood of the given text being generated by an AI language model, such as GPT. Analyze the content and provide the following:

1. AI-generated content detection score: A numerical score (e.g., 0-100%) indicating the likelihood of the content being generated by an AI language model.
2. AI-generated content assessment: Clearly state whether the content is likely to be AI-generated or not, based on the detection score.

Your analysis should be thorough, objective, and based on best practices in AI detection. The goal is to help the user understand the potential AI-generated nature of the content.

Text: {context}
"""

ESSAY_GENERATION_PROMPT = """
Your task is to generate an essay based on the provided topic and requirements.
Topic: {context}
Word Count: {word_count}
Role: {role}
The essay should:
1.Highlight the specific academic programs, courses, and faculty that you are interested in and explain how they will contribute to your intellectual growth and future career aspirations.
2.Discuss the extracurricular activities, clubs, and student organizations that you plan to engage with and how these will enhance your overall university experience and leadership development.
3.Describe the internships, research opportunities, and career services that the university provides, and explain how you will leverage these to gain practical experience and advance your professional goals.
4.Demonstrate a clear understanding of the university's mission, values, and areas of distinction, and articulate how your background, skills, and interests are a strong fit for the institution.
5.Convey your enthusiasm and commitment to contributing to the university community and achieving your personal and professional objectives.

Please generate the essay in a clear and coherent manner, adhering to the specified word count and addressing the key points outlined in the essay guidelines. 
"""

ESSAY_EVALUATION_PROMPT = """
Your task is to evaluate the provided essay based on the essay guidelines and the user's academic and professional achievements.
This prompt calls for a thoughtful exploration of the university's academic offerings, extracurricular activities, and professional development opportunities. The essay should demonstrate the applicant's thorough research into the university and how its resources align with their educational and career goals.
The essay guidelines should:
1.Highlight the specific academic programs, courses, and faculty that the applicant is interested in and explain how they will contribute to their intellectual growth and future career aspirations.
2.Discuss the extracurricular activities, clubs, and student organizations that the applicant plans to engage with and how these will enhance their overall university experience and leadership development.
3.Describe the internships, research opportunities, and career services that the university provides, and explain how the applicant will leverage these to gain practical experience and advance their professional goals.
4.Demonstrate a clear understanding of the university's mission, values, and areas of distinction, and articulate how the applicant's background, skills, and interests are a strong fit for the institution.
5.Convey the applicant's enthusiasm and commitment to contributing to the university community and achieving their personal and professional objectives.
Essay: {essay}
Academic Achievement: {academic_achievement}
Professional Achievement: {professional_achievement}
International Experience: {international_experience}
Degree/Program applying for: {degree_program}
Name of the college this essay is for: {college_name}

The essay should include:
- An opening that sets the tone for the essay (25 words)
- A clear description of the applicant's Short-Term Goals (STG) and Long-Term Goals (LTG) (100 words)
- Identification of skill set gaps and how the university can help bridge them (50 words)
- A detailed explanation of why the applicant is a strong fit for the college, highlighting specific resources and opportunities (200 words)
- A concise conclusion that summarizes the applicant's commitment to the university (25 words)

Provide a comment and a rating out of 5 for the essay's accuracy in addressing the key points outlined in the essay guidelines.
"""