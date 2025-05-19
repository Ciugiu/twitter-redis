# Twitter Redis API: Endpoint Query Report

Below are the Redis queries and explanations for each endpoint in the project.

---

## 1. **Create User**

**Endpoint:** `POST /user/`

**Redis Queries:**
- `INCR seq:user`  
  _Get a new user id._
- `HMSET user:{user_id} id {user_id} username {username} password {hashed_password} follower_count 0 following_count 0`  
  _Store user info._
- `SET username:{username} {user_id}`  
  _Index username for fast lookup._

**Explanation:**  
A new user id is generated, user info is stored in a hash, and the username is indexed for quick lookup by username.

---

## 2. **Get User by ID**

**Endpoint:** `GET /user/{id}`

**Redis Queries:**
- `EXISTS user:{id}`  
  _Check if user exists._
- `HMGET user:{id} username following_count follower_count`  
  _Get user info._
- `ZRANGE following:{id} 0 -1`  
  _Get all users this user is following._
- `ZRANGE followers:{id} 0 -1`  
  _Get all followers of this user._

**Explanation:**  
Fetches user info and lists of followers/following.

---

## 3. **Get User by Username**

**Endpoint:** `GET /user/by-username/{username}`

**Redis Queries:**
- `GET username:{username}`  
  _Get user id by username._
- `HMGET user:{user_id} username following_count follower_count`  
  _Get user info._
- `ZRANGE following:{user_id} 0 -1`  
  _Get following list._
- `ZRANGE followers:{user_id} 0 -1`  
  _Get followers list._

**Explanation:**  
Allows lookup of user info by username.

---

## 4. **Follow a User**

**Endpoint:** `POST /user/follow`

**Redis Queries:**
- `HGETALL user:{follower_id}`  
  _Check follower exists._
- `HGETALL user:{followed_id}`  
  _Check followed exists._
- `ZADD followers:{followed_id} NX {timestamp} {follower_id}`  
  _Add follower only if not already present._
- `ZADD following:{follower_id} NX {timestamp} {followed_id}`  
  _Add following only if not already present._
- `HINCRBY user:{follower_id} following_count 1`  
  _Increment following count._
- `HINCRBY user:{followed_id} follower_count 1`  
  _Increment follower count._

**Explanation:**  
Adds a follow relationship, increments counters, and preserves order using `NX`.

---

## 5. **Unfollow a User**

**Endpoint:** `POST /user/unfollow`

**Redis Queries:**
- `HGETALL user:{follower_id}`  
  _Check follower exists._
- `HGETALL user:{followed_id}`  
  _Check followed exists._
- `ZREM followers:{followed_id} {follower_id}`  
  _Remove follower._
- `ZREM following:{follower_id} {followed_id}`  
  _Remove following._
- `HINCRBY user:{follower_id} following_count -1`  
  _Decrement following count._
- `HINCRBY user:{followed_id} follower_count -1`  
  _Decrement follower count._

**Explanation:**  
Removes the follow relationship and decrements counters.

---

## 6. **Get User Followers (with Pagination)**

**Endpoint:** `GET /user/{id}/followers?start={start}&stop={stop}`

**Redis Queries:**
- `EXISTS user:{id}`  
  _Check user exists._
- `ZRANGE followers:{id} {start} {stop}`  
  _Get followers in range._

**Explanation:**  
Returns a paginated list of followers.

---

## 7. **Get User Following (with Pagination)**

**Endpoint:** `GET /user/{id}/following?start={start}&stop={stop}`

**Redis Queries:**
- `EXISTS user:{id}`  
  _Check user exists._
- `ZRANGE following:{id} {start} {stop}`  
  _Get following in range._

**Explanation:**  
Returns a paginated list of users this user is following.

---

## 8. **Create a Post**

**Endpoint:** `POST /post/`

**Redis Queries:**
- `EXISTS user:{user_id}`  
  _Check user exists._
- `INCR seq:post`  
  _Get a new post id._
- `HMSET post:{post_id} id {post_id} user_id {user_id} content {content} timestamp {timestamp}`  
  _Store post data._
- `LPUSH posts {post_id}`  
  _Add post to global post list (optional)._
- `LPUSH user:{user_id}:posts {post_id}`  
  _Add post to user's post list._

**Explanation:**  
Creates a post and links it to the user and global post list.

---

## 9. **Get User Posts (with Pagination)**

**Endpoint:** `GET /user/{id}/posts?start={start}&stop={stop}`

**Redis Queries:**
- `EXISTS user:{id}`  
  _Check user exists._
- `LRANGE user:{id}:posts {start} {stop}`  
  _Get post ids for user in range._
- For each post id:  
  `HGETALL post:{post_id}`  
  _Get post data._

**Explanation:**  
Returns a paginated list of posts for a user.

---

## 10. **Authenticate a User**

**Endpoint:** `POST /user/authenticate`

**Redis Queries:**
- `HGETALL user:{user_id}`  
  _Get user info._
- Compare provided password with stored hash using `bcrypt`.

**Explanation:**  
Checks if the provided password matches the stored hash for the user.

---

## 11. **Bug: Order of Followers Not Preserved**

**Problem:**  
Using `ZADD` with a new timestamp for an existing member updates the score and changes the order.

**Solution:**  
Use `ZADD ... NX` to only add if not already present, so the original order is preserved.

---

## 12. **Index Username for Fast Lookup**

**Query:**  
- `SET username:{username} {user_id}`  
  _On user creation, index username to user id._

**Explanation:**  
Allows fast lookup of user id by username.
