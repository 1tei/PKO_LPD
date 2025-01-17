import uvicorn

from .rest_api import app

def main():
    config = uvicorn.Config("vehicle_routing:app",
                            host="0.0.0.0",
                            port=8080,
                            log_config="/logs/logging.conf",
                            reload=True,
                            use_colors=True)
    server = uvicorn.Server(config)
    server.run()

if __name__ == "__main__":
    main()
