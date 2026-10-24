import uvicorn

from solomon.main import create_app
from solomon.portal import portal_from_environment

if __name__ == "__main__":
    uvicorn.run(create_app(provider=portal_from_environment()), host="127.0.0.1", port=8000)
