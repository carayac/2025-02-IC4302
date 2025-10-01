from flask import Blueprint, request,jsonify
from tools.mariadb_connection import execute_query
import logging
import sys
import mariadb
import bcrypt

logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

friend_blueprint = Blueprint('friends', __name__)


#route for following a friend
@friend_blueprint.route('/follow', methods=['POST'])
def follow():
    logger.info("Starting to follow a friend")

    #get the data from the request
    id_user = request.json.get("id_user")
    id_friend = request.json.get("id_friend")

    #validate the data
    if not id_user or not id_friend:
        return jsonify({"error": "id_user and id_friend are required"}), 400
    
    try:
        #validate if the user is trying to follow himself
        if id_user == id_friend:    
            logger.warning(f"User {id_user} is trying to follow himself")
            return {"error": "You cannot follow yourself"}, 400
        #validate if the user to follow exists
        user_to_follow = execute_query(
            "SELECT id FROM User WHERE id = ? LIMIT 1",
            (id_friend,),
            fetch_one=True
        )
        if not user_to_follow:
            logger.warning(f"User to follow does not exist: {id_friend}")
            return {"error": "User to follow does not exist"}, 404
        #validate if the user is already following the friend
        already_following = execute_query(
            "SELECT id FROM Friend WHERE id_user = ? AND id_friend = ? AND enabled = TRUE LIMIT 1",
            (id_user, id_friend),
            fetch_one=True
        )
        if already_following:
            logger.warning(f"User {id_user} is already following {id_friend}")
            return {"error": "You are already following this user"}, 400
        
        # execute the insert query in the table friends
        res = execute_query(
            "INSERT INTO Friend (id_user, id_friend) VALUES (?, ?)",
            (id_user, id_friend)
        )

        #update the followers and following count in the user table
        execute_query(
            "UPDATE User SET following = following + 1 WHERE id = ?",
            (id_user,)
        )
        execute_query(
            "UPDATE User SET followers = followers + 1 WHERE id = ?",
            (id_friend,)
        )
        logger.info(f"User followed successfully: {id_user} -> {id_friend}")
        return {"message": "User followed successfully"}, 201

    except mariadb.IntegrityError as e:
        # the email must be unique this error is for duplicate entry
        logger.error(f"Integrity error following user : {e}")
        return {"error": "Database integrity error"}, 500

    except Exception as e:
        logger.error(f"Integrity error following user : {e}")
        return {"error": "Error registering user"}, 500

#route for unfollowing a friend
@friend_blueprint.route('/unfollow', methods=['PUT'])
def unfollow():
    logger.info("Starting to unfollow a friend")

    #get the data from the request
    id_user = request.json.get("id_user")
    id_friend = request.json.get("id_friend")

    #validate the data
    if not id_user or not id_friend:
        return jsonify({"error": "id_user and id_friend are required"}), 400
    
    try:
        #validate if the user is trying to unfollow himself
        if id_user == id_friend:    
            logger.warning(f"User {id_user} is trying to follow himself")
            return {"error": "You cannot follow yourself"}, 400
        #validate if the user to unollow exists
        user_to_follow = execute_query(
            "SELECT id FROM User WHERE id = ? LIMIT 1",
            (id_friend,),
            fetch_one=True
        )
        if not user_to_follow:
            logger.warning(f"User to follow does not exist: {id_friend}")
            return {"error": "User to follow does not exist"}, 404
        #validate if the user is already following the friend
        already_following = execute_query(
            "SELECT id FROM Friend WHERE id_user = ? AND id_friend = ? AND enabled = TRUE LIMIT 1",
            (id_user, id_friend),
            fetch_one=True
        )
        if already_following is None:
            logger.warning(f"User {id_user} is not following {id_friend}")
            return {"error": "You are not following this user"}, 400
        
        # execute the insert query in the table friends
        res = execute_query(
            """UPDATE Friend SET enabled = FALSE WHERE id_user = ? AND id_friend = ?""",
            (id_user, id_friend)
        )

         #update the followers and following count in the user table
        execute_query(
            "UPDATE User SET following = following - 1 WHERE id = ?",
            (id_user,)
        )
        execute_query(
            "UPDATE User SET followers = followers - 1 WHERE id = ?",
            (id_friend,)
        )

        logger.info(f"User unfollowed successfully: {id_user} -> {id_friend}")
        return {"message": "User unfollowed successfully"}, 201

    except mariadb.IntegrityError as e:
        # the email must be unique this error is for duplicate entry
        logger.error(f"Integrity error unfollowing user : {e}")
        return {"error": "Database integrity error"}, 500

    except Exception as e:
        logger.error(f"Integrity error unfollowing user : {e}")
        return {"error": "Error registering user"}, 500

#route for finding friends
@friend_blueprint.route('/find', methods=['GET'])
def find():
    logger.info("finding friends")
    #get the name and lastname from the request args
    text = request.args.get("text")
    if not text:
        return jsonify({"error": "text is required"}), 400
    #clean the text
    text = text.strip('"')
    try:
        # split the text into words to search each one
        words = text.split()
        query = "SELECT id, name, lastname, email FROM User WHERE "
        params = []
        conditions = []
        # create a condition for each word to search in name or lastname
        for w in words:
            conditions.append("(name LIKE CONCAT('%', ?, '%') OR lastname LIKE CONCAT('%', ?, '%'))")
            params.extend([w, w])

        query += " AND ".join(conditions)  #all conditions must be met

        #execute the query created
        users = execute_query(query, tuple(params))

        return jsonify(users), 200
    except mariadb.IntegrityError as e:
        # there was an error with the query
        logger.error(f"Integrity error finding users : {e}")
        return {"error": "Database integrity error"}, 500

    except Exception as e:
        logger.error(f"Integrity error finding users : {e}")
        return {"error": "Error registering user"}, 500

#route for get my friends
@friend_blueprint.route('/get_friends', methods=['GET'])
def get_friends():
    logger.info("Getting my friends")
    #get the user id from the request args
    id_user = request.args.get("id")
    if not id_user:
        return jsonify({"error": "id_user is required"}), 400
    
    #get the friends from the database
    try:
        friends = execute_query(
            """
            SELECT u.id, u.name, u.lastname, u.description, u.email, u.followers, u.following FROM Friend f JOIN User u ON f.id_friend = u.id WHERE f.id_user = ? AND f.enabled = TRUE
            """,
            (id_user,)
        )
        logger.info(f"Friends retrieved successfully for user {id_user}")
        return jsonify(friends), 200
    except mariadb.IntegrityError as e:
        # the user it was not found
        logger.error(f"Integrity error getting user friends : {e}")
        return {"error": "Database integrity error"}, 500

    except Exception as e:
        logger.error(f"Integrity error getting user friends: {e}")
        return {"error": "Error registering user"}, 500


#route for  like a post
@friend_blueprint.route('/like', methods=['POST'])
def like():
    logger.info("Giving a like to a post")
    #get data from the request
    id_prompt = request.json.get("id_prompt")
    id_user = request.json.get("id_user")

    #validate the data
    if not id_user or not id_prompt:
        return jsonify({"error": "id_user and id_prompt are required"}), 400
    
    try:
        #validate if the user has already liked the prompt
        already_liked = execute_query(
            "SELECT id FROM Liked WHERE id_user = ? AND id_prompt = ? AND enabled = TRUE LIMIT 1",
            (id_user, id_prompt),
        )
        if already_liked:
            logger.warning(f"User {id_user} has already liked prompt {id_prompt}")
            return {"error": "You have already liked this prompt"}, 400

        # execute the insert query in the table friends
        execute_query(
            "INSERT INTO Liked (id_user, id_prompt) VALUES (?, ?)",
            (id_user, id_prompt,)
        )
        execute_query(
            """UPDATE Prompt SET likes = likes+1 WHERE id = ?""",
            (id_prompt,)
        )
        logger.info(f"Like ready: {id_user} -> {id_prompt}")
        return {"message": "Like successfully"}, 201

    except mariadb.IntegrityError as e:
        # the email must be unique this error is for duplicate entry
        logger.error(f"Integrity error like user : {e}")
        return {"error": "Database integrity error"}, 500

    except Exception as e:
        logger.error(f"Integrity error like user : {e}")
        return {"error": "Error registering user"}, 500


#route for unlike a post
@friend_blueprint.route('/unlike', methods=['PUT'])
def unlike():
    logger.info("Giving a like to a post")
    #get data from the request
    id_prompt = request.json.get("id_prompt")
    id_user = request.json.get("id_user")

    #validate the data
    if not id_user or not id_prompt:
        return jsonify({"error": "id_user and id_prompt are required"}), 400
    
    try:
        # execute the insert query in the table friends
        execute_query(
            """UPDATE Liked SET enabled = FALSE WHERE id_user = ? AND id_prompt = ? AND enabled = TRUE""",
            (id_user, id_prompt,)
        )
        execute_query(
            """UPDATE Prompt SET likes = likes-1 WHERE id = ?""",
            (id_prompt,)
        )

        logger.info(f"Prompt unliked successfully: {id_user} -> {id_prompt}")
        return {"message": "Like successfully"}, 201

    except mariadb.IntegrityError as e:
        # the email must be unique this error is for duplicate entry
        logger.error(f"Integrity error giving like : {e}")
        return {"error": "Database integrity error"}, 500

    except Exception as e:
        logger.error(f"Integrity error giving like  : {e}")
        return {"error": "Error giving like "}, 500


