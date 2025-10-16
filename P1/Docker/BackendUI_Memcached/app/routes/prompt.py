from flask import Blueprint, request,jsonify
from tools.mariadb_connection import execute_query
from tools.elastic_connection import execute_query_es, execute_vector_query, execute_text_search_by_title
from tools.embbeding import get_embedding
import logging
import sys
import mariadb
from pymemcache.client.base import Client
import os, json 
from prometheus_client import Counter, Histogram
import time
from metrics import (
    cache_hit, cache_miss,
    cache_hit_api, cache_miss_api,
    tiempo_procesamiento_api, peticiones_endpoint_api,
    COMPONENT, BD_TYPE, CACHE_TYPE, CACHE_TTL_SECONDS,
    MEMCACHED_HOST, MEMCACHED_PORT
)
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
            cache_miss_api.labels(componente=COMPONENT).inc()
            return None
        
        cache_hit.labels(bd=BD_TYPE, cache=CACHE_TYPE).inc()
        cache_hit_api.labels(componente=COMPONENT).inc()
        return json.loads(raw.decode("utf-8"))
    except Exception:
        cache_miss.labels(bd=BD_TYPE, cache=CACHE_TYPE).inc()
        cache_miss_api.labels(componente=COMPONENT).inc()
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
        # run searches
        # reviews vector search
        start_rv_vector = time.perf_counter()
        rv_hits = execute_vector_query("reviews", embedding)
        rv_vector_search_ms = round((time.perf_counter() - start_rv_vector) * 1000, 2)
        reviews_vector = [{"_id": h.get("_id"), "_score": h.get("_score"), "_source": h.get("_source")} for h in (rv_hits or [])]

        #reviews text search (nreviews index uses text+summary)
        start_reviews = time.perf_counter()
        rt_hits = execute_text_search_by_title("nreviews", text, match_phrase=False, fuzziness="AUTO", fields=["title", "review_text", "review_summary"]) or []
        rt_hits = complete_reviews(rt_hits)
        reviews_search_ms = round((time.perf_counter() - start_reviews) * 1000, 2)
        reviews_text = [{"_id": h.get("_id"), "_score": h.get("_score"), "_source": h.get("_source")} for h in rt_hits]

        #books vector search
        start_bv_vector = time.perf_counter()
        bv_hits = execute_vector_query("books", embedding)
        bv_vector_search_ms = round((time.perf_counter() - start_bv_vector) * 1000, 2)
        books_vector = [{"_id": h.get("_id"), "_score": h.get("_score"), "_source": h.get("_source")} for h in (bv_hits or [])]

        #books text search (nbooks index searches description)
        start_books = time.perf_counter()
        bt_hits = execute_text_search_by_title("nbooks", text, match_phrase=False, fuzziness="AUTO", fields=["title", "description"]) or []
        books_search_ms = round((time.perf_counter() - start_books) * 1000, 2)
        books_text = [{"_id": h.get("_id"), "_score": h.get("_score"), "_source": h.get("_source")} for h in bt_hits]

        #maria db search
        start_maria = time.perf_counter()
        mariaresult = search_mariadb(text)
        mariadb_search_ms = round((time.perf_counter() - start_maria) * 1000, 2)

        combined = {
            "reviews_text": reviews_text,
            "books_text": books_text,
            "mariadb": mariaresult,
            "reviews_vector": reviews_vector,
            "books_vector": books_vector,
            "timings_ms": {
                "reviews_text": reviews_search_ms,
                "books_text": books_search_ms,
                "mariadb": mariadb_search_ms,
                "reviews_vector": rv_vector_search_ms,
                "books_vector": bv_vector_search_ms
            },
        }


        """ combined = {
            "reviews_vector": reviews_vector,
            "reviews_text": reviews_text,
            "books_vector": books_vector,
            "books_text": books_text,
            "mariadb": mariaresult
        } """


        return jsonify(combined), 200
    except Exception as e:
        logger.error(f"Error posting prompt: {e}")
        return {"error": "Error generating prompt"}, 500


def complete_reviews(reviews):

    for review in reviews:
        book_info = search_book(review["_source"]["title"])
        if book_info and isinstance(book_info, list) and len(book_info) > 0:
            book = book_info[0]
            if isinstance(book, dict):
                review["_source"]["book_id"] = book.get("id")
                review["_source"]["description"] = book.get("description")
                review["_source"]["publisher"] = book.get("publisher")
                review["_source"]["preview_link"] = book.get("preview_link")
                review["_source"]["info_link"] = book.get("info_link")
                review["_source"]["image_link"] = book.get("image_link")
                review["_source"]["ratings_count"] = book.get("ratings_count")
                review["_source"]["authors"] = book.get("authors")
                review["_source"]["categories"] = book.get("categories")
            
    return reviews

#auxiliar methods for searching reviews with vectors search in elasticsearch
def search_vector(embedding,name):
    #call the function in elastic_connection to do the vector search
    result = execute_vector_query(name, embedding)
    # result is a list of hit dicts
    try:
        if result:
            return jsonify(result)
        return None
    except Exception as e:
        logger.error(f"Error converting vector search results to json: {e}")
        return None

#auxiliar methods for searching reviews with text search in elasticsearch
def search_esText(text,name):

    # choose fields depending on index
    try:
        if name == "nbooks":
            fields = ["description"]
        elif name == "nreviews":
            fields = ["review_text", "review_summary"]
        else:
            fields = ["title"]

        result = execute_text_search_by_title(name, text, match_phrase=False, fuzziness="AUTO", fields=fields)

        # result is a list of hits
        if result:
            return jsonify(result)
        return None
    except Exception as e:
        logger.error(f"Error executing text search for index {name}: {e}")
        return None


#auxiliar methods for searching books and reviews in mariadb
def search_mariadb(text, limit=10):
    if not text:
        return []

    like = f"%{text}%"
    query = (
        "SELECT * FROM ("
        "  SELECT b.id AS book_id, b.title, b.description, b.publisher, b.preview_link, b.info_link, b.image_link, b.ratings_count, "
        "         COALESCE(bauth.names, '') AS authors, COALESCE(bcat.names, '') AS categories, "
        "         r.id AS review_id, r.title AS review_title, r.review_summary, r.review_text, r.review_score, "
        "         r.user_id, r.profile_name, r.review_time "
        "  FROM books b "
        "  LEFT JOIN reviews r ON r.book_id = b.id "
        "  LEFT JOIN ("
        "    SELECT ba.book_id, GROUP_CONCAT(DISTINCT a.name ORDER BY a.name SEPARATOR ', ') AS names "
        "    FROM book_authors ba "
        "    JOIN authors a ON a.id = ba.author_id "
        "    GROUP BY ba.book_id"
        "  ) bauth ON bauth.book_id = b.id "
        "  LEFT JOIN ("
        "    SELECT bc.book_id, GROUP_CONCAT(DISTINCT c.name ORDER BY c.name SEPARATOR ', ') AS names "
        "    FROM book_categories bc "
        "    JOIN categories c ON c.id = bc.category_id "
        "    GROUP BY bc.book_id"
        "  ) bcat ON bcat.book_id = b.id "
        "  WHERE b.description LIKE ? OR r.review_text LIKE ? OR r.review_summary LIKE ? "
        "  UNION ALL "
        "  SELECT NULL AS book_id, r.title, NULL AS description, NULL AS publisher, NULL AS preview_link, NULL AS info_link, NULL AS image_link, NULL AS ratings_count, "
        "         '' AS authors, '' AS categories, r.id AS review_id, r.title AS review_title, r.review_summary, r.review_text, r.review_score, "
        "         r.user_id, r.profile_name, r.review_time "
        "  FROM reviews r "
        "  LEFT JOIN books b2 ON b2.id = r.book_id "
        "  WHERE b2.id IS NULL AND (r.review_text LIKE ? OR r.review_summary LIKE ?)"
        ") AS results "
        "ORDER BY results.review_time DESC "
        "LIMIT ?"
    )

    try:
        return execute_query(query, (like, like, like, like, like, limit))
    except Exception as exc:
        logger.error(f"Error searching MariaDB: {exc}")
        return []

#auxiliar method to create a json response with the five search results
def search_book(title):
    #call the function in mariadb_connection to do the search
    result = execute_query("SELECT * FROM books WHERE title LIKE ?", (f"%{title}%",))
    try:
        if result:
            return jsonify(result)
        return None
    except Exception as e:
        logger.error(f"Error converting text search results to json: {e}")
        return None

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
            "SELECT p.id, p.text, p.created_at, p.likes, u.name, u.lastname FROM Prompt p JOIN User u ON p.id_user = u.id WHERE p.id_user = ? AND p.enabled = TRUE ORDER BY p.created_at DESC",
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
        # split the text into words to search each one in prompts text or user name or lastname
        words = text.split()
        query = "SELECT p.id, p.text, u.name, u.lastname, p.likes FROM Prompt p JOIN User u ON p.id_user = u.id WHERE "
        params = []
        conditions = []
        # create a condition for each word to search in name or lastname
        for w in words:
            conditions.append("(p.text LIKE CONCAT('%', ?, '%') OR u.name LIKE CONCAT('%', ?, '%') OR u.lastname LIKE CONCAT('%', ?, '%'))")
            params.extend([w, w, w])

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
            "SELECT p.id, p.text, p.created_at, p.likes, u.name, u.lastname FROM Prompt p JOIN User u ON p.id_user = u.id WHERE p.id = ?  AND p.enabled = TRUE ORDER BY p.created_at DESC",
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
            friend_prompts = my_prompts(friend["id_friend"])
            logger.error(f"Error fetching prompts for user {friend_prompts}")
            if friend_prompts and isinstance(friend_prompts, list):
                for prompt in friend_prompts:
                    if isinstance(prompt, dict) and "id" in prompt and prompt["id"] not in added_prompt_ids:
                        feed.append(prompt)
                        added_prompt_ids.add(prompt["id"])
            
        #get liked prompts
        likes = execute_query(
            "SELECT id_prompt FROM Liked WHERE id_user = ? AND enabled = TRUE",
            (id_user,)
        )

        for like in likes:
            id_prompt = like["id_prompt"]
            if id_prompt not in added_prompt_ids:
                like_prompt = my_prompt(id_prompt)
                if like_prompt and isinstance(like_prompt, list) and len(like_prompt) > 0:
                    prompt = like_prompt[0]
                    if isinstance(prompt, dict) and "id" in prompt and prompt["id"] not in added_prompt_ids:
                        feed.append(prompt)
                        added_prompt_ids.add(prompt["id"])

        return jsonify(feed), 200

    except Exception as e:
        logger.error(f"Error aaaaaaaaaaaaaaaaaaaaaaaa {id_user}: {e}")
        return jsonify({"error": "Error fetching prompts"}), 500


