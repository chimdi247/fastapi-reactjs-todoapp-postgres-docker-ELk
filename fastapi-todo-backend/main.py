import uvicorn

def main():
    print("Hello from todo-backend!")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8085, reload=True)



if __name__ == "__main__":
    main()
