import uvicorn
from control.agent_control import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)