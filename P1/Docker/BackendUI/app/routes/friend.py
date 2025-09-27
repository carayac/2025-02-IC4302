from flask import Blueprint
import logging
import sys

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
    logger.info("follow a un amigo")
    return "follow route"

#route for unfollowing a friend
@friend_blueprint.route('/unfollow', methods=['PUT'])
def unfollow():
    logger.info("unfollow a un amigo")
    return "unfollow route"

#route for finding friends
@friend_blueprint.route('/find', methods=['GET'])
def find():
    logger.info("find a un amigo")
    return "find route"

#route for get my friends
@friend_blueprint.route('/get-friends', methods=['GET'])
def get_friends():
    logger.info("Obtener amigos")
    return "get friends route"

#route for get the feed
@friend_blueprint.route('/feed', methods=['GET'])
def feed():
    logger.info("get the feed")
    return "feed route"

