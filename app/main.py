from redis import Redis
from typing import Union

from fastapi import FastAPI, Response, status
from pydantic import BaseModel
import bcrypt
import time


redis = Redis(host="redis", port=6379, decode_responses=True)


class NewUser(BaseModel):
    username: str
    password: Union[str, None] = None


class User(BaseModel):
    id: int
    username: str
    follower_count: int
    following_count: int
    following: list[int]
    followers: list[int]

class NewPost(BaseModel):
    user_id: int
    content: str

class Post(BaseModel):
    id: int
    user_id: int
    content: str
    timestamp: int


tags_metadata = [
    {
        "name": "Users",
        "description": "Operations with users.",
    },
]

app = FastAPI(openapi_tags=tags_metadata)

# API Endpoints


## Users
### Create User
@app.post("/user/", tags=["Users"])
async def create_user(user: NewUser):
    user_id = redis.incr("seq:user")
    hashed_password = get_hashed_password(user.password.encode())
    user_info = {
        "id": user_id,
        "username": user.username,
        "password": hashed_password,
        "follower_count": 0,
        "following_count": 0,
    }
    redis.hmset(f"user:{user_id}", user_info)
    return {"success": True, user_id: user_id}


@app.post("/user/follow", tags=["Users"])
async def follow_user(follower_id: int, followed_id: int):
    timestamp = int(time.time())
    if not redis.hgetall(f"user:{follower_id}"):
        return {"success": False, "message": "Follower user does not exist"}
    if not redis.hgetall(f"user:{followed_id}"):
        return {"success": False, "message": "Followed user does not exist"}
    if redis.zadd(f"followers:{followed_id}", {follower_id: timestamp}) == 0:
        return {"success": False, "message": "User is already followed"}
    redis.zadd(f"following:{follower_id}", {followed_id: timestamp})
    redis.hincrby(f"user:{follower_id}", "following_count", 1)
    redis.hincrby(f"user:{followed_id}", "follower_count", 1)
    return {"success": True}


### Get User
@app.get("/user/{id}", tags=["Users"])
async def get_user(id: int, response: Response) -> User:
    # Get User from DB
    if redis.exists(f"user:{id}") == 0:
        response.status_code = status.HTTP_404_NOT_FOUND
        return

    user_info = redis.hmget(
        f"user:{id}", ["username", "following_count", "follower_count"]
    )
    return User(
        id=id,
        username=user_info[0],
        following_count=int(user_info[1]),
        follower_count=int(user_info[2]),
        following=redis.zrange(f"following:{id}", 0, -1),
        followers=redis.zrange(f"followers:{id}", 0, -1),
    )


def get_hashed_password(plain_text_password):
    # Hash a password for the first time
    #   (Using bcrypt, the salt is saved into the hash itself)
    return bcrypt.hashpw(plain_text_password, bcrypt.gensalt())


def check_password(plain_text_password, hashed_password):
    # Check hashed password. Using bcrypt, the salt is saved into the hash itself
    return bcrypt.checkpw(plain_text_password, hashed_password)


### Get User Followers
@app.get("/user/{id}/followers", tags=["Users"])
async def get_user_followers(id: int, start: int = 0, stop: int = -1, response: Response = None):
    """
    Return all the followers of a user, with optional pagination.
    - id: user id
    - start: start index for pagination (default 0)
    - stop: stop index for pagination (default -1, meaning all)
    """
    if redis.exists(f"user:{id}") == 0:
        if response:
            response.status_code = status.HTTP_404_NOT_FOUND
        return {"success": False, "message": "User does not exist"}

    followers = redis.zrange(f"followers:{id}", start, stop)
    return {"user_id": id, "followers": followers, "count": len(followers)}


### Get User Following
@app.get("/user/{id}/following", tags=["Users"])
async def get_user_following(id: int, start: int = 0, stop: int = -1, response: Response = None):
    """
    Return all the users followed by a user, with optional pagination.
    - id: user id
    - start: start index for pagination (default 0)
    - stop: stop index for pagination (default -1, meaning all)
    """
    if redis.exists(f"user:{id}") == 0:
        if response:
            response.status_code = status.HTTP_404_NOT_FOUND
        return {"success": False, "message": "User does not exist"}

    following = redis.zrange(f"following:{id}", start, stop)
    return {"user_id": id, "following": following, "count": len(following)}


### Unfollow a user
@app.post("/user/unfollow", tags=["Users"])
async def unfollow_user(follower_id: int, followed_id: int):
    """
    Unfollow a user. Reverts the actions of following:
    - Removes follower_id from followed_id's followers
    - Removes followed_id from follower_id's following
    - Decrements follower and following counts
    """
    if not redis.hgetall(f"user:{follower_id}"):
        return {"success": False, "message": "Follower user does not exist"}
    if not redis.hgetall(f"user:{followed_id}"):
        return {"success": False, "message": "Followed user does not exist"}
    # Remove follower from followed's followers set
    removed_from_followers = redis.zrem(f"followers:{followed_id}", follower_id)
    # Remove followed from follower's following set
    removed_from_following = redis.zrem(f"following:{follower_id}", followed_id)
    if removed_from_followers == 0 or removed_from_following == 0:
        return {"success": False, "message": "User is not currently followed"}
    redis.hincrby(f"user:{follower_id}", "following_count", -1)
    redis.hincrby(f"user:{followed_id}", "follower_count", -1)
    return {"success": True}


# Create a post
@app.post("/post/", tags=["Users"])
async def create_post(post: NewPost):
    """
    Create a new post.
    - Stores post content, user id, and timestamp in Redis.
    - Adds post id to a global list and to the user's post list.
    """
    if redis.exists(f"user:{post.user_id}") == 0:
        return {"success": False, "message": "User does not exist"}

    post_id = redis.incr("seq:post")
    timestamp = int(time.time())
    post_data = {
        "id": post_id,
        "user_id": post.user_id,
        "content": post.content,
        "timestamp": timestamp,
    }
    # Store the post data
    redis.hmset(f"post:{post_id}", post_data)
    # Add post id to global posts list (optional)
    redis.lpush("posts", post_id)
    # Add post id to user's posts list
    redis.lpush(f"user:{post.user_id}:posts", post_id)
    return {"success": True, "post_id": post_id}
