from flask import Blueprint, request,jsonify
from tools.mariadb_connection import execute_query
from tools.embbeding import get_embedding
import logging
import sys
import mariadb
from pymemcache.client.base import Client
from metrics import cache_hit, cache_miss
import os, json 

#Memcached variables
BD_TYPE = "mariadb"
CACHE_TYPE = "memcached"

MEMCACHED_HOST = os.getenv("MEMCACHED_HOST")
MEMCACHED_PORT = int(os.getenv("MEMCACHED_PORT"))
CACHE_TTL_SECONDS = 60

memcached = Client((MEMCACHED_HOST, MEMCACHED_PORT))

logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

prompt_blueprint = Blueprint('prompt', __name__)

def cache_get(key):
    try:
        raw = memcached.get(key)
        if not raw:
            cache_miss.labels(bd=BD_TYPE, cache=CACHE_TYPE).inc()
            return None
        
        cache_hit.labels(bd=BD_TYPE, cache=CACHE_TYPE).inc()
        return json.loads(raw.decode("utf-8"))
    except Exception:
        cache_miss.labels(bd=BD_TYPE, cache=CACHE_TYPE).inc()
        return None

def cache_set(key: str, value: dict, ttl: int = CACHE_TTL_SECONDS):
    try:
        memcached.set(key, json.dumps(value), expire=ttl)
    except Exception:
        pass

#route to generate a result by a prompt
@prompt_blueprint.route('/generate', methods=['POST'])
def generate():

    try:
        logger.info("Generating prompt")
        #get data from body request
        text = request.json.get("text")
        #get the embedding
        response = get_embedding(text)
        embedding = response["embedding"]

        #get the results by the text embedding


        
        return jsonify(response["embedding"]), 400
    except Exception as e:
        logger.error(f"Error posting prompt: {e}")
        return {"error": "Error generating prompt"}, 500



#auxiliar methods for posting a prompt
def insert_prompt(text, id_user):
    return execute_query(
        "INSERT INTO Prompt (text, id_user) VALUES (?, ?)",
        (text, id_user),
        get_id=True
    )

#auxiliar methods for update a prompt
def update_prompt(text, id_prompt):
    return execute_query(
        "UPDATE Prompt SET text = ? WHERE id = ?",
        (text, id_prompt),
        get_id=True
    )



#route fot posting a prompt
@prompt_blueprint.route('/post', methods=['POST'])
def post():
    data = request.json.get("prompt")
    if not data:
        return jsonify({"error": "prompt is required"}), 400

    text = data.get("text")
    id_user = data.get("id_user")

    if not text or not id_user:
        return jsonify({"error": "id_user and text are required"}), 400

    try:
        #saving the prompt
        prompt_id = insert_prompt(text, id_user)

        logger.info(f"Prompt {prompt_id} registered successfully")
        return {"message": "Prompt registered successfully"}, 201

    except mariadb.IntegrityError as e:
        logger.error(f"Integrity error posting prompt: {e}")
        return {"error": "Database integrity error"}, 500

    except Exception as e:
        logger.error(f"Error posting prompt: {e}")
        return {"error": "Error posting prompt"}, 500
    

#route to generate a result by a prompt
@prompt_blueprint.route('/edit', methods=['PUT'])
def edit():
    data = request.json.get("prompt")
    if not data:
        return jsonify({"error": "prompt is required"}), 400

    text = data.get("text")
    id_prompt = data.get("id_prompt")


    if not text or not id_prompt:
        return jsonify({"error": "id_prompt and text are required"}), 400

    try:
        #saving the prompt
        prompt_id = update_prompt(text, id_prompt)

        logger.info(f"Prompt {prompt_id} edited successfully")
        return {"message": "Prompt edited successfully"}, 201

    except mariadb.IntegrityError as e:
        logger.error(f"Integrity error posting prompt: {e}")
        return {"error": "Database integrity error"}, 500

    except Exception as e:
        logger.error(f"Error edited prompt: {e}")
        return {"error": "Error edited prompt"}, 500


#route to generate a result by a prompt
@prompt_blueprint.route('/myprompts', methods=['GET'])
def my_prompts(id_user=None):
    invocated = True
    if id_user is None:
        invocated = False
        if request.method == "POST":
            id_user = request.json.get("id_user")
        if not id_user:
            id_user = request.args.get("id_user")

    if not id_user:
        return jsonify({"error": "id_user is required"}), 400

    cache_key = f"myprompts:{id_user}"

    # Try to get user prompts from cache hit
    cached = cache_get(cache_key)
    if cached is not None:
        logger.info(f"My prompts id_user='{id_user}' source=cache")
        if invocated:
            return cached
        return jsonify(cached), 200

    try:
        #get user prompts
        prompts = execute_query(
            "SELECT id, text, created_at, likes FROM Prompt WHERE id_user = ? AND enabled = TRUE ORDER BY created_at DESC",
            (id_user,)
        )

        # Cache miss, so we save the prompts data in cache
        cache_set(cache_key, prompts, CACHE_TTL_SECONDS)
        logger.info(f"My prompts id_user='{id_user}' source=db")

        if invocated:
            return prompts
        return jsonify(prompts), 200

    except Exception as e:
        logger.error(f"Error fetching prompts for user {id_user}: {e}")
        return jsonify({"error": "Error fetching prompts"}), 500

#route to search prompts
@prompt_blueprint.route('/search', methods=['GET'])
def search():
    #get the params of the request body
    text = request.args.get("text")

    if not text:
        return jsonify({"error": "text is required"}), 400
    #clean the text
    text = text.strip('"')

    cache_key = f"search:{text.lower()}"  

    # Try to get user data from cache hit
    cached = cache_get(cache_key)
    if cached is not None:
        logger.info(f"Search prompts text='{text}' source=cache")
        return jsonify(cached), 200
    
    try:
        # split the text into words to search each one
        words = text.split()
        query = "SELECT id, text FROM Prompt WHERE "
        params = []
        conditions = []
        # create a condition for each word to search in name or lastname
        for w in words:
            conditions.append("(text LIKE CONCAT('%', ?, '%'))")
            params.extend([w])

        query += " AND ".join(conditions)  #all conditions must be met
        query += " AND enabled = TRUE"
        #execute the query created
        prompts = execute_query(query, tuple(params))

        # Cache miss, so we save the prompts data in cache
        cache_set(cache_key, prompts, CACHE_TTL_SECONDS)
        logger.info(f"Search prompts text='{text}' source=db")
        return jsonify(prompts), 200
        
    except mariadb.IntegrityError as e:
        # there was an error with the query
        logger.error(f"Integrity error finding prompt : {e}")
        return {"error": "Database integrity error"}, 500

    except Exception as e:
        logger.error(f"Integrity error finding users : {e}")
        return {"error": "Error finding prompt"}, 500

#route to generate a result by a prompt
@prompt_blueprint.route('/delete', methods=['PUT'])
def delete():
    #get the params of the request
    id_prompt = request.json.get("id_prompt")


    if not id_prompt:
        return jsonify({"error": "id_prompt is required"}), 400

    try:
        #UPDATE the register to put it false
        execute_query(
            """UPDATE Prompt SET enabled = FALSE WHERE id = ?""",
            (id_prompt,)
        )

        logger.info(f"Prompt {id_prompt} deleted successfully")
        return {"message": "Prompt deleted successfully"}, 201

    except mariadb.IntegrityError as e:
        # the email must be unique this error is for duplicate entry
        logger.error(f"Integrity error deleting prompt : {e}")
        return {"error": "Database integrity error"}, 500

    except Exception as e:
        logger.error(f"Integrity error deleting prompt  : {e}")
        return {"error": "Error deleting prompt "}, 500

#route to generate a result by a prompt
@prompt_blueprint.route('/myprompt', methods=['GET'])
def my_prompt(id_prompt=None):

    invocated = True #this variable say if the method was called here
    #get data from bady request or from the params
    if id_prompt is None:
        invocated = False
        if request.method == "POST":
            id_prompt = request.json.get("id_prompt")
        if not id_prompt:
            id_prompt = request.args.get("id_prompt")

    if not id_prompt:
        return jsonify({"error": "id_prompt is required"}), 400

    cache_key = f"myprompt:{id_prompt}"

    # Try to get prompt data from cache hit
    cached = cache_get(cache_key)
    if cached is not None:
        logger.info(f"My prompt id_prompt='{id_prompt}' source=cache")
        if invocated:
            return cached
        return jsonify(cached), 200

    try:
        #get user prompts
        prompt = execute_query(
            "SELECT id, text, created_at, likes FROM Prompt WHERE id = ?  AND enabled = TRUE ORDER BY created_at DESC",
            (id_prompt,)
        )

        # Cache miss, so we save the prompt data in cache
        cache_set(cache_key, prompt, CACHE_TTL_SECONDS)
        logger.info(f"My prompt id_prompt='{id_prompt}' source=db")

        if invocated:
            return prompt
        
        return jsonify(prompt), 200

    except Exception as e:
        logger.error(f"Error fetching prompts for user {id_prompt}: {e}")
        return jsonify({"error": "Error fetching prompts"}), 500

#route for get the feed
@prompt_blueprint.route('/feed', methods=['GET'])
def feed():
    id_user = request.args.get("id_user")
    if not id_user:
        return jsonify({"error": "id_user is required"}), 400
    
    try:

        added_prompt_ids = set() #save the idprompt to avoid duplicate
        #get user prompts from friends
        friends = execute_query(
            "SELECT id_friend FROM Friend WHERE id_user = ? AND enabled = TRUE",
            (id_user,)
        )

        feed = []
        for friend in friends:
            friend_prompt = my_prompts(friend["id_friend"])
            if friend_prompt:
                feed.append(friend_prompt)
                added_prompt_ids.add(friend_prompt["id"])
            
        #get liked prompts
        likes = execute_query(
            "SELECT id_prompt FROM Liked WHERE id_user = ? AND enabled = TRUE",
            (id_user,)
        )

        for like in likes:
            id_prompt = like["id_prompt"]
            if id_prompt not in added_prompt_ids:
                like_prompt = my_prompt(id_prompt)
                if like_prompt:
                    feed.append(like_prompt)

        return jsonify(feed), 200

    except Exception as e:
        logger.error(f"Error fetching prompts for user {id_user}: {e}")
        return jsonify({"error": "Error fetching prompts"}), 500

