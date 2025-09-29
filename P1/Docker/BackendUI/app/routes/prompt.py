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

#auxiliar methods for posting a prompt
def insert_prompt(text, id_user):
    return execute_query(
        "INSERT INTO Prompt (text, id_user) VALUES (?, ?)",
        (text, id_user),
        get_id=True
    )


def insert_result(searchTyper, prompt_id):
    return execute_query(
        "INSERT INTO Result (searchTyper, id_prompt) VALUES (?, ?)",
        (searchTyper, prompt_id),
        get_id=True
    )


def insert_book(book_data, result_id=None):
    book_id = execute_query(
        """INSERT INTO Book (id_result, title, description, image, previewLink,
                             publisher, published_date, infolink, ratings_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            result_id,
            book_data.get("title"),
            book_data.get("description"),
            book_data.get("image"),
            book_data.get("previewLink"),
            book_data.get("publisher"),
            book_data.get("published_date"),
            book_data.get("infolink"),
            book_data.get("ratings_count"),
        ),
        get_id=True
    )

    insert_authors(book_data.get("authors", []), book_id)

    insert_category(book_data.get("categories", []),book_id)

    return book_id


def insert_review(review_data, result_id):
    # si hay libro dentro del review
    book_data = review_data.get("book")
    book_id = None
    if book_data:
        book_id = insert_book(book_data,result_id)
    logger.info(f"Prompt {book_data} registered successfully")
    return execute_query(
        """INSERT INTO Review (id_result, id_book,title, price, profileName, helpfulness,
                               score, time, summary, text)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,?)""",
        (
            result_id,
            book_id,
            review_data.get("title"),
            review_data.get("price"),
            review_data.get("profileName"),
            review_data.get("helpfulness"),
            review_data.get("score"),
            review_data.get("time"),
            review_data.get("summary"),
            review_data.get("text"),
        )
    )



#route fot posting a prompt
@prompt_blueprint.route('/post', methods=['POST'])
def post():
    data = request.json.get("prompt")
    if not data:
        return jsonify({"error": "prompt is required"}), 400

    text = data.get("text")
    id_user = data.get("id_user")
    results = data.get("results", [])

    if not text or not id_user:
        return jsonify({"error": "id_user and text are required"}), 400

    try:
        #saving the prompt
        prompt_id = insert_prompt(text, id_user)

       #saving the results
        for r in results:
            result_id = insert_result(r.get("searchTyper"), prompt_id)

            #books 
            for b in r.get("books", []):
                insert_book(b, result_id)

            #getting tha reviews
            for rev in r.get("reviews", []):
                insert_review(rev, result_id)

        logger.info(f"Prompt {prompt_id} registered successfully")
        return {"message": "Prompt registered successfully"}, 201

    except mariadb.IntegrityError as e:
        logger.error(f"Integrity error posting prompt: {e}")
        return {"error": "Database integrity error"}, 500

    except Exception as e:
        logger.error(f"Error posting prompt: {e}")
        return {"error": "Error posting prompt"}, 500
    



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
    invocated = True
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
            "SELECT id, text, created_at, likes FROM Prompt WHERE id_user = ? AND enabled = TRUE ORDER BY created_at DESC",
            (id_user,)
        )

        for prompt in prompts:
            prompt_id = prompt["id"]

            #get the results associated 
            results = execute_query(
                "SELECT id, searchTyper, created_at FROM Result WHERE id_prompt = ?",
                (prompt_id,)
            )

            for result in results:
                result_id = result["id"]

                # get the books
                books = execute_query(
                    """SELECT id, title, description, image, previewLink, publisher,
                              published_date, infolink, ratings_count
                       FROM Book
                       WHERE enabled = 1 AND id_result = ?""",
                    (result_id,)
                )

                # para cada libro, agregar autores, categorías y reviews (solo si aplica)
                for book in books:
                    book_id = book["id"]

                    #authors
                    authors = execute_query(
                        """SELECT a.name
                           FROM Author AS a
                           JOIN Author_Book ab ON a.id = ab.author_id
                           WHERE ab.book_id = ? AND a.enabled = 1""",
                        (book_id,)
                    )
                    book["authors"] = [a["name"] for a in authors]

                    #categories
                    categories = execute_query(
                        """SELECT c.name
                           FROM Category AS c
                           JOIN Category_Book cb ON c.id = cb.category_id
                           WHERE cb.book_id = ? AND c.enabled = 1""",
                        (book_id,)
                    )
                    book["categories"] = [c["name"] for c in categories]

                    # reviews solo si el result es de tipo review
                    if result["searchTyper"] in ("vector_reviews", "text_reviews"):
                        reviews = execute_query(
                            """SELECT id, title, price, profileName, helpfulness, score,
                                      time, summary, text
                               FROM Review
                               WHERE enabled = 1 AND id_book = ? AND id_result = ?""",
                            (book_id, result_id)
                        )
                        book["reviews"] = reviews
                    else:
                        book["reviews"] = []

                result["books"] = books

            prompt["results"] = results

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

        # obtener results asociados al prompt
        results = execute_query(
            "SELECT id, searchTyper, created_at FROM Result WHERE id_prompt = ?",
            (prompt_id,)
        )

        for result in results:
            result_id = result["id"]

            # obtener libros asociados al result
            books = execute_query(
                  """SELECT id, title, description, image, previewLink, publisher,
                             published_date, infolink, ratings_count
                    FROM Book
                    WHERE enabled = 1 AND id_result = ?""",
                (result_id,)
            )

            # para cada libro, agregar autores, categorías y reviews (solo si aplica)
            for book in books:
                book_id = book["id"]

                # autores
                authors = execute_query(
                    """SELECT a.name
                        FROM Author AS a
                        JOIN Author_Book ab ON a.id = ab.author_id
                         WHERE ab.book_id = ? AND a.enabled = 1""",
                    (book_id,)
                )
                book["authors"] = [a["name"] for a in authors]

                # categorías
                categories = execute_query(
                    """SELECT c.name
                        FROM Category AS c
                        JOIN Category_Book cb ON c.id = cb.category_id
                        WHERE cb.book_id = ? AND c.enabled = 1""",
                    (book_id,)
                )
                book["categories"] = [c["name"] for c in categories]

                # reviews solo si el result es de tipo review
                if result["searchTyper"] in ("vector_reviews", "text_reviews"):
                    reviews = execute_query(
                        """SELECT id, title, price, profileName, helpfulness, score,
                                    time, summary, text
                            FROM Review
                            WHERE enabled = 1 AND id_book = ? AND id_result = ?""",
                        (book_id, result_id)
                    )
                    book["reviews"] = reviews
                else:
                    book["reviews"] = []

            result["books"] = books

            prompt["results"] = results

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

