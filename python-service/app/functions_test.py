from messageHandler import MessageHandler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import gspread
import os
import json
#import nltk
import difflib
import spacy
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk import pos_tag
from nltk.stem import WordNetLemmatizer

# Descargar recursos necesarios de NLTK
# nltk.download()
# nltk.download("punkt")  # Para tokenización
# nltk.download("punkt_tab")  # Para tokenización
# nltk.download("averaged_perceptron_tagger")  # Para POS tagging
# nltk.download("averaged_perceptron_tagger_eng")  # Para POS tagging
# nltk.download("wordnet")  # Para lematización
# nltk.download("stopwords")  # Para eliminar stopwords


################################Esta es mi estructura basica pregunta-respuesta
url = 'https://docs.google.com/spreadsheets/d/1zfaBTOvK02q7sxSLK3-tq4zgJxmmUvhGePA9Y32Asm8/edit?hl=es&gid=0#gid=0'

mHandler = MessageHandler()

mHandler.qa_to_json_excel_url(url)

mHandler.set_qa_pairs_json()

ans = mHandler.get_answer('taco')

print(ans)
#####################################################3

#qa_pairs = {}

# qa_pairs = {
#     "¿Qué es Python?": "Python es un lenguaje de programación.",
#     "¿Cómo instalo Python?": "Puedes descargarlo desde python.org.",
#     "¿Qué es un loop?": "Un loop es una estructura de control que repite un bloque de código."
# }

# # Cargar el modelo de lenguaje en español
# nlp = spacy.load("es_core_news_sm")

# def preprocess_text(question):
#     doc = nlp(question)
#     # Extraer palabras clave (sustantivos y verbos)
#     keywords = [token.lemma_ for token in doc if token.pos_ in ["NOUN", "VERB"]]
#     return " ".join(keywords)

# def get_answer_with_difflib(question):
#     closest_match = difflib.get_close_matches(question, qa_pairs.keys(), n=1, cutoff=0.6)
#     if closest_match:
#         return qa_pairs[closest_match[0]]
#     return None

# # Convertir preguntas a vectores TF-IDF
# vectorizer = TfidfVectorizer()
# questions = list(qa_pairs.keys())
# tfidf_matrix = vectorizer.fit_transform(questions)

# def get_answer_with_cosine_similarity(question):
#     # Preprocesar la pregunta
#     processed_question = preprocess_text(question)
#     # Convertir a vector TF-IDF
#     question_vector = vectorizer.transform([processed_question])
#     # Calcular similitud de coseno
#     similarities = cosine_similarity(question_vector, tfidf_matrix)
#     # Encontrar la pregunta más similar
#     most_similar_index = similarities.argmax()
#     if similarities[0, most_similar_index] > 0.5:  # Umbral de similitud
#         return qa_pairs[questions[most_similar_index]]
#     return None

# def get_answer(question):
#     # Primero intenta con Difflib
#     answer = get_answer_with_difflib(question)
#     if answer:
#         return answer

#     # Si no hay coincidencia, usa similitud de coseno con preprocesamiento
#     answer = get_answer_with_cosine_similarity(question)
#     if answer:
#         return answer

#     # Si no se encuentra una respuesta
#     return "No sé la respuesta a eso."


# print(get_answer("Que es Piton?"))  # Output: Python es un lenguaje de programación.
# #print(get_answer("Como puedo descargar Python?"))  # Output: Puedes descargarlo desde python.org.
# print(get_answer("Como puedo descargo Python?"))  # Output: Puedes descargarlo desde python.org.
# print(get_answer("Qué es un bucle?"))  # Output: Un loop es una estructura de control que repite un bloque de código.

# # Inicializar el lematizador
# lemmatizer = WordNetLemmatizer()

# # Definir una función para preprocesar el texto
# def preprocess_text(question):
#     # Tokenizar la pregunta
#     tokens = word_tokenize(question, language="spanish")
    
#     # Etiquetar partes del discurso (POS tagging)
#     tagged_tokens = pos_tag(tokens)
    
#     # Filtrar sustantivos (NN) y verbos (VB)
#     keywords = []
#     for word, tag in tagged_tokens:
#         if tag.startswith("NN"):  # Sustantivos
#             keywords.append(lemmatizer.lemmatize(word, pos="n"))
#         elif tag.startswith("VB"):  # Verbos
#             keywords.append(lemmatizer.lemmatize(word, pos="v"))
    
#     # Unir las palabras clave en un solo string
#     return " ".join(keywords)

# # Probar la función
# question = "¿Cómo puedo instalar Python en mi computadora?"
# processed_text = preprocess_text(question)
# print(processed_text)



# #test_message = "ans1, resp1, ans2, resp2, ans3, resp3, ans4, resp4"

# #print(mHandler.get_generic_answer_response("ans1"))

# api_key_google_sheets = 'AIzaSyAMiaX8o1myMZiZFacs8_Ckl2Dyv98Ff4U'

# gc = gspread.api_key(api_key_google_sheets)

# qa_dict = {}

# n_qa_dict = {}

# def extract_qa_pairs_excel_url(url):

#     sht = gc.open_by_url(url)
#     worksheets = sht.worksheets()
#     # Solo tomamos la primera hoja
#     sheet = worksheets[0]
#     sheet_data = sheet.get_all_values()
#     sheets_data_list = [row[:2] for row in  sheet_data]

#     for element in sheets_data_list:
#         qa_dict[element[0]] = element[1]

#     os.makedirs('./python-service/qa-files/', exist_ok=True)

#     with open('./python-service/qa-files/qa.json','w', encoding='utf-8') as f:
#         json.dump(qa_dict, f, ensure_ascii=False, indent=4)

#     # Cargar el archivo JSON
#     with open('./python-service/qa-files/qa.json', 'r', encoding='utf-8') as f:
#         return json.load(f)

    # for sheet in worksheets:
    #     sheets_data = sheet.get_all_values()
    #     sheets_data_list = [row[:2] for row in  sheets_data]

    #     #sheets_data.append(sheet.get_all_values())
    #     print(sheets_data_list)
    # #return sheets_data

# sheets_data = extract_qa_pairs_excel_url(url)
#n_qa_dict = extract_qa_pairs_excel_url(url)

#print(qa_dict)

#print(n_qa_dict)


# mHandler.set_qa_pairs_excel(sheets_data[0])

# print(mHandler.get_qa_pairs("tacos"))
# print(mHandler.get_qa_pairs("taquitos"))






#sh = gc.open('My poor gym results')

#sht1 = gc.open_by_key("1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms")

#print(len(row))
#worksheets_1 = sht1.worksheets() 
# for sheet in worksheets_1:
#     list_of_lists_1 = sheet.get_all_values()
#     print(list_of_lists_1)

#print(list_of_lists_2)

#all_values_1 = sht1.get_all_values()
#all_values_2 = sht2.get_all_values()

#print(sh.sheet1.get('A1'))
#print(sht1.sheet1.get('A1'))
#print(sht2.sheet1.get('A1'))

#print(worksheets_1)
#print(worksheets_2)

# gc = gspread.service_account()

# # Open a sheet from a spreadsheet in one go
# wks = gc.open("Where is the money Lebowski?").sheet1

# # Update a range of cells using the top left corner address
# wks.update([[1, 2], [3, 4]], "A1")

# # Or update a single cell
# wks.update_acell("B42", "it's down there somewhere, let me take another look.")

# # Format the header
# wks.format('A1:B1', {'textFormat': {'bold': True}})


# import difflib

# class MyClass:
#     def __init__(self):
#         # Diccionario con funciones y valores
#         self.qa_pairs = {
#             'sumar': (self.suma, True),  # Requiere parámetros
#             'restar': (self.resta, True),  # Requiere parámetros
#             'saludo': (self.saludar, False),  # No requiere parámetros
#             'hola': ('adios', False)  # Valor simple, no es función
#         }

#     def suma(self, a, b):
#         return a + b
    
#     def resta(self, a, b):
#         return a - b

#     def saludar(self):
#         return "Hola, ¿cómo estás?"
    
#     def get_answer_with_difflib(self, question, requester_id, *args):
#         closest_match = difflib.get_close_matches(question, self.qa_pairs.keys(), n=1, cutoff=0.6)
        
#         if closest_match:
#             value = self.qa_pairs[closest_match[0]]
#             # Verificar si el valor es una función y si es callable
#             if callable(value[0]):
#                 if value[1]:  # Si requiere parámetros
#                     return value[0](*args)  # Llamar con los parámetros
#                 else:
#                     return value[0]()  # Llamar sin parámetros si no hay
#             else:
#                 return value[0]  # Retornar el valor directo si no es una función

#         else:
#             return None

# # Crear una instancia
# my_instance = MyClass()

# # Ejemplo de uso
# print(my_instance.get_answer_with_difflib('sumar', 123, 5, 3))  # Llamará a suma(5, 3)
# print(my_instance.get_answer_with_difflib('restar', 123, 10, 4))  # Llamará a resta(10, 4)
# print(my_instance.get_answer_with_difflib('saludo', 123))  # Llamará a saludar() sin parámetros
# print(my_instance.get_answer_with_difflib('hola', 123))  # Retornará 'adios'
