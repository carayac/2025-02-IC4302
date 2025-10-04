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

user_blueprint = Blueprint('user', __name__)

#Route for getting user info
@user_blueprint.route('/me',methods=['GET'])
def login():
    logger.info("getting user information")
    id = request.args.get("id")

    if not id:
        return jsonify({"error": "ID is required"}), 400
    
    try:
        res = execute_query(
            "SELECT id, name, lastname, description, email, followers, following FROM User WHERE id = ? LIMIT 1",
            (id,)
        )

        user = res[0] if res else None
        if not user:
            logger.warning(f"Search failed: user not found {id}")
            return jsonify({"error": "Invalid id"}), 401

        logger.info(f"User found {id} successfully")
        return jsonify({
            "id": user["id"],
            "name": user["name"],
            "lastname": user["lastname"],
            "description": user["description"],
            "email": user["email"],
            "followers": user["followers"],
            "following": user["following"]
        }), 200

    except mariadb.Error as e:
        logger.error(f"Database error during search: {e}")
        return jsonify({"error": "Database error"}), 500

    except Exception as e:
        logger.error(f"Unexpected error during search: {e}")
        return jsonify({"error": "Internal server error"}), 500
    

#Route for updating user info
@user_blueprint.route('/edit' , methods=['PUT'])
def edit():
    logger.info("Editing user information")

    #get data from request
    id = request.json.get('id')
    name = request.json.get('name')
    lastname = request.json.get('lastname')
    description = request.json.get('description')

    if not id or not name or not lastname or not description:
        return jsonify({"error": "All fields are required"}), 400
    
    try:
        res = execute_query(
            """
            UPDATE User
            SET name = ?, lastname = ?, description = ?
            WHERE id = ?
            """,
            (name, lastname, description, id)
        )

        logger.info(f"User {id} edited successfully")
        return {"message": "User edited successfully"}, 201

    except mariadb.IntegrityError as e:
        # the user cannot be edited
        logger.error(f"Integrity error editing user {id}: {e}")
        return {"error": "Database editing error"}, 500

    except Exception as e:
        logger.error(f"Unexpected error editing user {id}: {e}")
        return {"error": "Error editing user"}, 500
    


#Route for change password
@user_blueprint.route('/change-password' , methods=['POST'])
def change_password():
    logger.info("Changing user password")

    #get data from request
    id = request.json.get('id')
    new_password = request.json.get('newpass')
    old_password = request.json.get('oldpass')

    if not id or not old_password or not new_password:
        return jsonify({"error": "All fields are required"}), 400
    
    try:
        #hash the new password with bcrypt
        hashednewpass = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()) 
        #get the old password to compare with the one in the database
        res = execute_query(
            """
            SELECT password FROM User WHERE id = ? LIMIT 1
            """,
            (id,)
        )
        old_passwordDB = res[0] if res else None
        if not old_passwordDB:
            logger.warning(f"User not found {id}")
            return jsonify({"error": "Invalid id"}), 401

        # CHECK IF THE OLD PASSWORD IS CORRECT
        if not bcrypt.checkpw(old_password.encode("utf-8"), old_passwordDB["password"].encode("utf-8")):
            logger.warning(f"Change failed: wrong password for {id}")
            return jsonify({"error": "Invalid old password"}), 401

        res = execute_query(
            """
            UPDATE User
            SET password = ?
            WHERE id = ?
            """,
            (hashednewpass ,id)
        )

        logger.info(f"User {id} with pass changed successfully")
        return {"message": "Password edited successfully"}, 201

    except mariadb.IntegrityError as e:
        # the user cannot be edited
        logger.error(f"Integrity error editing pass {id}: {e}")
        return {"error": "Database editing error"}, 500

    except Exception as e:
        logger.error(f"Unexpected error editing pass {id}: {e}")
        return {"error": "Error editing pass"}, 500

