import os
import google.generativeai as genai

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
for m in genai.list_models():
    if "gemini" in m.name:
        print(m.name)
