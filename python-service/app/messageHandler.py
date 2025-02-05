import re
import os
import logging
import json

#from DownloadFile import downloadFile as df
from DownloadFile import crud as cr
from urllib.parse import urlparse
from mysql.connector import Error

# For preprocessing text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import difflib
import spacy
import gspread

class MessageHandler:
    
    def __init__(self):
        self.status = 0
        #Dictionary for regular expression patterns
        self.patternsDict = {
            'updateId': r'^!updateId (\d+) (\d+)$',
            'updateNickname': r'^!updateNickname (\d+) (\w+)$',
            'updateCreditos': r'^!updateCreditos (\d+) ([0-9]{1,6})$',
            'updateRol': r'^!updateRol (\d+) (\w+)$',
            'updatePlan': r'^!updatePlan (\d+) (\w+)$',
            'updateSoporte': r'^!updateSoporte (\d+) (\w+)$',
            'updateAntiSpamTimeout': r'^!updateAntiSpamTimeout (\d+) (\d+)$',
            #'updateFullUser': r'^!updateFullUser (\d+) (\w+) ([0-9]{1,6}) (\w+) (\w+) (\w+) (\d+)$'
        }
        #Dictionary for corresponding mysql queries
        self.mysqlQueries = {
            'updateId': 'update users set id = %s where id = %s',
            'updateNickname': 'update users set nickname = %s where id = %s',
            'updateCreditos': 'update users set creditos = %s where id = %s',
            'updateRol': 'update users set rol = %s where id = %s',
            'updatePlan': 'update users set plan = %s where id = %s',
            'updateSoporte': 'update users set soporte = %s where id = %s',
            'updateAntiSpamTimeout': 'update users set anti_spam_timeout = %s where id = %s',
            #'updateFullUser': r'^!updateFullUser (\d+) (\w+) ([0-9]{1,6}) (\w+) (\w+) (\w+) (\d+)$'
        }
        self.generic_message_pair_dict = {}
        #Regex pattern to check for the webpages
        self.patternPages = r"^(https://)?(www\.)?(elements\.)?(freepik|envato)\.(com|es)(/.*)?$"
        # Cargar el modelo de lenguaje en español
        self.nlp = spacy.load("es_core_news_sm")
        # qa pairs
        self.qa_pairs = {}

        self.qa_file_route = './python-service/qa-files/qa.json'
        self.qa_directory_route = './python-service/qa-files/'

        #create the database connection
        try:
            with open('./python-service/qa-files/qa.json', 'r', encoding='utf-8') as f:
                self.qa_pairs = json.load(f)

            if not self.qa_pairs:
                self.qa_pairs = {
                    "HOla, buen día": ("Hola, buen día. ¿Cómo estas? ¿Cómo puedo ayudarte?", False),
                    "¿Dónde encuentro la política de privacidad?": ("La política de privacidad está en el pie de página.", False),
                    "!me" : (self.__handle_me, True),
                    "!buy": (self.__handle_buy, False)
                }

            # Convertir preguntas a vectores TF-IDF
            self.vectorizer = TfidfVectorizer()
            self.questions = list(self.qa_pairs.keys())
            self.tfidf_matrix = self.vectorizer.fit_transform(self.questions)

            self.api_key_google_sheets = 'AIzaSyAMiaX8o1myMZiZFacs8_Ckl2Dyv98Ff4U'
            self.gc = gspread.api_key(self.api_key_google_sheets)

            self.connection = cr.create_connection()
        except Error as e:
            if e.errno == 1045:
                logging.error("Error: Autenticación fallida. Verifica el usuario y la contraseña.")
                logging.error(f"The error '{e}' occurred")
            elif e.errno == 2003:
                logging.error("Error: No se pudo conectar al servidor MySQL. Verifica el nombre del host.")
                logging.error(f"The error '{e}' occurred")
            else:
                logging.error(f"The error '{e}' occurred")
            self.connection = None

    def process_message(self, message, requester_id, nickname):
        #verifies database connection
        self.connection = cr.reconnect(self.connection)
        # check all the update patterns to check for a coincidence
        pattern_name, pattern, matched = self.__check_pattern_match(message)
        #if message is !me process it like this

        ans = self.get_answer(message,requester_id, nickname)

        #if message == "!me": 
        #    return self.__handle_me(requester_id,nickname)
        #if message is !buy process it like this
        #elif message == "!buy":
        #    return self.__handle_buy()
        
        
        # if message matches the pattern then process it like this
        if ans is None and re.match(self.patternPages,message):
            return self.__handle_file_download_request(requester_id,message)
        elif ans is None and  pattern_name:
            return self.__handle_db_requests(requester_id, pattern_name, pattern, matched)   
        else:
            #return "Tenemos un problema, intentalo de nuevo más tarde"
            return "No sé la respuesta a eso."

    def __handle_db_requests(self,requester_id, pattern_name, pattern, matched):
        try:
            if self.connection.is_connected():
                #get the data from the one who made the request
                result = cr.fetch_data(self.connection,'select * from users where id = %s', (requester_id,))
            else:
                return "Tenemos un problema, intentalo de nuevo más tarde"
            #if role isn't from an admin
            if not result:
                return "Usuario no registrado"
            if(result[0][3]!="Admin"):#check requester role
                return "No permitido"
            #parts = checkedPatterns[0].groups()
            #get user id (phone number)
            parts = matched.groups()
            dummy_id = parts[0]
            user_id = f"{dummy_id[:2]}1{dummy_id[2:]}" if dummy_id.startswith("52") and not dummy_id.startswith("521") else dummy_id
            #On fulfilled condition get update element
            if  pattern_name != "updateFullUser":
                updateElement = parts[1]
            #get user data
            fetchedData = cr.fetch_data(self.connection,'select * from users where id = %s', (user_id,))
            #If we got a list of length 0 then user is not registered
            if(len(fetchedData)==0):
                return "Usuario no registrado"
            else:
                response_message = self.__process_update(fetchedData, updateElement, user_id, pattern_name)
                return response_message
        except Error as e:
            logging.error(f"Error ocurred: {e}")
            return "No se pudo realizar la actualización. Intentelo de nuevo más tarde."

    def __handle_file_download_request(self,requester_id, message):
        try: 
            answ = cr.fetch_data(self.connection,'select creditos from users where id = %s', (requester_id,))
            if len(answ) ==0: 
                response_message = "Pareces no estar registrado, solicita ayuda a un administrador"
            else:
                ans = int(answ[0][0])
                if ans == 0:
                    response_message = "Parece que no tienes creditos. Para informes sobre la compra de creditos escribe !buy."
                    return response_message
                else:
                    return "No hay nada aqui"
                    # result, response_message = df.get_file(message)
                    # if result:
                    #     remainingCredits = ans - 4 if ans>=4 else 0 
                    #     cr.update_data(self.connection, 'update users set creditos = %s where id=%s', (remainingCredits, requester_id))
                    #     fetchedData = cr.fetch_data(self.connection,'select * from users where id = %s', (requester_id,))
                    #     userData = fetchedData[0]
                    #     return "Muchas gracias por usar nuestro servicio\n\n Su link de descarga es: \n" + response_message + "\n\n" + f"ID → {userData[0]}\n[🗒] NICK →  {userData[1]}\n[💰] CREDITOS →  {userData[2]}\n[📈] ROL →  {userData[3]}\n[〽️] PLAN →  {userData[4]}\n[📈] SOPORTE →  {userData[5]}\n[⏱] ANTI-SPAM →  {userData[6]}"
                    # else:
                    #     return response_message
        except Error as e:
            logging.error(f"Error ocurred: {e}")
            return "No se pudo completar la acción. Intentelo de nuevo más tarde."

    def __handle_buy(self):
        return "FEChatbot\n30 creditos 50 mxn\n80 creditos 110 mxn\n180 creditos 220 mxn\n \n \nExtranjeros\n\nVenta de creditos \n+5512345678 \n+5509876543"

    def __handle_me(self,requester_id, nickname):

        if not requester_id or not nickname:
            response_message = "No tenemos la informacion necesaria para procesar tu peticion."
            return response_message

        answ = self.__register_or_check_user(requester_id, nickname)
        if len(answ)==0:
            response_message = "Parece que tenemos un problema, por favor intente nuevamente más tarde"
        else:
            response_message = f"BOT\n\n[🙎‍♂️] ID → {answ[0]}\n[🗒] NICK →  {answ[1]}\n[💰] CREDITOS →  {answ[2]}\n[📈] ROL →  {answ[3]}\n[〽️] PLAN →  {answ[4]}\n[📈] SOPORTE →  {answ[5]}\n[⏱] ANTI-SPAM →  {answ[6]} "
        return response_message

    def __process_update(self, fetched_data, update_data, user_id, pattern_name):
        if isinstance(update_data, (list, tuple)):
            # Procesando una lista de valores (for a complete user update)
            cr.update_data(
                self.connection,
                self.mysqlQueries.get(pattern_name),
                (*update_data, user_id,)
            )
            response_message = self.__get_update_message(pattern_name, user_id, update_data)
        else:
            # Procesando solo un dato
            # Problema con numeros de mexico
            if pattern_name == "updateCreditos":
                current_credits = int(fetched_data[0][2])
                amount_to_add = int(update_data)
                updated_value = current_credits + amount_to_add
            elif pattern_name == "updateAntiSpamTimeout":
                updated_value = int(update_data)
            else:
                updated_value = update_data

            cr.update_data(
                self.connection,
                self.mysqlQueries.get(pattern_name),
                (updated_value, user_id,)
            )
            response_message = self.__get_update_message(pattern_name, user_id, updated_value)


        return response_message

    #NECESITO ARREGLAR ESTA FUNCION
    #ESTA TRATANDO DE DEFINIR messages Y NO CUANDO updatedValue es un valor  
    def __get_update_message(self,patternName, user_id, updatedValue):
        if patternName=="updateFullUser":
            if isinstance(updatedValue, (list, tuple)) and len(updatedValue)!=7:
                return (
                    f"Usuario actualizado para el usuario con el id previamente registrado como {user_id}\n\n"
                    f"Los nuevos valores del usuario son:\n\n"
                    f"id: {updatedValue[0]}\n\n"
                    f"nickname: {updatedValue[1]}\n\n"
                    f"creditos: {updatedValue[2]}\n\n"
                    f"rol: {updatedValue[3]}\n\n"
                    f"plan: {updatedValue[4]}\n\n"
                    f"soporte: {updatedValue[5]}\n\n"
                    f"anti_spam_timeout: {updatedValue[6]}"
                )
            return f"La solicitud de actualización completa para el usuario debe incluir el id del usuario y todos los valores a actualizar."            

        messages = {
            'updateId': f'El nuevo id para el usuario previamente registrado como {user_id} es: {updatedValue}',
            'updateNickname': f'El nuevo nickname para el id {user_id} es:\n{updatedValue}',
            "updateCreditos": f"Creditos actualizados para el número {user_id}.\nNueva cantidad de creditos: {updatedValue}",
            'updateRol': f'Rol actualizado para el id {user_id}.\nNuevo rol: {updatedValue}',
            "updatePlan": f"Plan actualizado para el id {user_id}.\nNuevo plan: {updatedValue}",
            'updateSoporte': f'Soporte actualizado para el id {user_id}.\nNuevo soporte: {updatedValue}',
            "updateAntiSpamTimeout": f"El nuevo tiempo de espera de antispam para el id {user_id} es:\n{updatedValue} segundos",
        }
        message_template = messages.get(patternName)
        return message_template.format(id=user_id, updated_value=updatedValue)

    #Accepts the message and check if the message checks with any of the patterns
    def __check_pattern_match(self, message):
        for name, pattern in self.patternsDict.items():
            #compile a regular expression into a regular expression object
            compiled_pattern = re.compile(pattern)
            #check if there's a match with the compiled pattern
            matched = compiled_pattern.match(message)
            if matched:
                return name, pattern, matched,
        return None, None, None

    def __register_or_check_user(self, id, nickname):
        if self.connection.is_connected():
            result = cr.fetch_data(self.connection,'select * from users where id = %s', (id,))
            if len(result) == 1:
                return result[0]
            else:
                creditos = '0' 
                rol = 'Cliente'
                plan = 'Free'
                soporte = 'Cliente'
                anti_spam_timeout ='10'
                result = cr.insert_data(self.connection, 'insert into users (id, nickname, creditos, rol, plan, soporte, anti_spam_timeout) values (%s,%s,%s,%s,%s,%s,%s)',(id, nickname, creditos, rol, plan, soporte, anti_spam_timeout))
                if result is not None :
                    return [id, nickname, creditos, rol, plan, soporte, anti_spam_timeout]
                else:
                    logging.error("Can't add the user")
                    return []
        logging.error("Failed database connection")
        return [] 

#################################################
    def __preprocess_text(self, question):
        doc = self.nlp(question)
        # Extraer palabras clave (sustantivos y verbos)
        keywords = [token.lemma_ for token in doc if token.pos_ in ["NOUN", "VERB"]]
        return " ".join(keywords)

    def __get_answer_with_difflib(self, question, *args):
        closest_match = difflib.get_close_matches(question, self.qa_pairs.keys(), n=1, cutoff=0.6)
        if closest_match:
            #return self.qa_pairs[closest_match[0]]
            value = self.qa_pairs[closest_match[0]]
            # Verificar si el valor es una función y si es callable
            if isinstance(value,tuple) and callable(value[0]):
                if value[1]:  # Si requiere parámetros
                    return value[0](*args)  # Llamar con los parámetros
                else:
                    return value[0]()  # Llamar sin parámetros si no hay
            else:
                return value  # Retornar el valor directo si no es una función
        return None

    def __get_answer_with_cosine_similarity(self, question, *args):
        # Preprocesar la pregunta
        processed_question = self.__preprocess_text(question)
        # Convertir a vector TF-IDF
        question_vector = self.vectorizer.transform([processed_question])
        # Calcular similitud de coseno
        similarities = cosine_similarity(question_vector, self.tfidf_matrix)
        # Encontrar la pregunta más similar
        most_similar_index = similarities.argmax()
        if similarities[0, most_similar_index] > 0.5:  # Umbral de similitud
            matched_question = self.questions[most_similar_index]
            value = self.qa_pairs[matched_question]
            # Verificar si el valor es una función y si es callable
            if isinstance(value,tuple) and callable(value[0]):
                if value[1]:  # Si requiere parámetros
                    return value[0](*args)  # Llamar con los parámetros
                else: # no requiere parametros
                    return value[0]()  # Llamar sin parámetros si no son necesarios
            else:
                return value  # Retornar el valor directo si no es una función
        return None

    def qa_to_json_excel_url(self,url):

        try:
            sht = self.gc.open_by_url(url)
            worksheets = sht.worksheets()
            # Solo tomamos la primera hoja
            sheet = worksheets[0]
            sheet_data = sheet.get_all_values()
            sheet_data_list = [row[:2] for row in  sheet_data]
            self.qa_pairs = {sublista[0]: sublista[1] for sublista in sheet_data_list}

            os.makedirs(self.qa_directory_route, exist_ok=True)

            with open(self.qa_file_route,'w', encoding='utf-8') as f:
                json.dump(self.qa_pairs, f, ensure_ascii=False, indent=4)
        except Error as e:
            logging.error(f"Error ocurred: {e}")
            return "No se pudo completar la acción. Intentelo de nuevo más tarde."

    def set_qa_pairs_json(self):
        with open(self.qa_file_route, 'r', encoding='utf-8') as f:
            self.qa_pairs = json.load(f)
        
        self.questions = list(self.qa_pairs.keys())
        self.tfidf_matrix = self.vectorizer.fit_transform(self.questions)

    def get_answer(self,question,*args):
        # Primero intenta con Difflib
        answer = self.__get_answer_with_difflib(question,*args)
        if answer:
            return answer

        # Si no hay coincidencia, usa similitud de coseno con preprocesamiento
        answer = self.__get_answer_with_cosine_similarity(question,*args)
        if answer:
            return answer

        # Si no se encuentra una respuesta
        return None

    def set_qa_pairs_string(self, message):

        #generic_message_pair_list = message.split(",")
        # Crear la lista limpiando espacios
        generic_message_pair_list = [item.strip() for item in message.split(",")]

        for i in range(int(len(generic_message_pair_list)/2)):
            key = f"{generic_message_pair_list[2*i]}"
            value = generic_message_pair_list[2*i+1]
            self.generic_message_pair_dict[key] = value

    def set_qa_pairs_excel(self, qa_pairs):

        for pair in qa_pairs:
            key = f"{pair[0]}"
            value = f"{pair[1]}"
            self.generic_message_pair_dict[key] = value

    def get_qa_pairs(self, message):

        response = self.generic_message_pair_dict.get(message, None)

        if response is not None:
            return response

        return "Error"

###########################################################################

    def valid_url(url):
        try:
            result = urlparse(url)
        #verifies if scheme and hostname (netloc) are present in the resulting analysis.
            return all([result.scheme, result.netloc])
        except:
            return False