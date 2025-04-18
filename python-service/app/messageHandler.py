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

class InvalidUrl(Exception):
    pass

class MessageHandler:
    
    def __init__(self):
        self.status = 0
        #Dictionary for regular expression patterns
        self.mysql_query_regex_map = {
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
        self.generic_default_answer = "No sé la respuesta a eso. Te muestro temas con los que puedo ayudarte: "
        #Regex pattern to check for the webpages
        self.patternPages = r"^(https://)?(www\.)?(elements\.)?(freepik|envato)\.(com|es)(/.*)?$"
        # Cargar el modelo de lenguaje en español
        self.nlp = spacy.load("es_core_news_sm")

        self.excel_url = ""

        # qa pairs
        self.qa_pairs = {}
        self.messages = {}

        script_dir = os.path.dirname(os.path.abspath(__file__))

        self.qa_directory_route = os.path.abspath(os.path.join(script_dir, '../qa-files/')) 

        self.qa_file_route = os.path.abspath(os.path.join(script_dir, '../qa-files/qa.json')) 
        self.url_file_route =  os.path.abspath(os.path.join(script_dir, '../qa-files/excel_url.json')) 

        self.vectorizer = TfidfVectorizer()

        self.api_key_google_sheets = 'AIzaSyAMiaX8o1myMZiZFacs8_Ckl2Dyv98Ff4U'

        try:
            self.gc = gspread.api_key(self.api_key_google_sheets)
            # Hay archivo de ruta para inicializar el bot
            if os.path.exists(self.url_file_route):                
                with open(self.url_file_route, 'r', encoding='utf-8') as f:
                    self.excel_url = json.load(f)["url"]
                self.qa_excel_to_json_url(self.excel_url)

            if os.path.exists(self.qa_file_route):
                #print("El archivo qa existe")
                self.set_qa_pairs_from_json()
                # Esto se pone a parte porque quiero que los comandos solo funcionen cuando se escriben exatamente igual
                self.set_qa_function_key()

            # Cargar el archivo JSON
            #directorio_actual = os.getcwd()
            #print("Directorio actual:", directorio_actual)
            with open("app/messages.json", 'r', encoding='utf-8') as f:
                self.messages = json.load(f)

            if not self.qa_pairs:
                self.qa_pairs = {
                    "HOla, buen día": "Hola, buen día. ¿Cómo estas? ¿Cómo puedo ayudarte?",
                    "¿Dónde encuentro la política de privacidad?": "La política de privacidad está en el pie de página.",
                    "!me" : (self.__handle_me, True),
                    "!buy": (self.__handle_buy, False),
                    "!configureUrl": (self.set_qa_flow,True)
                }

            # Convertir preguntas a vectores TF-IDF
            self.questions = list(self.qa_pairs.keys())
            self.generic_default_answer = self.generic_default_answer + "\n".join(f"{i+1}.- {elem}" for i, elem in enumerate(self.questions))
            self.tfidf_matrix = self.vectorizer.fit_transform(self.questions)

            #print("Aca tan las preguntas")
            #print(self.questions)

            #create the database connection
            self.connection = cr.create_connection()
        except Exception as e: 
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
        try:
            # Creo que puedo pasar casi todo esto a get_answer
            #verifies database connection
            self.connection = cr.reconnect(self.connection)
            # check all the update patterns to check for a coincidence
            #pattern_name, pattern_mysql_regex, matched = self.__check_pattern_match(message)

            ans = self.get_answer(message,requester_id, nickname)

            if ans is not None:
                return ans
            if re.match(self.patternPages,message):
                return self.__handle_file_download_request(requester_id,message)
            #elif pattern_name:
            #    return self.__handle_db_requests(requester_id, pattern_name, pattern_mysql_regex, matched)
            else: 
                return self.generic_default_answer
        except InvalidUrl as e:
            logging.error(f"Error ocurred: {e}")
            return self.__get_message("errors","emptyIncorrectUrl")
        except Exception as e: 
            logging.error(f"Error ocurred: {e}")
            return self.__get_message("errors","cantCompleteRequest")

    # Definir una función para obtener mensajes
    def __get_message(self, desired_category, key):
        # Accede a la categoría y luego a la clave dentro de ella
        obtained_category = self.messages.get(desired_category,{})
        response = obtained_category.get(key, "No se pudo completar la solicitud, intentalo de nuevo mas tarde.")
        return response

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
        except Exception as e: 
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
        except Exception as e: 
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
        for name, pattern in self.mysql_query_regex_map.items():
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

    # Verificar si el valor es una función y si es callable
    def __get_value_from_dict(self,value,*args):
        print("Entra a funcion get_value_from_dict")
        print(value)
        if isinstance(value,tuple) and callable(value[0]):
            if value[1]:  # Si requiere parámetros
                return value[0](*args)  # Llamar con los parámetros
            else:
                return value[0]()  # Llamar sin parámetros si no hay
        else:
            # Value puede ser un texto por obtenerlo de la respuesta generica o porque asi se obtiene del dict
            return value  # Retornar el valor directo si no es una función

    def __get_answer_with_difflib(self, question, *args):
        closest_match = difflib.get_close_matches(question, self.qa_pairs.keys(), n=1, cutoff=0.6)
        if closest_match:
            # obtiene la funcion
            value = self.qa_pairs[closest_match[0]]
            # Verificar si el valor es una función y si es callable
            return_value = self.__get_value_from_dict(value, *args)
            return return_value
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
            return_value = self.__get_value_from_dict(value, *args)
            return return_value
        return None

    def set_qa_function_key(self):
        print("Entra a funcion set_qa_function_key")
        self.qa_pairs["!me"] = (self.__handle_me, True)
        self.qa_pairs["!configureUrl"] = (self.set_qa_flow,True)

    def set_qa_pairs_from_json(self):
        print("Entra a funcion set_qa_pairs_from_json")
        with open(self.qa_file_route, 'r', encoding='utf-8') as f:
            self.qa_pairs = json.load(f)
        
        self.questions = list(self.qa_pairs.keys())
        self.generic_default_answer = self.generic_default_answer + "\n".join(f"{i+1}.- {elem}" for i, elem in enumerate(self.questions))
        self.tfidf_matrix = self.vectorizer.fit_transform(self.questions)

    def get_answer(self,question,*args):
        ### CHECAR SI FUNCIONA BIEN LA FUNCION PARA AÑADIR EL URL
        #Expresión regular para separar el comando y la URL
        # Mas general para comandos
        #pattern = r'configure\s*\{(https?://[^\s{}]+)\}'
        #patternExcelFileUrl =  r"!([\w]+) '(.+)'"
        # Mas particular, solo para la url

        patternExcelFileUrl = r"(![\w]+) (https?://\S+)"
        excel_file_url_pattern_match = re.match(patternExcelFileUrl, question)

        if excel_file_url_pattern_match is not None:
            ### SI ENTRA ACA
            print("Entra al if de match url")
            # Aqui question es el patron obtenido, que debe encontrarse en el diccionario de funciones
            question, url = excel_file_url_pattern_match.groups()
            args = args + (url,)
            #Si hay una funcion la devuelve de otro modo devuelve la respuesta generica
            value = self.qa_pairs.get(question, self.generic_default_answer)
            # Verificar si el valor es una función y si es callable
            answer = self.__get_value_from_dict(value, *args)
            ## NI VALUE NI ANSWER DAN UNA RESPUESTA CORRECTA. REGRESAN "No se la respuesta a eso"
            return answer
        
        patternUpdateQA = r'^!updateQA'
        qa_pattern_match = re.search(patternUpdateQA, question)

        # Si solo queremos actualizar las preguntas respuestas pasamos por default el link del excel
        # que ya estaba previamente registrado
        if qa_pattern_match:
            print("entra a if de patron qa")
            self.qa_excel_to_json_url(self.excel_url)
            return self.__get_message("return_message", "configureUrlSuccesfull")

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

    # Obtiene los datos del excel a traves del url y los transforma en json
    def qa_excel_to_json_url(self,*args):

        # la url debe ser el último elemento
        print("entra a la funcion de qa_excel_to_json_url")
        url = args[-1] if args else None
        if not url:
            raise InvalidUrl(self.__get_message("errors","noArgumentsResponse"))
        sht = self.gc.open_by_url(url)
        worksheets = sht.worksheets()
        # Solo tomamos la primera hoja
        sheet = worksheets[0]
        sheet_data = sheet.get_all_values()
        sheet_data_list = [row[:2] for row in  sheet_data]
        self.qa_pairs = {sublista[0]: sublista[1] for sublista in sheet_data_list}

        # Crea el folder sino existe, si ya existe no hace nada
        os.makedirs(self.qa_directory_route, exist_ok=True)

        with open(self.qa_file_route,'w', encoding='utf-8') as f:
            json.dump(self.qa_pairs, f, ensure_ascii=False, indent=4)

    def set_excel_url(self,*args):
        print("Entra a funcion set_excel_url")
        if os.path.exists(self.url_file_route):
            os.remove(self.url_file_route)

        # la url debe ser el último elemento
        url = args[-1] if args else None
        if not url:
            raise InvalidUrl(self.__get_message("errors","noArgumentsResponse"))
        
        self.excel_url = url
        data = {"url" : self.excel_url}

        #with open(self.url_file_route, 'r', encoding='utf-8') as f:
        with open(self.url_file_route, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def set_qa_flow(self,*args):
        print("Entra a funcion set_qa_flow")
        self.set_excel_url(*args)
        self.qa_excel_to_json_url(*args)
        self.set_qa_pairs_from_json()
        self.set_qa_function_key()
        print("Configuration complete")
        return self.__get_message("return_message","configureUrlSuccesfull")

###########################################################################

    def valid_url(url):

        try:
            result = urlparse(url)
        #verifies if scheme and hostname (netloc) are present in the resulting analysis.
            return all([result.scheme, result.netloc])
        except:
            return False
        
###################################################################### Probably unused functions

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