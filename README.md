# Twitter Redis

Twitter style API using only redis for database

## Setup

To start the docker containers, run the command `docker compose up --build`.

The FastApi project is configured to reload once the code is updated, so there is no need to restart the containers after every change.

The redis data is also presisted on disk, so if you restart the docker containers, your data will still be available.

## Access

After running the `docker compose up --build` command, you can access the following:

- Swagger UI: This is a user interface to directly test your FastApi endpoints from the browser. [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Redinsight: This is a user interface to directly interact with your redis database. [http://localhost:8001/](http://localhost:8001/)
- redis-cli: Send commands to the databse using this cli. Execute the following command from a terminal: `docker exec -it redis-for-twitter redis-cli`

## Project

This project is not complete, and should be completed as part of an assesment.

Currently the current endpoints are missing:

- Get user followers:
  Return all the followers of one user.
  This method takes as input the Id of the user.
  This method should also allow for pagination using [ZRANGE](https://redis.io/docs/latest/commands/zrange/) start and stop parameters, by accepting 2 extra parameters for start and stop.
- Get user following:
  Return all the users followed by one user.
  Similar to the previous method.
- Unfollow a user:
  This method is similar to the Follow a user method, but should revert the actions already taken.
- Create a post:
  Create a new post. This method takes as input, the text content of the post, and the id of user creating the post. We should save the content, user id, and timestamp of the creation of the post to redis.
  You should store the posts, and also store separately a list of the posts of every user.
- Get user posts:
  Return posts of one user.
  This method takes as input the id of a user, and returns the posts linked to the user.
  This method should also allow for pagination by accepting 2 extra parameters for start and stop.
- Authenticate a user:
  This method takes as input a user id, and a password. It should use the existing `check_password` method, to compare the received password, with the password stored in the database.

## Challenges

Extra points will be allocated for completing the following:

- There is a bug in the code, where the order of followers is not preserved.
  To try this:

  1. Create 3 users.
  2. Let user 1 follow user 2
  3. Let user 3 follow user 2
  4. Get the followers of user 2
  5. Let user 1 follow user 2. This should return false, since they already follow each other.
  6. Get the followers of user 2, the order changed from the one in step 4. It should remain the same.

  Find the issue causing this, and propose/implement an alternative.

- Find a user by username. Currently we can find users using their ids. It can be important to also add the functionality for finding users by their username.

## Submission

You can send me one of the following:

- Report: Include all the queries required for every endpoint, plus an explanation.
- Code: Send the new main.py file, with the new endpoints implemented. You can also add comments, or send a small report with some explanation if you feel it's necessary.
