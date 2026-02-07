from google.generativeai import list_models

for m in list_models():
    print(m.name, m.supported_generation_methods)