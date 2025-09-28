from flask import Blueprint, request,jsonify
from tools.mariadb_connection import execute_query
import logging
import sys
import mariadb

logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

prompt_blueprint = Blueprint('prompt', __name__)

#route to generate a result by a prompt
@prompt_blueprint.route('/generate', methods=['GET'])
def generate():
    logger.info("esto es un prompt generado")
    return "generate route"

#route to post a generated prompt
@prompt_blueprint.route('/post', methods=['POST'])
def post():
    #get the params of the request
    prompt = request.json.get("prompt")
    id_user = id_user = request.json.get("prompt", {}).get("id_user")


    if not prompt or not id_user:
        return jsonify({"error": "id_user and prompt are required"}), 400

    #get prompt fields
    text =  request.json.get("prompt", {}).get("text")
    books = request.json.get("prompt", {}).get("books")

    try:
        #Save PROMPT into database and getting the last inserted id
        prompt_id = execute_query(
            "INSERT INTO Prompt (text, id_user) VALUES (?, ?)",
            (text, id_user,), get_id=True
        )

        if insert_books(books, prompt_id):
            logger.info(f"Prompt {prompt_id} registered successfully")
            return {"message": "Prompt registered successfully"}, 201
        else:
            logger.error(f"Unexpected error posting: {e}")
            return {"error": "Error posting prompt"}, 500


    except mariadb.IntegrityError as e:
        # the email must be unique this error is for duplicate entry
        logger.error(f"Integrity error posting prompt : {e}")
        return {"error": "Database integrity error"}, 500

    except Exception as e:
        logger.error(f"Integrity error posting prompt  : {e}")
        return {"error": "Error posting prompt "}, 500

    return
    
#method to insert the books   
def insert_books(books, id_prompt):
    try:
        for book in books:
            #get book data
            searchType= book.get("searchType")
            tittle = book.get("title")
            description = book.get("description")
            image = book.get("image")
            previewLink = book.get("previewLink")
            publisher = book.get("publisher")
            published_date = book.get("published_date")
            info_link = book.get("info_link")
            ratingCount = book.get("ratingCount")
            authors = book.get("authors")
            categories = book.get("categories")

            #saving the book into database and getting the last inserted id of the book
            book_id = execute_query(
                "INSERT INTO Book (searchTyper, title, description, image, previewLink, publisher, published_date, infolink, ratings_count,prompt_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (searchType,tittle,description,image,previewLink,publisher,published_date,info_link,ratingCount,id_prompt,),get_id=True
            )

            if insert_category(categories, book_id):
                logger.info(f"Book {book_id} registered successfully")

                if insert_authors(authors, book_id):
                    logger.info(f"Book {book_id} registered successfully")
                else:
                    logger.error(f"Unexpected error posting: {e}")
                    raise
            else:
                logger.error(f"Unexpected error posting: {e}")
                raise

        return True
    except Exception as e:
        logger.error(f"Error inserting books: {e}")
        return False


def insert_category(categories, book_id):
    try:
        for category in categories:

            res = execute_query(
                "SELECT id FROM Category where name = ? AND enabled = TRUE",
                (category,)
            )
            if not res:
                #saving the book into database
                category_id = execute_query(
                    "INSERT INTO Category (name) VALUES (?)",
                    (category,),get_id=True
                )
                logger.info(f"Category '{category}' for book {book_id} registered successfully")
            else:
                category_id = res[0]["id"]
                   
            execute_query(
                "INSERT INTO Category_Book (book_id,category_id) VALUES (?,?)",
                (book_id,category_id,)
            )

        return True
    except Exception as e:
        logger.error(f"Error inserting books: {e}")
        return False
    
def insert_authors(authors, book_id):
    try:
        for author in authors:

            res = execute_query(
                "SELECT id FROM Author where name = ? AND enabled = TRUE",
                (author,)
            )
            if not res:
                #saving the book into database
                author_id=execute_query(
                    "INSERT INTO Author (name) VALUES (?)",
                    (author,),get_id=True
                )
                logger.info(f"Author '{author}' for book {book_id} registered successfully")
            else:
                author_id = res[0]["id"]
                   
            execute_query(
                "INSERT INTO Author_Book (book_id,author_id) VALUES (?,?)",
                (book_id,author_id,)
            )

        return True
    except Exception as e:
        logger.error(f"Error inserting books: {e}")
        return False    

#route to generate a result by a prompt
@prompt_blueprint.route('/edit', methods=['PUT'])
def edit():
    logger.info("esto es un prompt editado")
    return "edited route"


#route to generate a result by a prompt

@prompt_blueprint.route('/myprompts', methods=['GET'])
def my_prompts(id_user=None):
    invocated = True #this variable say if the method was called here
    #get data from bady request or from the params
    if id_user is None:
        invocated = False
        if request.method == "POST":
            id_user = request.json.get("id_user")
        if not id_user:
            id_user = request.args.get("id_user")
    
    if not id_user:
        return jsonify({"error": "id_user is required"}), 400

    try:
        #get user prompts
        prompts = execute_query(
            "SELECT id, text, created_at, likes FROM Prompt WHERE id_user = ?  AND enabled = TRUE ORDER BY created_at DESC",
            (id_user,)
        )

        for prompt in prompts:
            prompt_id = prompt["id"]

            #get the books from the prompt
            books = execute_query(
                "SELECT id, searchTyper, title, description, image, previewLink, publisher, published_date, infolink, ratings_count FROM Book WHERE enabled=1 AND prompt_id = ?",
                (prompt_id,)
            )

            for book in books:
                book_id = book["id"]

                #get the authors by the id book
                authors = execute_query(
                    """SELECT a.name FROM Author AS a JOIN Author_Book AS b ON a.id = b.author_id WHERE b.book_id = ? AND a.enabled = 1 """,
                    (book_id,)
                )
                book["authors"] = [a["name"] for a in authors]

                # get the categories by the id book
                categories = execute_query(
                    """SELECT a.name FROM Category AS a JOIN Category_Book AS b ON a.id = b.category_id WHERE b.book_id = ? AND a.enabled = 1 """,
                    (book_id,)
                )
                book["categories"] = [c["name"] for c in categories]

            prompt["books"] = books


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
    try:
        # split the text into words to search each one
        words = text.split()
        query = "SELECT id FROM Prompt WHERE "
        params = []
        conditions = []
        # create a condition for each word to search in name or lastname
        for w in words:
            conditions.append("(text LIKE CONCAT('%', ?, '%'))")
            params.extend([w])

        query += " AND ".join(conditions)  #all conditions must be met
        query += " AND enabled = TRUE"
        #execute the query created
        prompts_ids = execute_query(query, tuple(params))
        result = []
        for prompt in prompts_ids:
            response = my_prompt(prompt["id"])    
            prompt_data = response.get_json()   
            result.append(prompt_data)

        return jsonify(result), 200
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

    try:
        #get user prompts
        res = execute_query(
            "SELECT id, text, created_at, likes FROM Prompt WHERE id = ?  AND enabled = TRUE ORDER BY created_at DESC",
            (id_prompt,)
        )

        if not res: 
            logger.error(f"Error id: {id_prompt} does not exist")
            return jsonify({"error": "Error the prompt does not exist"}), 500
        prompt = res[0]
        prompt_id = prompt["id"]

        #get the books from the prompt
        books = execute_query(
                "SELECT id, searchTyper, title, description, image, previewLink, publisher, published_date, infolink, ratings_count FROM Book WHERE enabled=1 AND prompt_id = ?",
                (prompt_id,)
        )

        for book in books:
            book_id = book["id"]

                #get the authors by the id book
            authors = execute_query(
                    """SELECT a.name FROM Author AS a JOIN Author_Book AS b ON a.id = b.author_id WHERE b.book_id = ? AND a.enabled = 1 """,
                    (book_id,)
            )
            book["authors"] = [a["name"] for a in authors]

                # get the categories by the id book
            categories = execute_query(
                    """SELECT a.name FROM Category AS a JOIN Category_Book AS b ON a.id = b.category_id WHERE b.book_id = ? AND a.enabled = 1 """,
                    (book_id,)
            )
            book["categories"] = [c["name"] for c in categories]

        prompt["books"] = books

        if invocated:
            return jsonify(prompt)
        
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
        #get user prompts
        friends = execute_query(
            "SELECT id_friend FROM Friend WHERE id_user = ? AND enabled = TRUE",
            (id_user,)
        )

        feed = []
        for friend in friends:
            friend_prompt = my_prompts(friend["id_friend"])
            if friend_prompt:
                feed.extend(friend_prompt)
            
        return jsonify(feed), 200

    except Exception as e:
        logger.error(f"Error fetching prompts for user {id_user}: {e}")
        return jsonify({"error": "Error fetching prompts"}), 500

