import jwt
import time
import requests
import subprocess

APP_ID = "4556123"  # your App ID
PRIVATE_KEY_PATH = "navtej-cloud-agent-dev.2026-08-11.private-key.pem"  # adjust to your actual filename


## create a jwt token 
def create_jwt():
    with open(PRIVATE_KEY_PATH, "r") as key_file:
        private_key = key_file.read()

    now = int(time.time())

    payload = {
        "iat": now - 60,        # issued at, backdated 60s to allow for clock drift
        "exp": now + (10 * 60), # expires in 10 minutes (GitHub's max allowed)
        "iss": APP_ID           # who is issuing this JWT — your app
    }

    encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")
    return encoded_jwt




##create a installtion token 


def get_installation_token():

    jwt_token=create_jwt()
    INSTALLATION_ID=153342078

    url = f"https://api.github.com/app/installations/{INSTALLATION_ID}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json"
    }

    response=requests.post(url,headers=headers)


    if response.status_code==201:
        data=response.json()
        return data["token"],data["expires_at"]
    else:
        raise Exception(f"Failed to get installation token")



def clone_repo(token,repo_full_name,destination):

    url = f"https://x-access-token:{token}@github.com/{repo_full_name}.git"

    result=subprocess.run(["git","clone",url,destination],capture_output=True,text=True)


    if (result.returncode==0):
        return f"Sucessfully Cloned and {result.stderr}"
    else:
        return f"Clone failed:{result}"


if __name__=="__main__":
    token,expires_at=get_installation_token()

    result=clone_repo(token,"navtej21/QuickNotesAI","myquicknotes")
    print(result)
