from flask import Blueprint
import logging
import sys

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
    logger.info("esto es un user")
    return "Ge me route"

#Route for updating user info
@user_blueprint.route('/edit' , methods=['PUT'])
def edit():
    logger.info("esto es un user")
    return "Edit user route"

#Route for change password
@user_blueprint.route('/change-password' , methods=['POST'])
def change_password():
    logger.info("esto es un user")
    return "Change password route"