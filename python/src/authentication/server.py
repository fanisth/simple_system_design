import jwt, datetime, os
from flask import Flask, request
from flask_mysqldb import MySQL

server = Flask(__name__)
mysql = MySQL(server)

#config
server.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST")
server.config["MYSQL_USER"] = os.environ.get("MYSQL_USER")
server.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD")
server.config["MYSQL_DB"] = os.environ.get("MYSQL_DB")
server.config["MYSQL_PORT"] = os.environ.get("MYSQL_PORT")


@server.route("/login", methods=["POST"])
def login():
    #basic authentication header
    auth = request.authorization
    #the header does not exist with in the request
    if not auth:
        return "missing credentials", 401
    
    #check db for username and pwd
    cur = mysql.connection.cursor()
    res = cur.execute(
        "SELECT email, password FROM user WHERE email=%s", (auth.username,)
    )

    if res > 0:
        user_row = cur.fetchone()
        email = user_row[0]
        password = user_row[1]

        if auth.password != password:
            return "invalid credentials", 401
        else:
            return createJWT(auth.username, os.environ.get("JWT_SECRET"), True)
    else:
        return "invalid credentials", 401
    
#this route will be used by our Gateway to validate jwts
@server.route("/validate", methods=["POST"])
def validate():
    encoded_jwt = request.headers["Authorization"]

    if not encoded_jwt:
        return "missing credentials", 401
    
    #should validate the type of the authorization Bearer/Basic...
    encoded_method = encoded_jwt.split(" ")[0]
    if encoded_method != "Bearer":
        return "missing credentials", 401
    
    encoded_jwt = encoded_jwt.split(" ")[1]

    try:
        decoded = jwt.decode(encoded_jwt, os.environ.get("JWT_SECRET"), algorithms=["HS256"])
    except:
        return "not authorized", 403
    
    return decoded, 200


#authz defines whether the user is admin or not, if True will have access to all endpoints 
def createJWT(username, secret, authz):
    return jwt.encode(
        #claims/payload
        {
            "username": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
            "iat": datetime.datetime.utcnow(),
            "admin": authz,
        },
        secret,
        algorithm="HS256",
    )


#configring host=0.0.0.0 tells your operating system to listen to all public ips(docker container's ip address=>subject to change, that's why 0.0.0.0)
#if we connect our Docker conainer to 2 seperate Docker networks Docker will assign a different IP address to our container for each Docker network
#with 0.0.0.0 flask app will listen to requests coming to both addresses
#otherwise default localhost
if __name__ == "__main__":
    server.run(host="0.0.0.0", port=5000)