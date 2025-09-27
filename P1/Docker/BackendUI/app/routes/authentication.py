from flask import Blueprint
import logging
import sys

logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

auth_blueprint = Blueprint('auth', __name__)

#Route for login into promptsy
@auth_blueprint.route('/login' , methods=['POST'])
def login():
    logger.info("Login route accessed")
    return "Login route"


#Route for registering into promptsy
@auth_blueprint.route('/register', methods=['POST'])
def register():
    logger.info("Register route accessed")
    return "Register route"
