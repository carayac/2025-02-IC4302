from flask import Blueprint
import logging
import sys

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
    logger.info("esto es un prompt posteado")
    return "posr route"

#route to generate a result by a prompt
@prompt_blueprint.route('/edit', methods=['PUT'])
def edit():
    logger.info("esto es un prompt editado")
    return "edited route"

#route to generate a result by a prompt
@prompt_blueprint.route('/myprompts', methods=['GET'])
def my_prompts():
    logger.info("estos son mis prompts")
    return "get prompts route"

#route to search prompts
@prompt_blueprint.route('/search', methods=['GET'])
def search():
    logger.info("esto es un prompt encontrado")
    return "searech route"

#route to generate a result by a prompt
@prompt_blueprint.route('/delete', methods=['PUT'])
def delete():
    logger.info("esto es un prompt eliminad")
    return "delete route"

#route to generate a result by a prompt
@prompt_blueprint.route('/myprompt', methods=['GET'])
def my_prompt():
    logger.info("estos es mi prompt")
    return "get prompts route"
